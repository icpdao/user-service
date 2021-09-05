from fastapi import Request, APIRouter

from pydantic import BaseModel
from redis.exceptions import LockNotOwnedError, LockError

from app.common.models.logic.user_helper import pre_icpper_to_icpper, icppership_accept, icppership_cancle_accept
from app.common.utils.errors import ICPPER_NOT_FOUND_ERROR, COMMON_NOT_PERMISSION_ERROR, ICPPER_LOOP_BACK_ERROR, \
    COMMON_TIMEOUT_ERROR, ICPPER_PRE_MENTOR_MAX_ERROR, ICPPER_ALREADY_MENTOR_ERROR
from app.common.utils.route_helper import get_current_user
from app.common.models.icpdao.user import User, UserStatus
from app.common.models.icpdao.icppership import Icppership, IcppershipStatus, IcppershipProgress
from settings import ICPDAO_REDIS_LOCK_DB_CONN


router = APIRouter()

PRE_MENTOR_ICPPERSHIP_COUNT_LIMIT = 10

LINK_MENTOR_AND_ICPPER_LOCK_KEY = "lock:LINK_MENTOR_AND_ICPPER_LOCK_KEY"


class CreateItem(BaseModel):
    icpper_github_login: str


def to_icppership_dict(icppership, icpper=None, icpper_icpper_count=0):
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
            "nickname":        nickname,
            "github_login":    github_login,
        },
        "icpper_icpper_count": icpper_icpper_count,
        "create_at":           icppership.create_at,
        "accept_at":           icppership.accept_at, 
        "icpper_at":           icppership.icpper_at, 
    }


@router.put('/icpperships/{icppership_id}/accept')
async def accept(icppership_id, request: Request):
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
            mentor_list = find_mentor_list_of_user(mentor)
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
        if Icppership.objects(mentor_user_id=str(user.id)).count() >= PRE_MENTOR_ICPPERSHIP_COUNT_LIMIT:
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
    mentor_list = find_mentor_list_of_user(user)
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

    return {
        "success": True,
        "data": {}
    }


@router.get('/icpperships')
async def get_list(request: Request):
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

    res = [to_icppership_dict(item, user_id_2_icpper.get(item.icpper_user_id, None), user_id_2__icpper_count.get(item.icpper_user_id, 0)) for item in is_list]

    return {
        "success": True,
        "data": res
    }


def find_mentor_list_of_user(user):
    # 找 user 的七个上级
    mentor_user_id_list = []
    current_user_id = str(user.id)
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
        return [user for user in User.objects(id__in=mentor_user_id_list)]
    else:
        return []
