# 当前脚本来自于http://script.345yun.cn脚本库下载！
"""
 作者:  临渊
 日期:  2025/7/10
 小程序:    银鱼质亨
 功能:  视频、提现
 变量:  yyzx_wxid_data (微信id) 多个账号用换行分割 
 定时:  一天两次
 cron:  10 8,9 * * *
 更新日志：
 2025/7/10 V1.0 适配协议核心插件格式
 2025/7/7  V1.1 使用wex_get模块统一微信授权接口
"""

MULTI_ACCOUNT_SPLIT = ["\n", "@", "&"]  # 分隔符列表

import requests
import time
import random
import json
import base64
import os
# 导入wex_get模块中的wx_code_auth方法
from wex_get import wx_code_auth
# 禁用所有代理环境变量
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)
os.environ.pop('no_proxy', None)
# 配置参数
CONFIG = {
    'only_withdraw': False,   # True=只提现, False=先刷视频再提现
    'delay': 1.5,             # 视频间隔秒
    'account_delay': 2,       # 账号间隔秒
    'watch_duration': 80,     # 模拟观看时长(秒)
    'base_version': "3.8.9"
}

# API
BASE_URL = "https://n05.sentezhenxuan.com"
VIDEO_LIST_API = f"{BASE_URL}/api/video/list?page=1&limit=10&status=1&source=0&isXn=1"
VIDEO_JOB_API = f"{BASE_URL}/api/video/videoJob"
WITHDRAW_API = f"{BASE_URL}/api/userTx"

# ===================== 微信小程序code获取（使用wex_get模块） =====================
def get_code_from_plugin(wxid, appid):
    """
    通过wex_get模块获取小程序code
    Args:
        wxid (str): 微信ID
        appid (str): 小程序的appid
    Returns:
        dict: {success, extracted_code, data, error}
    """
    try:
        code = wx_code_auth(wxid, appid)
        if code:
            return {"success": True, "extracted_code": code, "data": {"code": code}}
        else:
            return {"success": False, "error": "获取code失败"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ===================== 多账号环境变量读取 =====================
def get_env_accounts():
    """
    从环境变量yyzx_wxid_data读取账号列表，支持多账号分隔
    支持格式：wxid
    """
    soy_wxid_data = os.getenv("yyzx_wxid_data")
    if not soy_wxid_data:
        print("❌ 没有找到环境变量yyzx_wxid_data，请检查环境变量")
        return []
    # 自动检测分隔符
    split_char = None
    for sep in MULTI_ACCOUNT_SPLIT:
        if sep in soy_wxid_data:
            split_char = sep
            break
    if not split_char:
        soy_wxid_datas = [soy_wxid_data]
    else:
        soy_wxid_datas = soy_wxid_data.split(split_char)
    accounts = []
    for line in soy_wxid_datas:
        line = line.strip()
        if not line:
            continue
        accounts.append(line)
    return accounts

# ===================== 微信小程序code获取 =====================

WXAPP_LOGIN_ENDPOINT = "/Wxapp/JSLogin"

# 直接集成get_wxapp_code

def get_wxapp_code(wxid, appid, WXAPI_BASE_URL, data=None):
    """
    获取小程序code
    Args:
        wxid (str): 微信ID
        appid (str): 小程序的appid
        WXAPI_BASE_URL (str): 微信API基础URL
        data (str): 可选的Data参数，默认为示例值
    Returns:
        dict: 请求结果，包含success字段和提取的code
    """
    try:
        url = f"{WXAPI_BASE_URL}{WXAPP_LOGIN_ENDPOINT}"
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        if not data:
            data = "eyJ3aXRoX2NyZWRlbnRpYWxzIjp0cnVlLCJkYXRhIjp7ImxhbmciOiJlbiJ9LCJhcGlfbmFtZSI6IndlYmFwaV9nZXR1c2VyaW5mbyIsImZyb21fY29tcG9uZW50Ijp0cnVlfQ=="
        payload = {
            "Wxid": wxid,
            "Appid": appid,
            "Data": data,
            "Opt": 1
        }
        response = requests.post(url, headers=headers, json=payload, timeout=30, proxies={"http": None, "https": None})
        if response.status_code == 200:
            try:
                result = response.json()
                if 'Data' in result and 'code' in result['Data']:
                    extracted_code = result['Data']['code']
                    return {
                        'success': True,
                        'data': result,
                        'extracted_code': extracted_code
                    }
                else:
                    return {
                        'success': True,
                        'data': result,
                        'extracted_code': None
                    }
            except json.JSONDecodeError:
                return {
                    'success': True,
                    'data': response.text,
                    'extracted_code': None
                }
        else:
            return {
                'success': False,
                'error': f'HTTP错误: {response.status_code}',
                'response_text': response.text
            }
    except Exception as e:
        return {
            'success': False,
            'error': f'请求异常: {str(e)}'
        }

def get_accounts(accounts_raw):
    """从本地变量获取账号列表"""
    decoded = accounts_raw.strip()
    accounts = []
    for line in decoded.splitlines():
        if '#' in line:
            remark, auth = line.split('#', 1)
            accounts.append({'remark': remark.strip(), 'auth': auth.strip()})
    return accounts

def get_base_headers(auth):
    return {
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate, br",
        "Content-Type": "application/json",
        "Connection": "keep-alive",
        "Referer": "https://servicewechat.com/wx5b82dfe3747e533f/5/page-frame.html",
        "Host": "n05.sentezhenxuan.com",
        "Authori-zation": auth,
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.50 NetType/WIFI Language/zh_CN",
        "Cb-lang": "zh-CN",
        "Form-type": "routine-zhixiang",
        "xweb_xhr": "1"
    }

def get_withdraw_headers(auth):
    return {
        "Accept": "application/json",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Referer": "https://servicewechat.com/wx5b82dfe3747e533f/5/page-frame.html",
        "Host": "n05.sentezhenxuan.com",
        "Authori-zation": auth,
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.50(0x1800323d) NetType/WIFI Language/zh_CN",
        "Cb-lang": "zh-CN",
        "Form-type": "routine-zhixiang",
        "xweb_xhr": "1"
    }

def safe_json_parse(text):
    try:
        return json.loads(text)
    except Exception:
        return None

def get_video_ids(auth, account_name):
    headers = get_base_headers(auth)
    try:
        resp = requests.get(VIDEO_LIST_API, headers=headers, timeout=15, proxies={"http": None, "https": None})
        data = safe_json_parse(resp.text)
        if not data or data.get('status') != 200 or not isinstance(data.get('data'), list):
            print(f"⚠️ {account_name} 获取视频列表失败: {data.get('msg', '未知错误') if data else '无返回'}")
            return []
        return [item['id'] for item in data['data'] if isinstance(item.get('id'), int)]
    except Exception as e:
        print(f"⚠️ {account_name} 获取视频列表异常: {e}")
        return []

def watch_videos(video_ids, auth, account_name):
    total = len(video_ids)
    for i, vid in enumerate(video_ids):
        now = int(time.time() * 1000)
        body = json.dumps({
            "vid": vid,
            "startTime": now - CONFIG['watch_duration'] * 1000,
            "endTime": now,
            "baseVersion": CONFIG['base_version'],
            "playMode": 0
        })
        headers = get_base_headers(auth)
        try:
            resp = requests.post(VIDEO_JOB_API, headers=headers, data=body, timeout=15, proxies={"http": None, "https": None})
            data = safe_json_parse(resp.text)
            if data and data.get('status') == 200:
                print(f"🎥 {account_name} 视频 {i+1}/{total} 刷完 (ID: {vid})")
            else:
                print(f"⚠️ {account_name} 视频 {i+1}/{total} 返回异常: {data.get('msg', '无返回数据') if data else '无返回'}")
        except Exception as e:
            print(f"⚠️ {account_name} 视频 {i+1}/{total} 请求失败: {e}")
        if i < total - 1:
            time.sleep(CONFIG['delay'])

def do_withdraw(auth, account_name):
    headers = get_withdraw_headers(auth)
    try:
        resp = requests.get(WITHDRAW_API, headers=headers, timeout=15, proxies={"http": None, "https": None})
        data = safe_json_parse(resp.text)
        if not data:
            print(f"❌ {account_name} 提现无效响应")
            return False, '无效响应'
        if data.get('code') == 200 or data.get('status') == 200:
            print(f"💰 {account_name} 提现成功: {data.get('msg', '成功')}")
            return True, data.get('msg', '成功')
        elif data.get('msg') and '每天只可提现1次' in data.get('msg'):
            print(f"💰 {account_name} 今日已提现过")
            return False, data.get('msg')
        else:
            print(f"❌ {account_name} 提现失败: {data.get('msg', '未知错误')}")
            return False, data.get('msg', '未知错误')
    except Exception as e:
        print(f"❌ {account_name} 提现异常: {e}")
        return False, str(e)

def main():
    wxidlist = get_env_accounts()
    if not wxidlist:
        print('❌ 未配置账号，请设置环境变量yyzx_wxid_data')
        return
    appid = "wx5b82dfe3747e533f"
    accounts_raw_lines = []
    for wxid in wxidlist:
        code_result = get_code_from_plugin(wxid, appid)
        if not code_result.get('success') or not code_result.get('extracted_code'):
            print(f"❌ 获取code失败: {code_result.get('error')}")
            continue
        code = code_result['extracted_code']
        token = get_token_by_code(code)
        if not token:
            print(f"❌ 获取token失败")
            continue
        accounts_raw_lines.append(f"{wxid}#Bearer {token}")
        time.sleep(random.uniform(2, 4))
    accounts_raw = '\n'.join(accounts_raw_lines)
    accounts = get_accounts(accounts_raw)
    if not accounts:
        print('❌ 未配置账号，请在yyzx_wxid_data环境变量中配置账号')
        return
    print(f"\n🎉 共找到 {len(accounts)} 个账号")
    stats = {
        'total': len(accounts),
        'success_withdraw': 0,
        'already_withdraw': 0,
        'failed_withdraw': 0,
        'watched_videos': 0
    }
    for idx, acc in enumerate(accounts):
        account_name = acc['remark'] or f"账号{idx+1}"
        auth = acc['auth']
        print(f"\n📌 ━━━━━━ 开始处理 {account_name} ━━━━━━")
        try:
            if CONFIG['only_withdraw']:
                print('ℹ️ 只提现模式已启用，跳过刷视频步骤')
                ok, msg = do_withdraw(auth, account_name)
                if ok:
                    stats['success_withdraw'] += 1
                elif '提现' in msg:
                    stats['already_withdraw'] += 1
                else:
                    stats['failed_withdraw'] += 1
            else:
                video_ids = get_video_ids(auth, account_name)
                if video_ids:
                    print(f"📽️ 获取到 {len(video_ids)} 个视频ID，准备刷视频...")
                    watch_videos(video_ids, auth, account_name)
                    stats['watched_videos'] += len(video_ids)
                else:
                    print('⚠️ 无视频可刷，跳过刷视频步骤')
                ok, msg = do_withdraw(auth, account_name)
                if ok:
                    stats['success_withdraw'] += 1
                elif '提现' in msg:
                    stats['already_withdraw'] += 1
                else:
                    stats['failed_withdraw'] += 1
        except Exception as e:
            print(f"❌ {account_name} 处理异常: {e}")
            stats['failed_withdraw'] += 1
        if idx < len(accounts) - 1:
            time.sleep(CONFIG['account_delay'])
    # 统计报告
    report = [
        '✅ 所有账号处理完成',
        f"📊 统计报告:",
        f"├─ 总账号数: {stats['total']}",
        f"├─ 成功提现: {stats['success_withdraw']}",
        f"├─ 今日已提现: {stats['already_withdraw']}",
        f"├─ 提现失败: {stats['failed_withdraw']}",
        f"└─ 刷视频数: {stats['watched_videos']}"
    ]
    print('\n' + '\n'.join(report))

def get_token_by_code(code):
    """根据code获取token值"""
    url = f"https://n05.sentezhenxuan.com/api/v2/routine/silenceAuth?code={code}&spread_spid=0&spread_code=0"
    headers = {
        "xweb_xhr": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090c33)XWEB/13639",
        "form-type": "routine-zhixiang",
        "content-type": "application/json",
        "accept": "*/*",
        "sec-fetch-site": "cross-site",
        "sec-fetch-mode": "cors",
        "sec-fetch-dest": "empty",
        "referer": "https://servicewechat.com/wx5b82dfe3747e533f/7/page-frame.html",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh-CN,zh;q=0.9",
        "priority": "u=1, i"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15, proxies={"http": None, "https": None})
        data = resp.json()
        if data.get('status') == 200 and 'data' in data and 'token' in data['data']:
            token = data['data']['token']
            # print(f"获取到的token: {token}")
            return token
        else:
            print(f"未能获取到token，返回内容: {data}")
            return None
    except Exception as e:
        print(f"请求token异常: {e}")
        return None

def batch_generate_accounts(wxidlist, WXAPI_BASE_URL, appid="wx5b82dfe3747e533f"):
    """批量获取code和token，生成accounts_raw内容"""
    lines = []
    for wxid in wxidlist:
        # print(f"\n处理wxid: {wxid}")
        code_result = get_wxapp_code(wxid, appid, WXAPI_BASE_URL)
        if not code_result.get('success') or not code_result.get('extracted_code'):
            print(f"❌ 获取code失败: {code_result.get('error')}")
            continue
        code = code_result['extracted_code']
        token = get_token_by_code(code)
        if not token:
            print(f"❌ 获取token失败")
            continue
        lines.append(f"{wxid}#Bearer {token}")
        time.sleep(random.uniform(2, 4))
    result = '\n'.join(lines)
    # print("\n生成的accounts_raw内容：\n" + result)
    return result

if __name__ == '__main__':
    main()
        

# 当前脚本来自于http://script.345yun.cn脚本库下载！