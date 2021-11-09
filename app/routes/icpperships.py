from fastapi import Request, APIRouter, BackgroundTasks

from pydantic import BaseModel
from redis.exceptions import LockNotOwnedError, LockError
from collections import defaultdict
from mongoengine import Q

from app.common.models.icpdao.dao import DAO
from app.common.models.icpdao.job import Job, JobStatusEnum
from app.common.models.icpdao.token import MentorTokenIncomeStat
from app.common.models.logic.user_helper import pre_icpper_to_icpper, icppership_accept, icppership_cancle_accept
from app.common.utils.errors import ICPPER_NOT_FOUND_ERROR, COMMON_NOT_PERMISSION_ERROR, ICPPER_LOOP_BACK_ERROR, \
    COMMON_TIMEOUT_ERROR, ICPPER_PRE_MENTOR_MAX_ERROR, ICPPER_ALREADY_MENTOR_ERROR
from app.common.utils.route_helper import get_current_user
from app.common.models.icpdao.user import User, UserStatus
from app.common.models.icpdao.icppership import Icppership, IcppershipStatus, IcppershipProgress, MentorRelationStat, \
    MentorLevel7IcpperCountStat
from app.helpers.discord import set_discord_role
from settings import ICPDAO_REDIS_LOCK_DB_CONN, ICPDAO_MINT_TOKEN_ETH_CHAIN_ID, ICPDAO_DISCORD_GUILD, ICPDAO_DISCORD_NORMAL_ROLEID, \
    ICPDAO_DISCORD_ICPPER_ROLEID

router = APIRouter()

PRE_MENTOR_ICPPERSHIP_COUNT_LIMIT = 10

LINK_MENTOR_AND_ICPPER_LOCK_KEY = "lock:LINK_MENTOR_AND_ICPPER_LOCK_KEY"


class CreateItem(BaseModel):
    icpper_github_login: str


def to_icppership_dict(icppership, icpper=None, icpper_icpper_count=0) -> dict:
    if icpper:
        nickname = icpper.nickname
        github_login = icpper.github_login
    else:
        nickname = ""
        github_login = icppership.icpper_github_login
    mentor = User.objects(id=str(icppership.mentor_user_id)).first()

    return {
        "id":                  str(icppership.id),
        "progress":            icppership.progress,
        "status":              icppership.status, 
        "mentor_github_login": mentor.github_login,
        "icpper": {
            "id":              str(icpper.id) if icpper else "",
            "nickname":        nickname,
            "github_login":    github_login,
        },
        "icpper_icpper_count": icpper_icpper_count,
        "create_at":           icppership.create_at,
        "accept_at":           icppership.accept_at, 
        "icpper_at":           icppership.icpper_at, 
    }


@router.put('/icpperships/{icppership_id}/accept')
async def accept(icppership_id, request: Request, background_tasks: BackgroundTasks):
    user = get_current_user(request)

    icppership = Icppership.objects(id=icppership_id).first()
    if not icppership:
        return {
            "success": False,
            "errorCode": "404",
            "errorMessage": ICPPER_NOT_FOUND_ERROR
        }

    if icppership.icpper_github_login != user.github_login:
        return {
            "success": False,
            "errorCode": "403",
            "errorMessage": COMMON_NOT_PERMISSION_ERROR
        }

    if icppership.progress != IcppershipProgress.PENDING.value:
        return {
            "success": True,
            "data": to_icppership_dict(icppership, user)
        }

    mentor = User.objects(id=icppership.mentor_user_id).first()
    try:
        with ICPDAO_REDIS_LOCK_DB_CONN.lock(LINK_MENTOR_AND_ICPPER_LOCK_KEY, timeout=5, blocking_timeout=5) as lock:
            # 锁内操作
            mentor_list = find_mentor_list_of_user(str(mentor.id))
            mentor_id_list = [str(user.id) for user in mentor_list]
            if str(user.id) in mentor_id_list:
                return {
                    "success": False,
                    "errorCode": "403",
                    "errorMessage": ICPPER_LOOP_BACK_ERROR
                }

            icppership_accept(icppership, user)
    except LockNotOwnedError:
        # 使用锁超时了
        icppership_cancle_accept(icppership)
        return {
            "success": False,
            "errorCode": "403",
            "errorMessage": COMMON_TIMEOUT_ERROR
        }
    except LockError:
        # 没有获取到锁
        return {
            "success": False,
            "errorCode": "403",
            "errorMessage": COMMON_TIMEOUT_ERROR
        }

    pre_icpper_to_icpper(icppership.mentor_user_id)
    update_icpper_count_stat_for_create_icppership(icppership.mentor_user_id, icppership.icpper_user_id)

    job = Job.objects(status__ne=JobStatusEnum.AWAITING_MERGER.value, user_id=icppership.icpper_user_id).first()
    dao = DAO.objects(owner_id=icppership.icpper_user_id).first()
    if dao or job:
        pre_icpper_to_icpper(icppership.icpper_user_id)
    if user.discord_user_id:
        background_tasks.add_task(
            set_discord_role,
            ICPDAO_DISCORD_GUILD,
            user.discord_user_id, 
            ICPDAO_DISCORD_ICPPER_ROLEID)
    return {
        "success": True,
        "data": to_icppership_dict(icppership, user)
    }


@router.post('/icpperships')
async def create(request: Request, item: CreateItem):
    user = get_current_user(request)

    if user.status == UserStatus.NORMAL.value:
        return {
            "success": False,
            "errorCode": "403",
            "errorMessage": COMMON_NOT_PERMISSION_ERROR
        }

    if PRE_MENTOR_ICPPERSHIP_COUNT_LIMIT != -1:
        query1 = Q(mentor_user_id=str(user.id), progress=IcppershipProgress.PENDING.value)
        query2 = Q(mentor_user_id=str(user.id), progress=IcppershipProgress.ACCEPT.value, status=IcppershipStatus.PRE_ICPPER.value)
        if Icppership.objects(query1 | query2).count() >= PRE_MENTOR_ICPPERSHIP_COUNT_LIMIT:
            return {
                "success": False,
                "errorCode": "403",
                "errorMessage": ICPPER_PRE_MENTOR_MAX_ERROR
            }

    icpper_github_login = item.icpper_github_login
    if Icppership.objects(icpper_github_login=icpper_github_login).count() > 0:
        return {
            "success": False,
            "errorCode": "403",
            "errorMessage": ICPPER_ALREADY_MENTOR_ERROR
        }

    # 找 user 的七个上级
    # XXX 这里不用锁，是考虑到后续只有用户同意才能最终建立关系，这里只需要拒绝大部分情况即可，不用太严格
    mentor_list = find_mentor_list_of_user(str(user.id))
    mentor_github_login_list = [user.github_login for user in mentor_list]
    if icpper_github_login in mentor_github_login_list:
        return {
            "success": False,
            "errorCode": "403",
            "errorMessage": ICPPER_LOOP_BACK_ERROR
        }

    icpper = User.objects(github_login=icpper_github_login).first()
    status = icpper.status if icpper else IcppershipStatus.NORMAL.value
    icppership = Icppership(
        mentor_user_id=str(user.id),
        icpper_github_login=icpper_github_login,
        status=status
    )
    icppership.save()

    return {
        "success": True,
        "data": to_icppership_dict(icppership, icpper)
    }


@router.delete('/icpperships/{icppership_id}')
async def delete(icppership_id, request: Request):
    user = get_current_user(request)

    icppership = Icppership.objects(id=icppership_id).first()
    if not icppership:
        return {
            "success": False,
            "errorCode": "404",
            "errorMessage": ICPPER_NOT_FOUND_ERROR
        }

    if icppership.mentor_user_id != str(user.id):
        return {
            "success": False,
            "errorCode": "403",
            "errorMessage": COMMON_NOT_PERMISSION_ERROR
        }

    Icppership.objects(id=icppership_id).delete()

    if icppership.progress == IcppershipProgress.ACCEPT.value:
        pre_icpper = User.objects(id=icppership.icpper_user_id).first()
        if pre_icpper and pre_icpper.status == UserStatus.PRE_ICPPER.value:
            pre_icpper.status = UserStatus.NORMAL.value
            pre_icpper.save()

        update_icpper_count_stat_for_delete_icppership(icppership.mentor_user_id, icppership.icpper_user_id)

    return {
        "success": True,
        "data": {}
    }


@router.get('/icpperships')
async def get_list(request: Request, token_chain_id: str = ICPDAO_MINT_TOKEN_ETH_CHAIN_ID):
    user = get_current_user(request)

    is_list = Icppership.objects(mentor_user_id=str(user.id)).all()

    icpper_user_id_list = []
    for item in is_list:
        if item.icpper_user_id:
            icpper_user_id_list.append(item.icpper_user_id)
    user_id_2_icpper = {}
    for icpper in User.objects(id__in=icpper_user_id_list):
        user_id_2_icpper[str(icpper.id)] = icpper

    user_id_2__icpper_count = {}
    data_query = Icppership.objects(
        progress=IcppershipProgress.ACCEPT.value,
        status=IcppershipStatus.ICPPER.value,
        mentor_user_id__in=icpper_user_id_list
    )
    for is_item in data_query:
        user_id = is_item.mentor_user_id
        user_id_2__icpper_count.setdefault(user_id, 0)
        user_id_2__icpper_count[user_id] += 1

    relations = MentorRelationStat.objects(
        mentor_id=str(user.id), icpper_id__in=icpper_user_id_list
    )

    mentor_relation_stat = dict()

    for rel in relations:
        mentor_relation_stat[rel.icpper_id] = dict(
            relation=rel.relation,
            has_reward_icpper_count=rel.has_reward_icpper_count,
            token_count=0
        )
        token_count_record = rel.token_stat.filter(token_chain_id=token_chain_id).first()
        if token_count_record:
            mentor_relation_stat[rel.icpper_id]['token_count'] = token_count_record.token_count

    token_income_stat = MentorTokenIncomeStat.objects(
        mentor_id=str(user.id), icpper_id__in=icpper_user_id_list, token_chain_id=token_chain_id
    )

    mentor_token_stat = defaultdict(list)

    for tis in token_income_stat:
        dao = DAO.objects(id=tis.dao_id).first()
        if not dao:
            continue
        mentor_token_stat[tis.icpper_id].append(dict(
            dao_id=tis.dao_id,
            dao_name=dao.name,
            token_contract_address=tis.token_contract_address,
            token_name=tis.token_name,
            token_symbol=tis.token_symbol,
            total_value=tis.total_value,
        ))

    icpper_info_list = [to_icppership_dict(item, user_id_2_icpper.get(item.icpper_user_id, None), user_id_2__icpper_count.get(item.icpper_user_id, 0)) for item in is_list]

    res = [{**r, **mentor_relation_stat.get(r['icpper']['id'], {}), 'token_stat': mentor_token_stat.get(r['icpper']['id'], [])} for r in icpper_info_list]

    return {
        "success": True,
        "data": {
            "icpperships": res,
            "pre_mentor_icppership_count_limit": PRE_MENTOR_ICPPERSHIP_COUNT_LIMIT
        }
    }


def find_mentor_list_of_user(user_id):
    # 找 user 的七个上级
    mentor_user_id_list = []
    current_user_id = user_id
    for i in range(7):
        icppership = Icppership.objects(
            icpper_user_id=current_user_id,
            progress=IcppershipProgress.ACCEPT.value
        ).first()
        if not icppership:
            break
        mentor_user_id_list.append(icppership.mentor_user_id)
        current_user_id = icppership.mentor_user_id
    if len(mentor_user_id_list) > 0:
        result = []
        id_2_user = {}
        for user in User.objects(id__in=mentor_user_id_list):
            id_2_user[str(user.id)] = user
        for user_id in mentor_user_id_list:
            result.append(id_2_user[user_id])
        return result
    else:
        return []


def update_icpper_count_stat_for_create_icppership(mentor_user_id, icpper_user_id):
    ####
    # 更新人数

    # 获取 icpper_user_id 下七层的人数 cache
    cache_stat = MentorLevel7IcpperCountStat.objects(mentor_id=icpper_user_id).first()
    level_1_count = 0
    level_2_count = 0
    level_3_count = 0
    level_4_count = 0
    level_5_count = 0
    level_6_count = 0

    if cache_stat:
        level_1_count = cache_stat.level_1_count
        level_2_count = cache_stat.level_2_count
        level_3_count = cache_stat.level_3_count
        level_4_count = cache_stat.level_4_count
        level_5_count = cache_stat.level_5_count
        level_6_count = cache_stat.level_6_count

    # 更新 1 mentor_user_id  stat and cache
    MentorRelationStat.objects(
        mentor_id=mentor_user_id,
        icpper_id=icpper_user_id
    ).update_one(
        upsert=True,
        relation=True,
        has_reward_icpper_count=1 + level_6_count
    )
    MentorLevel7IcpperCountStat.objects(
        mentor_id=mentor_user_id
    ).update_one(
        upsert=True,
        inc__level_1_count=1,
        inc__level_2_count=1 + level_1_count,
        inc__level_3_count=1 + level_2_count,
        inc__level_4_count=1 + level_3_count,
        inc__level_5_count=1 + level_4_count,
        inc__level_6_count=1 + level_5_count,
        inc__level_7_count=1 + level_6_count
    )

    mentor_list = find_mentor_list_of_user(mentor_user_id)
    mentor_list_count = len(mentor_list)
    level_1_mentor = mentor_list[0] if mentor_list_count >= 1 else None
    level_2_mentor = mentor_list[1] if mentor_list_count >= 2 else None
    level_3_mentor = mentor_list[2] if mentor_list_count >= 3 else None
    level_4_mentor = mentor_list[3] if mentor_list_count >= 4 else None
    level_5_mentor = mentor_list[4] if mentor_list_count >= 5 else None
    level_6_mentor = mentor_list[5] if mentor_list_count >= 6 else None

    # 更新 2 mentor_user_id_lev_1 stat and cache
    if level_1_mentor:
        MentorRelationStat.objects(
            mentor_id=str(level_1_mentor.id),
            icpper_id=mentor_user_id
        ).update_one(
            upsert=True,
            inc__has_reward_icpper_count=1 + level_5_count
        )
        MentorLevel7IcpperCountStat.objects(
            mentor_id=str(level_1_mentor.id)
        ).update_one(
            upsert=True,
            inc__level_2_count=1,
            inc__level_3_count=1 + level_1_count,
            inc__level_4_count=1 + level_2_count,
            inc__level_5_count=1 + level_3_count,
            inc__level_6_count=1 + level_4_count,
            inc__level_7_count=1 + level_5_count
        )

    # 更新 3 mentor_user_id_lev_2 stat and cache
    if level_2_mentor:
        MentorRelationStat.objects(
            mentor_id=str(level_2_mentor.id),
            icpper_id=str(level_1_mentor.id)
        ).update_one(
            upsert=True,
            inc__has_reward_icpper_count=1 + level_4_count
        )
        MentorLevel7IcpperCountStat.objects(
            mentor_id=str(level_2_mentor.id)
        ).update_one(
            upsert=True,
            inc__level_3_count=1,
            inc__level_4_count=1 + level_1_count,
            inc__level_5_count=1 + level_2_count,
            inc__level_6_count=1 + level_3_count,
            inc__level_7_count=1 + level_4_count
        )

    # 更新 4 mentor_user_id_lev_3 stat and cache
    if level_3_mentor:
        MentorRelationStat.objects(
            mentor_id=str(level_3_mentor.id),
            icpper_id=str(level_2_mentor.id)
        ).update_one(
            upsert=True,
            inc__has_reward_icpper_count=1 + level_3_count
        )
        MentorLevel7IcpperCountStat.objects(
            mentor_id=str(level_3_mentor.id)
        ).update_one(
            upsert=True,
            inc__level_4_count=1,
            inc__level_5_count=1 + level_1_count,
            inc__level_6_count=1 + level_2_count,
            inc__level_7_count=1 + level_3_count
        )

    # 更新 5 mentor_user_id_lev_4 stat and cache
    if level_4_mentor:
        MentorRelationStat.objects(
            mentor_id=str(level_4_mentor.id),
            icpper_id=str(level_3_mentor.id)
        ).update_one(
            upsert=True,
            inc__has_reward_icpper_count=1 + level_2_count
        )
        MentorLevel7IcpperCountStat.objects(
            mentor_id=str(level_4_mentor.id)
        ).update_one(
            upsert=True,
            inc__level_5_count=1,
            inc__level_6_count=1 + level_1_count,
            inc__level_7_count=1 + level_2_count
        )

    # 更新 6 mentor_user_id_lev_5 stat and cache
    if level_5_mentor:
        MentorRelationStat.objects(
            mentor_id=str(level_5_mentor.id),
            icpper_id=str(level_4_mentor.id)
        ).update_one(
            upsert=True,
            inc__has_reward_icpper_count=1 + level_1_count
        )
        MentorLevel7IcpperCountStat.objects(
            mentor_id=str(level_5_mentor.id)
        ).update_one(
            upsert=True,
            inc__level_6_count=1,
            inc__level_7_count=1 + level_1_count
        )

    # 更新 7 mentor_user_id_lev_6 stat and cache
    if level_6_mentor:
        MentorRelationStat.objects(
            mentor_id=str(level_6_mentor.id),
            icpper_id=str(level_5_mentor.id)
        ).update_one(
            upsert=True,
            inc__has_reward_icpper_count=1
        )
        MentorLevel7IcpperCountStat.objects(
            mentor_id=str(level_6_mentor.id)
        ).update_one(
            upsert=True,
            inc__level_7_count=1
        )


def update_icpper_count_stat_for_delete_icppership(mentor_user_id, icpper_user_id):
    ####
    # 更新人数

    # 获取 icpper_user_id 下七层的人数 cache
    cache_stat = MentorLevel7IcpperCountStat.objects(mentor_id=icpper_user_id).first()
    level_1_count = 0
    level_2_count = 0
    level_3_count = 0
    level_4_count = 0
    level_5_count = 0
    level_6_count = 0

    if cache_stat:
        level_1_count = cache_stat.level_1_count
        level_2_count = cache_stat.level_2_count
        level_3_count = cache_stat.level_3_count
        level_4_count = cache_stat.level_4_count
        level_5_count = cache_stat.level_5_count
        level_6_count = cache_stat.level_6_count

    # 更新 1 mentor_user_id  stat and cache
    MentorRelationStat.objects(
        mentor_id=mentor_user_id,
        icpper_id=icpper_user_id
    ).update_one(
        upsert=True,
        relation=False,
        has_reward_icpper_count=1 + level_6_count
    )
    MentorLevel7IcpperCountStat.objects(
        mentor_id=mentor_user_id
    ).update_one(
        upsert=True,
        inc__level_1_count=-1,
        inc__level_2_count=-(1 + level_1_count),
        inc__level_3_count=-(1 + level_2_count),
        inc__level_4_count=-(1 + level_3_count),
        inc__level_5_count=-(1 + level_4_count),
        inc__level_6_count=-(1 + level_5_count),
        inc__level_7_count=-(1 + level_6_count)
    )

    mentor_list = find_mentor_list_of_user(mentor_user_id)
    mentor_list_count = len(mentor_list)
    level_1_mentor = mentor_list[0] if mentor_list_count >= 1 else None
    level_2_mentor = mentor_list[1] if mentor_list_count >= 2 else None
    level_3_mentor = mentor_list[2] if mentor_list_count >= 3 else None
    level_4_mentor = mentor_list[3] if mentor_list_count >= 4 else None
    level_5_mentor = mentor_list[4] if mentor_list_count >= 5 else None
    level_6_mentor = mentor_list[5] if mentor_list_count >= 6 else None

    # 更新 2 mentor_user_id_lev_1 stat and cache
    if level_1_mentor:
        MentorRelationStat.objects(
            mentor_id=str(level_1_mentor.id),
            icpper_id=mentor_user_id
        ).update_one(
            upsert=True,
            inc__has_reward_icpper_count=-(1 + level_5_count)
        )
        MentorLevel7IcpperCountStat.objects(
            mentor_id=str(level_1_mentor.id)
        ).update_one(
            upsert=True,
            inc__level_2_count=-1,
            inc__level_3_count=-(1 + level_1_count),
            inc__level_4_count=-(1 + level_2_count),
            inc__level_5_count=-(1 + level_3_count),
            inc__level_6_count=-(1 + level_4_count),
            inc__level_7_count=-(1 + level_5_count)
        )

    # 更新 3 mentor_user_id_lev_2 stat and cache
    if level_2_mentor:
        MentorRelationStat.objects(
            mentor_id=str(level_2_mentor.id),
            icpper_id=str(level_1_mentor.id)
        ).update_one(
            upsert=True,
            inc__has_reward_icpper_count=-(1 + level_4_count)
        )
        MentorLevel7IcpperCountStat.objects(
            mentor_id=str(level_2_mentor.id)
        ).update_one(
            upsert=True,
            inc__level_3_count=-1,
            inc__level_4_count=-(1 + level_1_count),
            inc__level_5_count=-(1 + level_2_count),
            inc__level_6_count=-(1 + level_3_count),
            inc__level_7_count=-(1 + level_4_count)
        )

    # 更新 4 mentor_user_id_lev_3 stat and cache
    if level_3_mentor:
        MentorRelationStat.objects(
            mentor_id=str(level_3_mentor.id),
            icpper_id=str(level_2_mentor.id)
        ).update_one(
            upsert=True,
            inc__has_reward_icpper_count=-(1 + level_3_count)
        )
        MentorLevel7IcpperCountStat.objects(
            mentor_id=str(level_3_mentor.id)
        ).update_one(
            upsert=True,
            inc__level_4_count=-1,
            inc__level_5_count=-(1 + level_1_count),
            inc__level_6_count=-(1 + level_2_count),
            inc__level_7_count=-(1 + level_3_count)
        )

    # 更新 5 mentor_user_id_lev_4 stat and cache
    if level_4_mentor:
        MentorRelationStat.objects(
            mentor_id=str(level_4_mentor.id),
            icpper_id=str(level_3_mentor.id)
        ).update_one(
            upsert=True,
            inc__has_reward_icpper_count=-(1 + level_2_count)
        )
        MentorLevel7IcpperCountStat.objects(
            mentor_id=str(level_4_mentor.id)
        ).update_one(
            upsert=True,
            inc__level_5_count=-1,
            inc__level_6_count=-(1 + level_1_count),
            inc__level_7_count=-(1 + level_2_count)
        )

    # 更新 6 mentor_user_id_lev_5 stat and cache
    if level_5_mentor:
        MentorRelationStat.objects(
            mentor_id=str(level_5_mentor.id),
            icpper_id=str(level_4_mentor.id)
        ).update_one(
            upsert=True,
            inc__has_reward_icpper_count=-(1 + level_1_count)
        )
        MentorLevel7IcpperCountStat.objects(
            mentor_id=str(level_5_mentor.id)
        ).update_one(
            upsert=True,
            inc__level_6_count=-1,
            inc__level_7_count=-(1 + level_1_count)
        )

    # 更新 7 mentor_user_id_lev_6 stat and cache
    if level_6_mentor:
        MentorRelationStat.objects(
            mentor_id=str(level_6_mentor.id),
            icpper_id=str(level_5_mentor.id)
        ).update_one(
            upsert=True,
            inc__has_reward_icpper_count=-1
        )
        MentorLevel7IcpperCountStat.objects(
            mentor_id=str(level_6_mentor.id)
        ).update_one(
            upsert=True,
            inc__level_7_count=-1
        )
