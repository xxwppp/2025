# 统一梦时代小程序——活动——茄皇的家
#环境变量名：TYQH
#变量值：抓wid值(可搜索 "wid": 或登录时抓login接口)
#多账户用&分割
#注：第一次需要手动领取种子种植，领过没法抓包了，后续再完善吧

#原作者：妖火 重庆第一深情

#Vorto：改了引导的领取种子请求，判断用户状态是否初次引导

import requests
import json
import os
import time
from notify import send

# 从环境变量获取多用户信息，用@分割
users = os.getenv("TYQH", "").split("&")
# 过滤空用户（处理环境变量为空或分割后产生的空字符串）
users = [user.strip() for user in users if user.strip()]

user_agent = "Mozilla/5.0 (Linux; Android 15; PKG110 Build/UKQ1.231108.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/138.0.7204.180 Mobile Safari/537.36 XWEB/1380215 MMWEBSDK/20250904 MMWEBID/6169 MicroMessenger/8.0.64.2940(0x28004033) WeChat/arm64 Weixin NetType/WIFI Language/zh_CN ABI/arm64 miniProgram/wx532ecb3bdaaf92f9"

def login(wid, user_logs):
    """登录并获取授权token及用户数据"""
    step = "登录"
    try:
        url = "https://api.zhumanito.cn/api/login"
        payload = {"wid": wid}
        headers = {
            'User-Agent': user_agent,
            'Content-Type': "application/json"
        }
        
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        response.raise_for_status()  # 检查请求是否成功
        dljson = response.json()
        
        # 检查返回数据是否包含token和用户数据
        if 'data' in dljson and 'token' in dljson['data'] and 'user' in dljson['data']:
            msg = "登录成功 ✅"
            print(msg)
            user_logs.append(f"🔑 {step}: {msg}")
            # 返回token和用户数据
            return {
                "token": dljson['data']['token'],
                "user_data": dljson['data']['user']
            }
        else:
            msg = f"登录失败，返回数据: {dljson} ❌"
            print(msg)
            user_logs.append(f"🔑 {step}: {msg}")
            return None
    except Exception as e:
        msg = f"登录出错: {str(e)} ❌"
        print(msg)
        user_logs.append(f"🔑 {step}: {msg}")
        return None

def get_seeds(authorization, user_logs):
    """领取种子"""
    step = "领取种子"
    if not authorization:
        msg = "未获取到授权，无法领取种子 🔒"
        print(msg)
        user_logs.append(f"🌱 {step}: {msg}")
        return
    
    try:
        url = "https://api.zhumanito.cn/api/guide"
        payload = {"status": 1}
        headers = {
            'User-Agent': user_agent,
            'Content-Type': "application/json",
            'authorization': authorization
        }
        
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        response.raise_for_status()

        payload = {"status": 2}
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        response.raise_for_status()

        msg = f"领取种子结果: {response.text} 📦"
        print(msg)
    except Exception as e:
        msg = f"领取种子出错: {str(e)} ❌"
        print(msg)
        user_logs.append(f"🌱 {step}: {msg}")

def check_in(authorization, user_logs):
    """签到"""
    step = "签到"
    if not authorization:
        msg = "未获取到授权，无法签到 🔒"
        print(msg)
        user_logs.append(f"📅 {step}: {msg}")
        return
    
    try:
        url = "https://api.zhumanito.cn/api/task/complete"
        headers = {
            'User-Agent': user_agent,
            'Content-Type': "application/x-www-form-urlencoded",
            'authorization': authorization
        }
        
        response = requests.post(url, headers=headers)
        response_data = response.json()
        if response_data.get("msg") == "成功":
            msg = "签到成功 ✅"
            print(f"签到结果: {msg}")
            user_logs.append(f"📅 {step}: {msg}")
        else:
            msg = f"失败，原因: {response_data.get('msg', '未知错误')} ❌"
            print(f"签到结果: {msg}")
            user_logs.append(f"📅 {step}: {msg}")
    except Exception as e:
        msg = f"签到出错: {str(e)} ❌"
        print(msg)
        user_logs.append(f"📅 {step}: {msg}")

def explore(authorization, wid, user_logs):
    """浏览任务"""
    step = "浏览任务"
    if not authorization:
        msg = "未获取到授权，无法执行浏览任务 🔒"
        print(msg)
        user_logs.append(f"🔍 {step}: {msg}")
        return
    
    try:
        # 浏览任务URL，正确格式化wid参数
        url = f"https://api.zhumanito.cn/?wid={wid}"
        
        # 使用统一的headers并添加authorization
        headers = {
            'Host': 'api.zhumanito.cn',
            'User-Agent': user_agent,
            'authorization': authorization
        }
        
        response = requests.get(url, headers=headers, verify=True, allow_redirects=True)
        if response.status_code == 200:
            msg = "浏览完成 ✅"
            print(f"浏览任务：{msg}")
            user_logs.append(f"🔍 {step}: {msg}")
        else:
            msg = f"失败，状态码: {response.status_code}, 内容: {response.text} ❌"
            print(f"浏览任务：{msg}")
            user_logs.append(f"🔍 {step}: {msg}")
        
    except requests.exceptions.RequestException as e:
        msg = f"浏览任务出错: {e} ❌"
        print(msg)
        user_logs.append(f"🔍 {step}: {msg}")

def loop_watering(headers, account_idx, account, user_logs):
    """循环浇水（资源≥20时执行）"""
    step = "循环浇水"
    user_logs.append(f"🔄 {step}：进入循环浇水（需💧≥20且☀️≥20）")
    print(f"\n🔄 账号{account_idx}：进入循环浇水（需💧≥20且☀️≥20）")
    
    while True:
        water = account["user_data"].get("water_num", 0)
        sun = account["user_data"].get("sun_num", 0)
        
        if water >= 20 and sun >= 20:
            log_msg = f"📌 账号{account_idx}：资源满足（💧{water}，☀️{sun}），浇水..."
            print(log_msg)
            user_logs.append(log_msg)
            
            try:
                water_headers = headers.copy()
                water_headers["Content-Type"] = "application/x-www-form-urlencoded;charset=utf-8"
                res = requests.post(
                    "https://api.zhumanito.cn/api/water",
                    headers=water_headers,
                    data=b"",
                    timeout=(25, 30)
                ).json()
                
                if res["code"] != 200:
                    raise Exception(res.get("msg", "浇水失败"))
                
                # 更新用户数据
                account["user_data"] = res["data"]["user"]
                land = res["data"].get("land", [])
                
                success_msg = f"✅ 账号{account_idx}：浇水成功！"
                status_msg = f"📊 剩余：💧{account['user_data']['water_num']}，☀️{account['user_data']['sun_num']}"
                print("="*35)
                print(success_msg)
                print(status_msg)
                user_logs.append(success_msg)
                user_logs.append(status_msg)
                
                if land:
                    land_msg = f"🌱 土地：共{len(land)}块，阶段{land[0]['seed_stage']} 🌱"
                    print(land_msg)
                    user_logs.append(land_msg)
                print("="*35)
                
                time.sleep(2)  # 间隔2秒避免请求过于频繁
                
            except Exception as e:
                error_msg = f"⚠️ 账号{account_idx}：浇水失败：{str(e)} ❌"
                print(error_msg)
                user_logs.append(f"❌ {step}：{error_msg}")
                break
        else:
            end_msg = f"🔚 账号{account_idx}：资源不足（💧{water}，☀️{sun}），停止浇水 ⏹️"
            print(end_msg)
            user_logs.append(f"ℹ️ {step}：{end_msg}")
            break

def process_user(wid, user_index):
    """处理单个用户的所有操作"""
    # 为当前用户创建日志列表
    user_logs = [f"👤 用户{user_index}: {wid[:10]}..."]
    
    print(f"\n===== 开始处理用户 {user_index} (wid: {wid[:10]}...) =====")
    
    # 执行流程：登录 -> 领种子 -> 签到 -> 浏览 -> 循环浇水
    login_data = login(wid, user_logs)
    if login_data:
        auth_token = login_data["token"]
        # 构建请求头
        headers = {
            'User-Agent': user_agent,
            'authorization': auth_token
        }
        # 构建账号数据对象
        account = {
            "user_data": login_data["user_data"]
        }
        if login_data["user_data"]["new_status"] != 2:
            get_seeds(auth_token, user_logs) 
        check_in(auth_token, user_logs)
        explore(auth_token, wid, user_logs)
        loop_watering(headers, user_index, account, user_logs)
    else:
        msg = "获取授权失败，无法执行后续操作 🔒"
        print(msg)
        user_logs.append(f"⚠️ {msg}")
    
    print(f"===== 完成处理用户 {user_index} =====\n")
    return user_logs

if __name__ == "__main__":
    if not users or len(users) == 0:
        print("未从环境变量TYQH中获取到任何用户信息！ 🚫")
        send("统一茄皇", "未从环境变量TYQH中获取到任何用户信息！ 🚫")
    else:
        print(f"共检测到 {len(users)} 个用户，开始依次处理... 👥")
        
        # 记录所有用户的详细日志
        all_logs = []
        
        # 遍历处理每个用户
        for i, user_wid in enumerate(users, 1):
            try:
                user_logs = process_user(user_wid, i)
                all_logs.extend(user_logs)
                all_logs.append("")  # 添加空行分隔不同用户
            except Exception as e:
                error_msg = f"用户 {i} 处理过程中发生未捕获错误: {str(e)} ❌"
                print(error_msg)
                all_logs.append(f"❌ {error_msg}")
                all_logs.append("")
        
        # 发送包含所有步骤结果的汇总通知
        send("统一茄皇", "\n".join(all_logs))
