# 当前脚本来自于http://script.345yun.cn脚本库下载！
"""
 作者:  临渊
 日期:  2025/7/1
 小程序:    红人库 (https://s.c1ns.cn/EO1Zb)
 功能:  签到、查询积分
 变量:  hrk_wxid_data (微信id) 多个账号用换行分割 
        PROXY_API_URL (代理api，返回一条txt文本，内容为代理ip:端口)
 定时:  一天两次
 cron:  10 8,9 * * *
 更新日志：
 2025/7/1 V1.0 初始化脚本
 2025/7/7 V1.1 适配协议核心插件
 2025/7/7 V1.2 使用wex_get模块统一微信授权接口
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
        self.wx_appid = "wx44356198837c0121" # 微信小程序id
        self.host = "xapi.weimob.com"
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
            url = f"http://{self.host}/api3/onecrm/mactivity/santa/core/showCActivityPop"
            payload = {"appid":"wx532ecb3bdaaf92f9","basicInfo":{"vid":6015049204105,"vidType":2,"bosId":4020386662105,"productId":1,"productInstanceId":1021218105,"productVersionId":"36000","merchantId":2000027614105,"tcode":"weimob","cid":114397105},"extendInfo":{"wxTemplateId":7912,"analysis":[],"bosTemplateId":1000001980,"childTemplateIds":[{"customId":90004,"version":"crm@0.1.63"},{"customId":90002,"version":"ec@68.1"},{"customId":90006,"version":"hudong@0.0.229"},{"customId":90008,"version":"cms@0.0.504"}],"quickdeliver":{"enable":"false"},"youshu":{"enable":"false"},"source":1,"channelsource":5,"refer":"cms-index","mpScene":1302},"queryParameter":"null","i18n":{"language":"zh","timezone":"8"},"pid":"4020386662105","storeId":"0","targetBasicInfo":{"productInstanceId":1021082105}}
            response = session.post(url, json=payload, timeout=5)
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
            soy_wxid_data = os.getenv(f"hrk_wxid_data")
            if not soy_wxid_data:
                self.log("[检查环境变量] 没有找到环境变量hrk_wxid_data，请检查环境变量", level="error")
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
            url = f"https://{self.host}/fe/mapi/user/loginX"
            payload = {
                "appid": "wx44356198837c0121",
                "basicInfo": {
                    "bosId": "4020386662105",
                    "cid": "114397105",
                    "tcode": "weimob",
                    "vid": "6015049204105"
                },
                "env": "production",
                "extendInfo": {
                    "source": 1
                },
                "is_pre_fetch_open": "true",
                "parentVid": 0,
                "pid": "4020386662105",
                "storeId": "0",
                "code": code,
                "queryAuthConfig": "true"
            }
            response = session.post(url, json=payload, timeout=5)
            response_json = response.json()
            if int(response_json['errcode']) == 0:
                self.log(f"[登录] 成功")
                token = response_json['data']['token']
                session.headers["x-wx-token"] = token
                return True
            else:
                self.log(f"[登录] 发生错误: {response_json['errmsg']}", level="error")
                return False
        except requests.RequestException as e:
            self.log(f"[登录] 发生网络错误: {str(e)}\n{traceback.format_exc()}", level="error")
            return False
        except Exception as e:
            self.log(f"[登录] 发生错误: {str(e)}\n{traceback.format_exc()}", level="error")
            return False
        
    def get_sign_info(self, session):
        """
        获取签到信息
        :param session: session
        :return: 签到信息
        """
        try:
            url = f"https://{self.host}/api3/onecrm/mactivity/sign/misc/sign/activity/c/signMainInfo"
            payload = {
                "appid": "wx44356198837c0121",
                "basicInfo": {
                    "vid": 6015049204105,
                    "vidType": 2,
                    "bosId": 4020386662105,
                    "productId": 146,
                    "productInstanceId": 1021082105,
                    "productVersionId": "10003",
                    "merchantId": 2000027614105,
                    "tcode": "weimob",
                    "cid": 114397105
                },
                "extendInfo": {
                    "wxTemplateId": 7912,
                    "analysis": [],
                    "bosTemplateId": 1000001980,
                    "childTemplateIds": [
                        {
                            "customId": 90004,
                            "version": "crm@0.1.62"
                        },
                        {
                            "customId": 90002,
                            "version": "ec@67.1"
                        },
                        {
                            "customId": 90006,
                            "version": "hudong@0.0.227"
                        },
                        {
                            "customId": 90008,
                            "version": "cms@0.0.503"
                        }
                    ],
                    "quickdeliver": {
                        "enable": "false"
                    },
                    "youshu": {
                        "enable": "false"
                    },
                    "source": 1,
                    "channelsource": 5,
                    "refer": "onecrm-signgift",
                    "mpScene": 1302
                },
                "queryParameter": "null",
                "i18n": {
                    "language": "zh",
                    "timezone": "8"
                },
                "pid": "",
                "storeId": "",
                "customInfo": {
                    "source": 0,
                    "wid": 11649425250
                }
            }
            response = session.post(url, json=payload)
            response_json = response.json()
            if int(response_json['errcode']) == 0:
                return response_json['data']['hasSign']
            else:
                self.log(f"[获取签到信息] 发生错误: {response_json['errmsg']}", level="error")
                return False
        except Exception as e:
            self.log(f"[获取签到信息] 发生错误: {str(e)}\n{traceback.format_exc()}", level="error")
            return False

    def sign_in(self, session):
        """
        签到
        :param session: session
        :return: 签到结果
        """
        try:
            url = f"https://{self.host}/api3/onecrm/mactivity/sign/misc/sign/activity/core/c/sign"
            payload = {
                "appid": "wx44356198837c0121",
                "basicInfo": {
                    "vid": 6015049204105,
                    "vidType": 2,
                    "bosId": 4020386662105,
                    "productId": 146,
                    "productInstanceId": 1021082105,
                    "productVersionId": "10003",
                    "merchantId": 2000027614105,
                    "tcode": "weimob",
                    "cid": 114397105
                },
                "extendInfo": {
                    "wxTemplateId": 7912,
                    "analysis": [],
                    "bosTemplateId": 1000001980,
                    "childTemplateIds": [
                        {
                            "customId": 90004,
                            "version": "crm@0.1.62"
                        },
                        {
                            "customId": 90002,
                            "version": "ec@67.1"
                        },
                        {
                            "customId": 90006,
                            "version": "hudong@0.0.227"
                        },
                        {
                            "customId": 90008,
                            "version": "cms@0.0.503"
                        }
                    ],
                    "quickdeliver": {
                        "enable": "false"
                    },
                    "youshu": {
                        "enable": "false"
                    },
                    "source": 1,
                    "channelsource": 5,
                    "refer": "onecrm-signgift",
                    "mpScene": 1302
                },
                "queryParameter": "null",
                "i18n": {
                    "language": "zh",
                    "timezone": "8"
                },
                "pid": "",
                "storeId": "",
                "customInfo": {
                    "source": 0,
                    "wid": 11649425250
                }
            }
            response = session.post(url, json=payload)
            response_json = response.json()
            if int(response_json['errcode']) == 0:
                self.log(f"[签到] {response_json['errmsg']} 获得: {response_json['data']['fixedReward']['points']}积分 额外获得:{response_json['data']['extraReward']['points']}积分")
                return True
            else:
                self.log(f"[签到] {response_json['errmsg']}", level="warning")
                return False
        except Exception as e:
            self.log(f"[签到] 发生错误: {str(e)}\n{traceback.format_exc()}", level="error")
            return False
        
    def get_points(self, session):
        """
        查询积分
        :param session: session
        :return: 积分
        """
        try:
            url = f"https://{self.host}/api3/onecrm/point/myPoint/getSimpleAccountInfo"
            payload = {
                "appid": "wx44356198837c0121",
                "basicInfo": {
                    "vid": 6015049204105,
                    "vidType": 2,
                    "bosId": 4020386662105,
                    "productId": 1,
                    "productInstanceId": 1021218105,
                    "productVersionId": "36000",
                    "merchantId": 2000027614105,
                    "tcode": "weimob",
                    "cid": 114397105
                },
                "extendInfo": {
                    "wxTemplateId": 7912,
                    "analysis": [],
                    "bosTemplateId": 1000001980,
                    "childTemplateIds": [
                        {
                            "customId": 90004,
                            "version": "crm@0.1.62"
                        },
                        {
                            "customId": 90002,
                            "version": "ec@67.1"
                        },
                        {
                            "customId": 90006,
                            "version": "hudong@0.0.227"
                        },
                        {
                            "customId": 90008,
                            "version": "cms@0.0.503"
                        }
                    ],
                    "quickdeliver": {
                        "enable": "false"
                    },
                    "youshu": {
                        "enable": "false"
                    },
                    "source": 1,
                    "channelsource": 5,
                    "refer": "cms-usercenter",
                    "mpScene": 1302
                },
                "queryParameter": "null",
                "i18n": {
                    "language": "zh",
                    "timezone": "8"
                },
                "pid": "",
                "storeId": "",
                "targetBasicInfo": {
                    "productInstanceId": 1021082105
                },
                "request": {}
            }
            response = session.post(url, json=payload)
            response_json = response.json()
            if int(response_json['errcode']) == 0:
                self.log(f"[积分] {response_json['data']['availablePoint']}")
                return response_json['data']['availablePoint']
            else:
                self.log(f"[积分] {response_json['errmsg']}", level="warning")
                return False
        except Exception as e:
            self.log(f"[积分] 发生错误: {str(e)}\n{traceback.format_exc()}", level="error")
            return False

    def run(self):
        """
        运行任务
        """
        try:
            self.log(f"【{self.script_name}】开始执行任务")
            
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
                code = self.wx_code_auth(wx_id)
                if code:
                    if self.wxlogin(session, code):
                        if not self.get_sign_info(session):
                            # 签到
                            self.sign_in(session)
                            time.sleep(random.randint(1, 3))
                        else:
                            self.log(f"[签到] 今日已签到", level="warning")
                        # 查询积分
                        self.get_points(session)
                self.log(f"------ 【账号{index}】执行任务完成 ------")
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
                header = "作者：临渊\n\n"
                content = header + "\n" +"\n".join(self.log_msgs)
                notify.send(title, content)


if __name__ == "__main__":
    auto_task = AutoTask("红人库")
    auto_task.run() 
# 当前脚本来自于http://script.345yun.cn脚本库下载！