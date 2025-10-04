# 当前脚本来自于http://script.345yun.cn脚本库下载！
"""
 作者:  临渊
 日期:  2025/6/30
 小程序:    康师傅畅饮社 (https://s.c1ns.cn/GekGz)
 功能:  签到、查积分、每日C活动(签到、视频、邀请、小游戏)
 变量:  ksf_wxid_data (微信id) 多个账号用换行分割 
        PROXY_API_URL (代理api，返回一条txt文本，内容为代理ip:端口)
 定时:  一天两次
 cron:  10 8,9 * * *
 更新日志：
 2025/6/30 V1.0 初始化脚本
 2025/6/30 V1.1 修复助力错账号问题
 2025/6/30 V1.2 修复查询信息错误
 2025/7/7  V1.3 适配更多协议
 2025/7/7  V1.4 使用wex_get模块统一微信授权接口
"""

MULTI_ACCOUNT_SPLIT = ["\n", "@","&"] # 分隔符列表
MULTI_ACCOUNT_PROXY = False # 是否使用多账号代理，默认不使用，True则使用多账号代理
NOTIFY = False # 是否推送日志，默认不推送，True则推送

import json
import random
import time
import requests
import os
import logging
import traceback
import ssl
from datetime import datetime
# 导入wex_get模块中的wx_code_auth方法
from wex_get import wx_code_auth

class TLSAdapter(requests.adapters.HTTPAdapter):
    """
    自定义TLS
    解决unsafe legacy renegotiation disabled
    貌似python太高版本依然会报错
    """
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.set_ciphers("DEFAULT@SECLEVEL=1")
        ctx.options |= 0x4   # <-- the key part here, OP_LEGACY_SERVER_CONNECT
        kwargs["ssl_context"] = ctx
        return super(TLSAdapter, self).init_poolmanager(*args, **kwargs)

class AutoTask:
    def __init__(self, script_name):
        """
        初始化自动任务类
        :param script_name: 脚本名称，用于日志显示
        """
        self.script_name = script_name
        self.log_msgs = []  # 日志收集
        self.proxy_url = os.getenv("PROXY_API_URL") # 代理api，返回一条txt文本，内容为代理ip:端口
        self.wx_appid = "wx54f3e6a00f7973a7" # 微信小程序id
        self.host = ""
        self.unionid = ""
        self.nickname = ""
        self.user_agent = "Mozilla/5.0 (Linux; Android 12; M2012K11AC Build/SKQ1.220303.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/134.0.6998.136 Mobile Safari/537.36 XWEB/1340129 MMWEBSDK/20240301 MMWEBID/9871 MicroMessenger/8.0.48.2580(0x28003036) WeChat/arm64 Weixin NetType/WIFI Language/zh_CN ABI/arm64 MiniProgramEnv/android"
        self.setup_logging()
        
    def setup_logging(self):
        """
        配置日志系统
        """
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s\t- %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                # logging.FileHandler(f'{self.script_name}_{datetime.now().strftime("%Y%m%d")}.log', encoding='utf-8'),  # 保存日志
                logging.StreamHandler()
            ]
        )

    def log(self, msg, level="info"):
        if level == "info":
            logging.info(msg)
        elif level == "error":
            logging.error(msg)
        elif level == "warning":
            logging.warning(msg)
        self.log_msgs.append(msg)

    def get_proxy(self):
        """
        获取代理
        :return: 代理
        """
        if not self.proxy_url:
            self.log("[获取代理] 没有找到环境变量PROXY_API_URL，不使用代理", level="warning")
            return None
        url = self.proxy_url
        response = requests.get(url)
        proxy = response.text
        self.log(f"[获取代理] {proxy}")
        return proxy
    
    def check_proxy(self, proxy, session):
        """
        检查代理
        :param proxy: 代理
        :param session: session
        :return: 是否可用
        """
        try:
            url = f"https://club.biqr.cn/api/index/getBasic"
            response = session.get(url, timeout=5)
            if response.status_code == 200:
                self.log(f"[检查代理] {proxy} 应该可用")
                return True
            else:
                self.log(f"[检查代理] {response.text}")
                return False
        except Exception as e:
            return False
        

    def check_env(self):
        """
        检查环境变量
        :return: 环境变量字符串
        """
        try:
            # 从环境变量获取cookie
            soy_wxid_data = os.getenv(f"ksf_wxid_data")
            if not soy_wxid_data:
                self.log("[检查环境变量] 没有找到环境变量ksf_wxid_data，请检查环境变量", level="error")
                return None

            # 自动检测分隔符
            split_char = None
            for sep in MULTI_ACCOUNT_SPLIT:
                if sep in soy_wxid_data:
                    split_char = sep
                    break
            if not split_char:
                # 如果都没有分隔符，默认当作单账号
                soy_wxid_datas = [soy_wxid_data]
            else:
                soy_wxid_datas = soy_wxid_data.split(split_char)

            for soy_wxid_data in soy_wxid_datas:
                if "=" in soy_wxid_data:
                    soy_wxid_data = soy_wxid_data.split("=")[1]
                    yield soy_wxid_data
                else:
                    yield soy_wxid_data
        except Exception as e:
            self.log(f"[检查环境变量] 发生错误: {str(e)}\n{traceback.format_exc()}", level="error")
            raise

    def dict_keys_to_lower(self, obj):
        """
        递归将字典的所有键名转为小写
        """
        if isinstance(obj, dict):
            return {k.lower(): self.dict_keys_to_lower(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.dict_keys_to_lower(i) for i in obj]
        else:
            return obj

        
    def wxlogin(self, session, code):
        """
        登录
        :param session: session
        :param code: 微信code
        :return: 登录结果
        """
        try:
            url = f"https://nclub.gdshcm.com/pro/whale-member/api/login/login"
            payload = {
                "code": code,
                "inviterId": "6816542043825766400",
                "inviterType": 1,
                "inviterMatchUserId": "",
                "spUrl": "null"
            }
            response = session.post(url, json=payload, timeout=5)
            response_json = response.json()
            if int(response_json['code']) == 0:
                token = response_json['data']['token']
                self.nickname = response_json['data']['member']['nickname']
                self.unionid = response_json['data']['member']['unionid']
                score = response_json['data']['member']['integral']
                session.headers["Token"] = token
                self.log(f"[{self.nickname}] 登录: 成功 积分: {score}")
                return True
            else:
                self.log(f"[登录] 失败，错误信息: {response_json['msg']}", level="error")
                return False
        except requests.RequestException as e:
            self.log(f"[登录] 发生网络错误: {str(e)}\n{traceback.format_exc()}", level="error")
            return False
        except Exception as e:
            self.log(f"[登录] 发生错误: {str(e)}\n{traceback.format_exc()}", level="error")
            return False

    def sign_in(self, session):
        """
        签到
        :param session: session
        :return: 签到结果
        """
        try:
            url = f"https://club.biqr.cn/api/signIn/integralSignIn"
            payload = "{}="
            response = session.post(url, data=payload, timeout=5)
            response_json = response.json()
            if int(response_json['code']) == 0:
                self.log(f"[{self.nickname}] 签到: 成功")
                return True
            else:
                self.log(f"[{self.nickname}] 签到: {response_json['msg']}", level="warning")
                return False
        except Exception as e:
            self.log(f"[{self.nickname}] 签到: 发生错误: {str(e)}\n{traceback.format_exc()}", level="error")
            return False
        
    def daily_c_signin(self, session):
        """
        活动每日C 签到
        :param session: session
        :return: 签到结果
        """
        try:
            url = f"https://ksfdailyc-api.teown.com/api/sign_in.php"
            params = {
                "_": int(time.time()*1000),
            }
            payload = f"unionid={self.unionid}&timestamp={int(time.time())}"
            session.headers["Content-Type"] = "application/x-www-form-urlencoded"
            response = session.post(url, params=params, data=payload, timeout=5)
            response_json = response.json()
            if response_json['errcode'] == 8000:
                self.log(f"[{self.nickname}] 每日C 签到: 成功，获得{response_json['data']['score']}VC值")
                return True
            else:
                self.log(f"[{self.nickname}] 每日C 签到: {response_json['errmsg']}", level="warning")
                return False
        except Exception as e:
            self.log(f"[{self.nickname}] 每日C 签到: 发生错误: {str(e)}\n{traceback.format_exc()}", level="error")
            return False
        
    def daily_c_video(self, session):
        """
        活动每日C 视频
        :param session: session
        :return: 视频结果
        """
        try:
            url = f"https://ksfdailyc-api.teown.com/api/video.php"
            params = {
                "_": int(time.time()*1000),
            }
            payload = f"unionid={self.unionid}&timestamp={int(time.time())}"
            response = session.post(url, params=params, data=payload, timeout=5)
            response_json = response.json()
            if response_json['errcode'] == 8000:
                self.log(f"[{self.nickname}] 每日C 视频: 请求成功")
                return True
            else:
                self.log(f"[{self.nickname}] 每日C 视频: {response_json['errmsg']}", level="warning")
                return False
        except Exception as e:
            self.log(f"[{self.nickname}] 每日C 视频: 发生错误: {str(e)}\n{traceback.format_exc()}", level="error")
            return False
        
    def daily_c_mini_game(self, session):
        """
        活动每日C 小游戏
        :param session: session
        :return: 小游戏结果
        """
        try:
            url = f"https://club.biqr.cn/api/juiceGame/saveLog"
            payload = {
                "score": "u7Y2YshA2NFqWJIwDWXbZL%2BQ40o1WkNpiFnGzG1p73faQyVZ1BrGysG9U%2B%2BH7w2Zh%2Fmiz29ft3IqB%2F1EGN4O7GOz5CS5uTyIEhVxDOYJ5yhVel4KJaPApDRju%2FAmNy00Il%2BXlNsPkpJ%2F8PhZx0ov3HmPstIrwYPMnkdrDcwgnPY%3D"
            }
            response = session.post(url, json=payload, timeout=5)
            response_json = response.json()
            if response_json['code'] == 0:
                self.log(f"[{self.nickname}] 每日C 小游戏: 保存成绩成功")
                return True
            else:
                self.log(f"[{self.nickname}] 每日C 小游戏: {response_json['msg']}", level="warning")
                return False
        except Exception as e:
            self.log(f"[{self.nickname}] 每日C 小游戏: 发生错误: {str(e)}\n{traceback.format_exc()}", level="error")
            return False
        
    def daily_c_write_invite_unionid_list(self, unionid_list):
        """
        活动每日C 写入邀请unionid列表
        :param unionid_list: 邀请unionid列表
        """
        try:
            with open("daily_c_invite_unionid.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(unionid_list))
        except Exception as e:
            self.log(f"每日C 写入邀请unionid列表: 发生错误: {str(e)}\n{traceback.format_exc()}", level="error")
            return False
            
    def daily_c_get_invite_unionid_list(self):
        """
        活动每日C 获取邀请unionid列表
        :return: 邀请unionid列表
        """
        try:
            # 检查是否存在文件
            if not os.path.exists("daily_c_invite_unionid.txt"):
                return []
            # 读取文件
            with open("daily_c_invite_unionid.txt", "r", encoding="utf-8") as f:
                unionid_list = f.readlines()
            return unionid_list
        except Exception as e:
            self.log(f"[{self.nickname}] 每日C 获取邀请unionid: 发生错误: {str(e)}\n{traceback.format_exc()}", level="error")
            return []
    
    def daily_c_invite(self, session, unionid):
        """
        活动每日C 邀请/查信息
        :param session: session
        :param unionid: 邀请unionid
        :return: 邀请结果
        """
        try:
            url = f"https://ksfdailyc-api.teown.com/api/login.php"
            params = {
                "_": int(time.time()*1000),
            }
            payload = f"unionid={unionid}&refer={self.unionid}&timestamp={int(time.time())}"
            response = session.post(url, params=params, data=payload, timeout=5)
            response_json = response.json()
            if response_json['errcode'] == 8000:
                if unionid != self.unionid:
                    self.log(f"[{self.nickname}] 每日C 尝试邀请: 成功")
                else:
                    self.log(f"[{self.nickname}] 每日C 任务: 签到 {response_json['data']['sign_in_score']}/{response_json['data']['daily_sign_in_score']} 视频 {response_json['data']['video_score']}/{response_json['data']['daily_video_score']} 分享 {response_json['data']['share_score']}/{response_json['data']['daily_share_score']} 小游戏 {response_json['data']['game_score']}/{response_json['data']['daily_game_score']}""")
                    self.log(f"[{self.nickname}] 每日C 总VC值: {response_json['data']['score']}")
                    return True
            else:
                self.log(f"[{self.nickname}] 每日C 尝试邀请: {response_json['errmsg']}", level="warning")
                return False
        except Exception as e:
            self.log(f"[{self.nickname}] 每日C 尝试邀请: 发生错误: {str(e)}\n{traceback.format_exc()}", level="error")
            return False
        
    def run(self):
        """
        运行任务
        """
        try:
            self.log(f"【{self.script_name}】开始执行任务")
            
            # unionid列表
            unionid_list = []
            # 检查环境变量
            for index, wx_id in enumerate(self.check_env(), 1):
                self.log("")
                self.log(f"------ 【账号{index}】开始执行任务 ------")

                if MULTI_ACCOUNT_PROXY:
                    proxy = self.get_proxy()
                    if proxy:
                        session = requests.Session()
                        session.proxies.update({"http": f"http://{proxy}", "https": f"http://{proxy}"})
                        # 检查代理，不可用重新获取
                        while not self.check_proxy(proxy, session):
                            proxy = self.get_proxy()
                            session.proxies.update({"http": f"http://{proxy}", "https": f"http://{proxy}"})
                    else:
                        session = requests.Session()
                else:
                    session = requests.Session()
                    
                session.headers["User-Agent"] = self.user_agent

                # 执行微信授权
                code = wx_code_auth(wx_id, self.wx_appid)
                if code:
                    if self.wxlogin(session, code):
                        # 签到
                        self.sign_in(session)
                        """
                        每日C活动
                        """
                        # 小游戏 - 持续执行直到失败
                        while True:
                            if not self.daily_c_mini_game(session):
                                break
                        # 签到
                        self.daily_c_signin(session)
                        # 视频
                        self.daily_c_video(session)
                        # 获取邀请unionid列表
                        invite_unionid_list = self.daily_c_get_invite_unionid_list()
                        # 邀请
                        if invite_unionid_list:
                            # 去除当前账号unionid
                            invite_unionid_list = [uid.strip() for uid in invite_unionid_list if uid.strip() and uid.strip() != self.unionid]
                            # 如果大于5个，随机取5个，否则直接全部
                            if len(invite_unionid_list) > 5:
                                invite_unionid_list = random.sample(invite_unionid_list, 5)
                            # 邀请
                            for invite_unionid in invite_unionid_list:
                                self.daily_c_invite(session, invite_unionid)
                        # 积分
                        self.daily_c_invite(session, self.unionid)
                        # 当前账号unionid写入邀请unionid列表
                        unionid_list.append(self.unionid)
                                
                self.log(f"------ 【账号{index}】执行任务完成 ------")
            # 写入邀请unionid列表
            self.daily_c_write_invite_unionid_list(unionid_list)
        except Exception as e:
            self.log(f"【{self.script_name}】执行过程中发生错误: {str(e)}\n{traceback.format_exc()}", level="error")
        finally:
            if NOTIFY:
                # 如果notify模块不存在，从远程下载至本地
                if not os.path.exists("notify.py"):
                    url = "https://raw.githubusercontent.com/whyour/qinglong/refs/heads/develop/sample/notify.py"
                    response = requests.get(url)
                    with open("notify.py", "w", encoding="utf-8") as f:
                        f.write(response.text)
                    import notify
                else:
                    import notify
                # 任务结束后推送日志
                title = f"{self.script_name} 运行日志"
                header = "作者：临渊\n"
                content = header + "\n" +"\n".join(self.log_msgs)
                notify.send(title, content)


if __name__ == "__main__":
    auto_task = AutoTask("康师傅畅饮社")
    auto_task.run() 
# 当前脚本来自于http://script.345yun.cn脚本库下载！