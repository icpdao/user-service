import requests

from settings import ICPDAO_BOT_TOKEN

def set_discord_role(guild_id, user_id, role_id) -> bool:
    url = f"https://discord.com/api/v8/guilds/{guild_id}/members/{user_id}/roles/{role_id}"

    headers = {
        "Authorization": "Bot " + ICPDAO_BOT_TOKEN
    }
    r = requests.put(url, headers=headers)
    if r.status_code == 200:
        return True
    return False
