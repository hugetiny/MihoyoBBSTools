import collections
import os
import yaml
from copy import deepcopy

from loghelper import log

# 这个字段现在还没找好塞什么地方好，就先塞config这里了
serverless = False
# 提示需要更新config版本
update_config_need = False
# 防止重复加载环境变量
env_loaded = False

config = {
    'enable': True, 'version': 14, "push": "",
    'account': {'cookie': '', 'stuid': '', 'stoken': '', 'mid': ''},
    'device': {'name': 'Xiaomi MI 6', 'model': 'Mi 6', 'id': '', 'fp': ''},
    'mihoyobbs': {
        'enable': True, 'checkin': True, 'checkin_list': [5, 2],
        'read': True, 'like': True, 'cancel_like': True, 'share': True
    },
    'games': {
        'cn': {
            'enable': True,
            'useragent': 'Mozilla/5.0 (Linux; Android 12; Unspecified Device) AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Version/4.0 Chrome/103.0.5060.129 Mobile Safari/537.36',
            'retries': 3,
            'genshin': {'checkin': True, 'black_list': []},
            'honkai2': {'checkin': False, 'black_list': []},
            'honkai3rd': {'checkin': False, 'black_list': []},
            'tears_of_themis': {'checkin': False, 'black_list': []},
            'honkai_sr': {'checkin': False, 'black_list': []},
            'zzz': {'checkin': False, 'black_list': []}
        },
        'os': {
            'enable': False, 'cookie': '', 'lang': 'zh-cn',
            'genshin': {'checkin': False, 'black_list': []},
            'honkai3rd': {'checkin': False, 'black_list': []},
            'tears_of_themis': {'checkin': False, 'black_list': []},
            'honkai_sr': {'checkin': False, 'black_list': []},
            'zzz': {'checkin': False, 'black_list': []}
        }
    },
    'cloud_games': {
        "cn": {
            "enable": False,
            "genshin": {'enable': False, 'token': ""},
            "zzz": {'enable': False, 'token': ""}
        },
        "os": {
            "enable": False, 'lang': 'zh-cn',
            "genshin": {'enable': False, 'token': ""}
        }
    },

    'competition': {
        'enable': False,
        'genius_invokation': {'enable': False, 'account': [], 'checkin': False, 'weekly': False}
    }
}
config_raw = deepcopy(config)

path = os.path.dirname(os.path.realpath(__file__)) + "/config"
if os.getenv("AutoMihoyoBBS_config_path") is not None:
    path = os.getenv("AutoMihoyoBBS_config_path")
config_prefix = os.getenv("AutoMihoyoBBS_config_prefix")
if config_prefix is None:
    config_prefix = ""
config_Path = f"{path}/{config_prefix}config.yaml"


def copy_config():
    return config_raw


def config_v10_update(data: dict):
    global update_config_need
    update_config_need = True
    data['version'] = 11
    data['account']['mid'] = ""
    genius = data['competition']['genius_invokation']
    new_keys = ['enable', 'account', 'checkin', 'weekly']
    data['competition']['genius_invokation'] = dict(collections.OrderedDict(
        (key, genius.get(key, False) if key != 'account' else []) for key in new_keys))
    log.info("config 已升级到：11")
    return data


def config_v11_update(data: dict):
    global update_config_need
    update_config_need = True
    data['version'] = 13
    new_config = {}
    for key in data:
        if key == "account":
            new_config["push"] = ""
        if key == "cloud_games":
            new_config['cloud_games'] = deepcopy(config_raw['cloud_games'])
            continue
        new_config[key] = deepcopy(data[key])
    new_config['cloud_games']['cn']['enable'] = data['cloud_games']['genshin']['enable']
    new_config['cloud_games']['cn']['genshin']['enable'] = data['cloud_games']['genshin']['enable']
    new_config['cloud_games']['cn']['genshin']['token'] = data['cloud_games']['genshin']['token']
    log.info("config 已升级到：13")
    return new_config


def config_v12_update(data: dict):
    global update_config_need
    update_config_need = True
    data['version'] = 13
    data['cloud_games']['cn']['zzz'] = {'enable': False, 'token': ""}
    log.info("config 已升级到: 13")
    return data


def config_v13_update(data: dict):
    global update_config_need
    update_config_need = True
    new_config = deepcopy(data)

    # 确保版本号更新为14
    new_config['version'] = 14
    new_config['device']['fp'] = config['device'].get('fp', '')

    log.info("config 已升级到：14")
    return new_config


def load_dotenv():
    """简单的.env文件加载器"""
    global env_loaded
    if env_loaded:
        return True
        
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip().strip('"\'')
            log.info("已从.env文件加载环境变量")
            env_loaded = True
            return True
        except Exception as e:
            log.warning(f"加载.env文件失败: {e}")
    return False


def load_config(p_path=None):
    global config, serverless, env_loaded
    if not p_path:
        p_path = config_Path
    
    # 尝试加载.env文件 (只在第一次加载时)
    if not env_loaded:
        load_dotenv()
    
    # 检查是否为CI环境
    is_ci = os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS") == "true"
    if is_ci:
        serverless = True
        if not env_loaded:  # 只在第一次时输出
            log.info("检测到CI环境，启用无状态模式")
    
    with open(p_path, "r", encoding='utf-8') as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
    
    # 从环境变量覆盖账号信息 (只在第一次时输出日志)
    env_cookie = os.getenv("MIHOYO_COOKIE")
    env_stuid = os.getenv("MIHOYO_STUID")
    env_stoken = os.getenv("MIHOYO_STOKEN")
    env_mid = os.getenv("MIHOYO_MID")
    
    if env_cookie:
        data['account']['cookie'] = env_cookie
        if not env_loaded:
            log.info("已从环境变量加载 Cookie")
    if env_stuid:
        data['account']['stuid'] = env_stuid
        if not env_loaded:
            log.info("已从环境变量加载 STUID")
    if env_stoken:
        data['account']['stoken'] = env_stoken
        if not env_loaded:
            log.info("已从环境变量加载 Stoken")
    if env_mid:
        data['account']['mid'] = env_mid
        if not env_loaded:
            log.info("已从环境变量加载 MID")
    
    if data['version'] != config_raw['version']:
        if data['version'] == 10:
            data = config_v10_update(data)
        if data['version'] == 11:
            data = config_v11_update(data)
        if data['version'] == 12:
            data = config_v12_update(data)
        if data['version'] == 13:
            data = config_v13_update(data)
        save_config(p_config=data)
    # 去除cookie最末尾的空格
    data["account"]["cookie"] = str(data["account"]["cookie"]).rstrip(' ')
    
    # 自动生成设备ID
    if data["device"]["id"] == "" or data["device"]["id"] == "auto-generate":
        import tools
        data["device"]["id"] = tools.get_device_id(data["account"]["cookie"])
        if not env_loaded:
            log.info(f"自动生成设备ID: {data['device']['id']}")
    
    config = data
    if not env_loaded:
        log.info("Config 加载完毕")
        env_loaded = True  # 标记已完成首次加载
    return data


def save_config(p_path=None, p_config=None):
    global serverless
    if serverless:
        log.info("云函数执行，无法保存")
        return None
    if not p_path:
        p_path = config_Path
    if not p_config:
        p_config = config
    
    # 创建一个副本，移除来自环境变量的敏感信息
    clean_config = deepcopy(p_config)
    
    # 如果有环境变量，说明敏感信息来自环境变量，不应保存到文件
    if os.getenv("MIHOYO_COOKIE"):
        clean_config["account"]["cookie"] = ""
    if os.getenv("MIHOYO_STOKEN"):
        clean_config["account"]["stoken"] = ""
    if os.getenv("MIHOYO_STUID"):
        clean_config["account"]["stuid"] = ""
    if os.getenv("MIHOYO_MID"):
        clean_config["account"]["mid"] = ""
    
    with open(p_path, "w+") as f:
        try:
            f.seek(0)
            f.truncate()
            f.write(yaml.dump(clean_config, Dumper=yaml.Dumper, sort_keys=False))
            f.flush()
        except OSError:
            serverless = True
            log.info("Cookie 保存失败")
        else:
            log.info("Config 保存完毕")


def clear_stoken():
    global config
    if serverless:
        log.info("云函数执行，无法保存")
        return None
    config["account"]["mid"] = ""
    config["account"]["stuid"] = ""
    config["account"]["stoken"] = "StokenError"
    log.info("Stoken 已删除")
    save_config()


def clear_cookie():
    global config
    if serverless:
        log.info("云函数执行，无法保存")
        return None
    config["account"]["cookie"] = "CookieError"
    log.info(f"Cookie 已删除")
    save_config()


def disable_games(region: str = "cn"):
    global config
    if serverless:
        log.info("云函数执行，无法保存")
        return None
    config['games'][region]['enable'] = False
    log.info(f"游戏签到（{region}）已关闭")
    save_config()


def clear_cookie_cloudgame_genshin():
    global config
    if serverless:
        log.info("云函数执行，无法保存")
        return None
    config['cloud_games']['cn']['genshin']["enable"] = False
    config['cloud_games']['cn']['genshin']['token'] = ""
    log.info("国服云原神 Cookie 删除完毕")
    save_config()


def clear_cookie_cloudgame_genshin_os():
    global config
    if serverless:
        log.info("云函数执行，无法保存")
        return None
    config['cloud_games']['os']['genshin']["enable"] = False
    config['cloud_games']['os']['genshin']['token'] = ""
    log.info("国际服云原神 Cookie 删除完毕")
    save_config()


def clear_cookie_cloudgame_zzz():
    global config
    if serverless:
        log.info("云函数执行，无法保存")
        return None
    config['cloud_games']['cn']['zzz']["enable"] = False
    config['cloud_games']['cn']['zzz']['token'] = ""
    log.info("国服云绝区零 Cookie 删除完毕")
    save_config()


if __name__ == "__main__":
    # 初始化配置文件
    # try:
    #     account_cookie = config['account']['cookie']
    #     config = load_config()
    #     config['account']['cookie'] = account_cookie
    # except OSError:
    #     pass
    # save_config()
    # update_config()
    pass
