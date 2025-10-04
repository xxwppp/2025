# 当前脚本来自于http://script.345yun.cn脚本库下载！
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
 作者:  3iXi
 日期:  2025/7/10
 小程序:  三福会员中心
 功能:  签到、查询福币、获取账号信息
 变量:  sf_wxid_data (微信id) 多个账号用换行分割 
        PROXY_API_URL (代理api，返回一条txt文本，内容为代理ip:端口)
 定时:  一天一次
 cron:  0 8 * * *
 更新日志：
 2025/7/10  V1.0 初始化脚本
 2025/7/7   V1.1 使用wex_get模块统一微信授权接口
"""

import time
import json
import os
import requests
from typing import Optional

try:
    import httpx
except ImportError:
    print("错误: 需要安装 httpx[http2] 依赖")
    exit(1)

# 导入wex_get模块中的wx_code_auth方法
from wex_get import wx_code_auth

# 环境变量配置
MULTI_ACCOUNT_SPLIT = ["\n", "@","&"] # 分隔符列表
NOTIFY = False # 是否推送日志，默认不推送，True则推送


class SanfuSignin:
    """三福小程序签到类"""

    def __init__(self):
        """初始化签到客户端"""
        self.base_url = "https://crm.sanfu.com"
        self.app_id = "wxfe13a2a5df88b058"
        self.wx_appid = "wxfe13a2a5df88b058" # 微信小程序id

        self.client = httpx.Client(http2=True, timeout=30.0, verify=False)

        self.headers = {
            "host": "crm.sanfu.com",
            "connection": "keep-alive",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B)",
            "content-type": "application/json",
            "accept": "*/*",
            "referer": "https://servicewechat.com/wxfe13a2a5df88b058/333/page-frame.html",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "zh-CN,zh;q=0.9"
        }

        self.sid = None

    def check_env(self):
        """
        检查环境变量
        :return: 环境变量字符串
        """
        try:
            # 从环境变量获取微信ID
            soy_wxid_data = os.getenv("sf_wxid_data")
            if not soy_wxid_data:
                print("[检查环境变量] 没有找到环境变量sf_wxid_data，请检查环境变量")
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
            print(f"[检查环境变量] 发生错误: {str(e)}")
            raise


    def login(self, code: str) -> bool:
        """
        用户登录

        Args:
            code (str): 微信小程序登录code

        Returns:
            bool: 登录是否成功
        """
        payload = {
            "code": code,
            "appid": self.app_id,
            "shoId": "",
            "userId": "",
            "sourceWxsceneid": 1145,
            "sourceUrl": "pages/ucenter_index/ucenter_index"
        }

        url = f"{self.base_url}/ms-sanfu-wechat-customer-core/customer/core/wxMiniAppLogin"

        try:
            response = self.client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()

            data = response.json()
            if data.get("code") == 200 and data.get("success"):
                sid = data.get("data", {}).get("sid")
                if sid:
                    self.sid = sid
                    print("登录成功")
                    return True
                else:
                    print("登录失败：未获取到sid")
                    return False
            else:
                print(f"登录失败：{data.get('msg', '未知错误')}")
                return False

        except Exception as e:
            print(f"登录请求失败: {e}")
            return False

    def check_signin_status(self) -> Optional[bool]:
        """
        检查签到状态

        Returns:
            Optional[bool]: True=已签到, False=未签到, None=检查失败
        """
        if not self.sid:
            print("未获取到sid，无法检查签到状态")
            return None

        url = f"{self.base_url}/ms-sanfu-wechat-customer/customer/index/equity?sid={self.sid}"

        try:
            response = self.client.get(url, headers=self.headers)
            response.raise_for_status()

            data = response.json()
            if data.get('code') == 200:
                sign_in = data.get('data', {}).get('signIn', 1)
                is_signed = sign_in == 1
                print(f"签到状态: {'已签到' if is_signed else '未签到'}")
                return is_signed
            else:
                print(f"检查签到状态失败：{data.get('msg', '未知错误')}")
                return None

        except Exception as e:
            print(f"检查签到状态请求失败: {e}")
            return None

    def submit_signin(self) -> Optional[dict]:
        """
        提交签到

        Returns:
            Optional[dict]: 签到结果数据，None表示签到失败
        """
        if not self.sid:
            print("未获取到sid，无法签到")
            return None

        payload = {
            "sid": self.sid,
            "signWay": 0
        }

        url = f"{self.base_url}/ms-sanfu-wechat-common/customer/onSign"

        try:
            response = self.client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()

            data = response.json()
            if data.get('code') == 200:
                return data.get('data', {})
            else:
                print(f"签到失败：{data.get('msg', '未知错误')}")
                return None

        except Exception as e:
            print(f"签到请求失败: {e}")
            return None

    def get_account_info(self) -> Optional[dict]:
        """
        获取账号基本信息

        Returns:
            Optional[dict]: 账号信息，None表示获取失败
        """
        if not self.sid:
            print("未获取到sid，无法获取账号信息")
            return None

        url = f"{self.base_url}/ms-sanfu-wechat-customer/customer/index/baseInfo?sid={self.sid}"

        try:
            response = self.client.get(url, headers=self.headers)
            response.raise_for_status()

            data = response.json()
            if data.get('code') == 200:
                return data.get('data', {})
            else:
                print(f"获取账号信息失败：{data.get('msg', '未知错误')}")
                return None

        except Exception as e:
            print(f"获取账号信息请求失败: {e}")
            return None

    def process_account(self, wx_id: str) -> bool:
        """
        处理单个账号的签到流程

        Args:
            wx_id (str): 微信ID

        Returns:
            bool: 是否处理成功
        """
        print(f"\n开始处理账号: {wx_id}")

        # 1. 获取微信code
        code = wx_code_auth(wx_id, self.wx_appid)
        if not code:
            print(f"账号 {wx_id} 获取code失败")
            return False

        # 2. 登录
        if not self.login(code):
            print(f"账号 {wx_id} 登录失败")
            return False

        # 3. 检查签到状态
        sign_status = self.check_signin_status()
        if sign_status is None:
            print(f"账号 {wx_id} 检查签到状态失败")
            return False

        if sign_status:
            print("今日已签到")
        else:
            # 4. 提交签到
            sign_result = self.submit_signin()
            if sign_result is None:
                print(f"账号 {wx_id} 签到失败")
                return False

            # 5. 处理签到结果
            onSign_fubi = sign_result.get('fubi', 0)
            onKeepSignDay = sign_result.get('onKeepSignDay', 0)
            giftMoneyDaily = sign_result.get('giftMoneyDaily', 0)

            print(f"签到成功，获得{onSign_fubi}个福币，连续签到{onKeepSignDay}天")
            if giftMoneyDaily > 0:
                print(f"再签{giftMoneyDaily}天可得神秘礼物🎁")

        # 6. 获取账号信息
        account_info = self.get_account_info()
        if account_info:
            curCusId = account_info.get('curCusId', '未知ID')
            baseInfo_fubi = account_info.get('fubi', 0)
            print(f"账号ID: {curCusId}，当前有{baseInfo_fubi}个福币")

        return True

    def close(self):
        """关闭HTTP客户端"""
        self.client.close()


def main():
    """主函数"""
    try:
        print("正在初始化三福签到脚本...")
        
        signin = SanfuSignin()

        try:
            # 检查环境变量
            wx_ids = list(signin.check_env())
            if not wx_ids:
                print("未获取到任何账号信息")
                return

            print(f"获取到 {len(wx_ids)} 个账号")

            for i, wx_id in enumerate(wx_ids, 1):
                print(f"\n{'='*50}")
                print(f"处理第 {i}/{len(wx_ids)} 个账号")
                print(f"{'='*50}")

                try:
                    signin.process_account(wx_id)
                except Exception as e:
                    print(f"处理账号 {wx_id} 时发生错误: {e}")

                if i < len(wx_ids):
                    print(f"等待2秒后处理下一个账号...")
                    time.sleep(2)

        finally:
            signin.close()

        print("\n所有账号处理完成")

    except Exception as e:
        print(f"脚本执行失败: {e}")


if __name__ == "__main__":
    main()
# 当前脚本来自于http://script.345yun.cn脚本库下载！