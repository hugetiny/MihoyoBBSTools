import re
import config
import setting
from request import http
from loghelper import log
from error import CookieError


def login():
    if config.config["account"]["cookie"] == '':
        log.error("请填入Cookies!")
        config.clear_cookies()
        raise CookieError('No cookie')
    # 判断Cookie里面是否有login_ticket 没有的话直接退了
    login_ticket = get_login_ticket()
    if login_ticket is None:
        log.error("cookie中没有'login_ticket'字段,请重新登录米游社，重新抓取cookie!")
        config.clear_cookies()
        raise CookieError('Cookie lost login_ticket')
    config.config["account"]["login_ticket"] = login_ticket
    uid = get_uid()
    if uid is not None:
        config.config["account"]["stuid"] = uid
        data = http.get(url=setting.bbs_cookie_url2.format(login_ticket, uid)).json()
        config.config["account"]["stoken"] = data["data"]["list"][0]["token"]
        log.info("登录成功！")
        log.info("正在保存Config！")
        config.save_config()
    else:
        log.error("cookie已失效,请重新登录米游社抓取cookie")
        config.clear_cookies()
        raise CookieError('Cookie expires')


def get_login_ticket() -> str:
    ticket_match = re.search(r'login_ticket=(.*?)(?:;|$)', config.config["account"]["cookie"])
    return ticket_match.group(1) if ticket_match else None


def get_uid() -> str:
    uid = None
    uid_match = re.search(r"(account_id|ltuid|login_uid)=(\d+)", config.config["account"]["cookie"])
    if uid_match is None:
        # stuid就是uid，先搜索cookie里面的，搜不到再用api获取
        data = http.get(url=setting.bbs_cookie_url.format(config.config["account"]["login_ticket"])).json()
        if "成功" in data["data"]["msg"]:
            uid = str(data["data"]["cookie_info"]["account_id"])
    else:
        uid = uid_match.group(2)
    return uid
