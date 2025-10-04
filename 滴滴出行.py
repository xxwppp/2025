# 当前脚本来自于http://script.345yun.cn脚本库下载！
# -*- coding=UTF-8 -*-
# @Project          QL_TimingScript
# @fileName         滴滴出行.py
# @author           Echo
# @EditTime         2024/11/27
# const $ = new Env('滴滴出行')
# cron: "0 8,14,17 * * *"
"""
 作者:  Echo
 日期:  2024/11/27
 小程序:  滴滴出行
 功能:  签到、瓜分福利金、领取优惠券、每日精选等
 变量:  dd_wxid_data (微信id) 多个账号用换行分割 
        PROXY_API_URL (代理api，返回一条txt文本，内容为代理ip:端口)
 定时:  一天三次
 cron:  0 8,14,17 * * *
 更新日志：
 2024/11/27  V1.0 初始化脚本
 2025/7/7   V1.1 使用wex_get模块统一微信授权接口
"""
import os
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)
os.environ.pop('no_proxy', None)
import asyncio
import datetime
import httpx
import requests
import json
from urllib.parse import quote, urlencode
# 导入wex_get模块中的wx_code_auth方法
from wex_get import wx_code_auth

# from fn_print import fn_print
# from get_env import get_env
# from sendNotify import send_notification_message_collection

MONTH_SIGNAL = False  # 月月领券

# dd_tokens = get_env("DD_TOKENS", "&")


class DiDi:
    LAT = "30.707130422009786"  # 纬度
    LNG = "104.09652654810503"  # 经度
    CITY_ID = 17  # 城市id

    def __init__(self, token, city_id=CITY_ID, lat=LAT, lng=LNG):
        self.user_phone = None
        self.client = httpx.AsyncClient(verify=False)
        self.token = token
        self.city_id = city_id
        self.lat = lat
        self.lng = lng
        self.today = datetime.datetime.now().strftime("%Y-%m-%d")
        self.tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        self.activity_id_today = 0
        self.task_id_today = 0
        self.status_today = 0
        self.activity_id_tomorrow = 0
        self.status_tomorrow = 0
        self.count_tomorrow = 0

    async def aclose(self):
        await self.client.aclose()

    async def get_user_info(self):
        """
        获取用户信息
        :return: 
        """
        get_user_info_response = await self.client.get(
            url=f"https://common.diditaxi.com.cn/passenger/getprofile?token={self.token}"
        )
        get_user_info_data = get_user_info_response.json()
        self.user_phone = get_user_info_data.get("phone")

    async def get_welfare_payments(self):
        """
        获取福利金
        :return: 
        """
        get_weibo_payments_response = await self.client.get(
            url="https://rewards.xiaojukeji.com/loyalty_credit/bonus/getWelfareUsage4Wallet",
            params={
                "token": self.token,
                "city_id": self.city_id
            }
        )
        if get_weibo_payments_response.status_code == 200:
            get_info_data = get_weibo_payments_response.json()
            if "token error" in get_info_data.get("errmsg") and get_info_data.get("errno") == 20001:
                print("token已过期，请重新获取token")
                print(
                    "滴滴出行通知 - {}".format(datetime.datetime.now().strftime("%Y/%m/%d")))
                exit()
            return get_info_data['data']['balance']
        else:
            print(f"===获取用户福利金请求异常, {get_weibo_payments_response.text}===")

    async def sign_in(self):
        """
        签到
        :return: 
        """
        sign_in_response = await self.client.post(
            url="https://ut.xiaojukeji.com/ut/welfare/api/action/dailySign",
            json={
                "token": self.token,
                "lat": self.lat,
                "lng": self.lng,
                "platform": "na",
                "env": '{}'
            }
        )
        if sign_in_response.status_code == 200:
            sign_in_data = sign_in_response.json()
            print(sign_in_data)
            if sign_in_data["errno"] == 0:
                subsidy_amount = sign_in_data["data"]["subsidy_state"]["subsidy_amount"]
                print(f"用户【{0}】, ===今日签到成功，获得{subsidy_amount}福利金🪙🪙🪙===")
                return
            elif sign_in_data["errno"] == 40009:
                print(f"用户【{0}】, ===今日福利金已签到，无需重复签到！===")
                return
            else:
                print(f"用户【{0}】, ===签到失败, {sign_in_data}===")
        else:
            print(f"===签到请求异常, {sign_in_response}===")

    async def get_carve_up_action_id(self):
        """
        获取瓜分活动的ID
        :return: 
        """
        get_carve_up_action_id_response = await self.client.post(
            url="https://ut.xiaojukeji.com/ut/welfare/api/home/init/v2",
            json={
                "token": self.token,
                "lat": self.lat,
                "lng": self.lng,
                "platform": "na",
                "env": '{}'
            }
        )
        if get_carve_up_action_id_response.status_code == 200:
            get_carve_up_action_id_data = get_carve_up_action_id_response.json()
            if get_carve_up_action_id_data.get("errno") == 0:
                data = get_carve_up_action_id_data.get("data")
                if not data:
                    print(f"【瓜分活动】接口返回异常，无data字段，原始返回: {get_carve_up_action_id_data}")
                    return False
                divide_data_all = data.get("divide_data")
                if not divide_data_all:
                    print(f"【瓜分活动】接口返回异常，无divide_data字段，原始返回: {get_carve_up_action_id_data}")
                    return False
                divide_data = divide_data_all.get("divide")
                if not divide_data:
                    print(f"【瓜分活动】接口返回异常，无divide字段，原始返回: {get_carve_up_action_id_data}")
                    return False
                today_data = divide_data.get(self.today)
                if not today_data:
                    print(f"【瓜分活动】接口返回异常，无今日数据，原始返回: {get_carve_up_action_id_data}")
                    return False
                self.activity_id_today, self.task_id_today, self.status_today = today_data["activity_id"], today_data[
                    "task_id"], today_data["status"]
                tomorrow_data = divide_data.get(self.tomorrow)
                if not tomorrow_data:
                    print(f"【瓜分活动】接口返回异常，无明日数据，原始返回: {get_carve_up_action_id_data}")
                    return False
                self.activity_id_tomorrow, self.status_tomorrow, self.count_tomorrow = tomorrow_data["activity_id"], \
                    tomorrow_data["status"], tomorrow_data["button"]["count"]
                return True
        else:
            print(f"===获取瓜分活动ID请求异常, {get_carve_up_action_id_response.text}===")
        return False

    async def apply_carve_up_action(self):
        """
        报名明天的瓜分福利金
        :return: 
        """
        apply_carve_up_action_response = await self.client.post(
            url="https://ut.xiaojukeji.com/ut/welfare/api/action/joinDivide",
            json={
                "token": self.token,
                "lat": self.lat,
                "lng": self.lng,
                "platform": "na",
                "env": '{}',
                "activity_id": self.activity_id_tomorrow,
                "count": self.count_tomorrow,
                "type": "ut_bonus"
            }
        )
        if apply_carve_up_action_response.status_code == 200:
            apply_carve_up_action_data = apply_carve_up_action_response.json()
            if apply_carve_up_action_data.get("errno") == 0:
                if apply_carve_up_action_data.get("data", {}).get("result"):
                    print(f"用户【{self.user_phone}】, ===报名明日瓜分福利金成功🎉===")
                    return
            elif apply_carve_up_action_data.get("errno") == 1003:
                print(f"用户【{self.user_phone}】, ===今日瓜分福利金已报名，无需重复报名！===")
                return
            else:
                print(f"用户【{self.user_phone}】, ===报名明日瓜分福利金失败, {apply_carve_up_action_data}===")
                return
        else:
            print(f"===报名明日瓜分福利金请求异常, {apply_carve_up_action_response.text}===")

    async def complete_carve_up_action(self):
        """
        完成今天的瓜分福利金，14点前完成
        :return: 
        """
        complete_carve_up_action_response = await self.client.post(
            url="https://ut.xiaojukeji.com/ut/welfare/api/action/divideReward",
            json={
                "token": self.token,
                "lat": self.lat,
                "lng": self.lng,
                "platform": "na",
                "env": '{}',
                "activity_id": self.activity_id_today,
                "task_id": self.task_id_today
            }
        )
        if complete_carve_up_action_response.status_code == 200:
            complete_carve_up_action_data = complete_carve_up_action_response.json()
            if complete_carve_up_action_data.get("errno") == 0:
                if complete_carve_up_action_data.get("data", {}).get("result"):
                    print(f"用户【{self.user_phone}】, ===完成今日打卡瓜分福利金成功🎉===")
                    return
            elif complete_carve_up_action_data.get("errno") == 1003:
                print(f"用户【{self.user_phone}】, ===今日瓜分福利金已完成，无需重复完成！===")
                return
            else:
                print(f"用户【{self.user_phone}】, ===完成今日瓜分福利金失败, {complete_carve_up_action_data}===")
                return
        else:
            print(f"===完成今日瓜分福利金请求异常, {complete_carve_up_action_response.text}===")

    async def inquire_benefits_details(self):
        """
        查询权益详情
        :return: 
        """
        benefits_details_response = await self.client.get(
            url="https://member.xiaojukeji.com/dmember/h5/privilegeLists",
            params={
                "token": self.token,
                "city_id": self.city_id
            }
        )
        if benefits_details_response.status_code == 200:
            benefits_details_data = benefits_details_response.json()
            if benefits_details_data.get("errno") == 0:
                privileges_list = benefits_details_data.get('data', {}).get('privileges', [])  # 我的权益列表
                return privileges_list
        else:
            print(f"===查询权益详情请求异常, {benefits_details_response.text}===")

    async def receive_level_gift_week(self):
        """
        领取周周领券活动的优惠券
        :return: 
        """
        privileges_list = await self.inquire_benefits_details()
        for privilege in privileges_list:
            if privilege.get('name') not in ['周周领券'] or privilege.get('level_gift') is None:
                continue
            coupons_list = privilege.get('level_gift', {}).get('coupons', [])
            for coupon in coupons_list:
                status = coupon.get("status")  # 0: 未领取 1: 已使用 2: 未使用
                if status != 0:
                    continue
                batch_id = coupon.get("batch_id")
                print(f"用户【“{self.user_phone}】, ===开始领取{coupon.get('remark')}{coupon.get('coupon_title')}===")
                receive_level_gift_response = await self.client.get(
                    url=f"https://member.xiaojukeji.com/dmember/h5/receiveLevelGift?xbiz=&prod_key=wyc-vip-level&xpsid=&dchn=&xoid=&xenv=passenger&xspm_from=&xpsid_root=&xpsid_from=&xpsid_share=&token={self.token}&batch_id={batch_id}&env={{}}&gift_type=1&city_id={self.city_id}"
                )
                if receive_level_gift_response.status_code == 200:
                    receive_level_gift_data = receive_level_gift_response.json()
                    if receive_level_gift_data.get("errno") == 0:
                        print(f"用户【“{self.user_phone}】, ===领取成功🎉===")
                        continue
                    else:
                        print(f"用户【“{self.user_phone}】, ===领取失败, {receive_level_gift_data}===")
                else:
                    print(f"===领取周周领券请求异常, {receive_level_gift_response.text}===")

    async def receive_level_gift_month(self):
        """
        领取月月领券活动的优惠券
        :return: 
        """
        if not MONTH_SIGNAL:
            print(f"用户【“{self.user_phone}】, ===月月领券活动未开启===")
            return
        privileges_list = await self.inquire_benefits_details()
        for privilege in privileges_list:
            if privilege.get('name') not in ['月月领券'] or privilege.get('level_gift') is None:
                continue
            coupons_list = privilege.get('level_gift', {}).get('coupons', [])
            for coupon in coupons_list:
                status = coupon.get("status")  # 0: 未领取 1: 已使用 2: 未使用
                if status != 0:
                    continue
                batch_id = coupon.get("batch_id")
                print(f"用户【“{self.user_phone}】, ===开始领取{coupon.get('remark')}{coupon.get('coupon_title')}===")
                receive_level_gift_response = await self.client.get(
                    url=f"https://member.xiaojukeji.com/dmember/h5/receiveLevelGift?xbiz=&prod_key=wyc-vip-level&xpsid=&dchn=&xoid=&xenv=passenger&xspm_from=&xpsid_root=&xpsid_from=&xpsid_share=&token={self.token}&batch_id={batch_id}&env={{}}&gift_type=1&city_id={self.city_id}"
                )
                if receive_level_gift_response.status_code == 200:
                    receive_level_gift_data = receive_level_gift_response.json()
                    if receive_level_gift_data.get("errno") == 0:
                        print(f"用户【“{self.user_phone}】, ===领取成功🎉===")
                        continue
                    else:
                        print(f"用户【“{self.user_phone}】, ===领取失败, {receive_level_gift_data}===")
                else:
                    print(f"===领取月月领券请求异常, {receive_level_gift_response.text}===")

    async def swell_coupon(self):
        """
        膨胀周周领券活动的优惠券
        :return: 
        """
        privileges_list = await self.inquire_benefits_details()
        for privilege in privileges_list:
            if privilege.get("name") in ["周周领券", "月月领券"]:
                if privilege.get('level_gift') is None:
                    continue
                coupons_list = privilege.get('level_gift', {}).get('coupons', [])
                for coupon in coupons_list:
                    swell_status = coupon.get('swell_status')  # 0代表不能膨胀，1代表能膨胀,2代表已膨胀、
                    if swell_status == 1:
                        print(
                            f"用户【“{self.user_phone}】, ===开始膨胀{coupon.get('remark')}{coupon.get('coupon_title')}===")
                    batch_id = coupon.get("batch_id")
                    coupon_id = coupon.get("coupon_id")
                    swell_coupon_response = await self.client.post(
                        url=f"https://member.xiaojukeji.com/dmember/h5/swell_coupon?city_id={self.city_id}",
                        json={
                            "token": self.token,
                            "batch_id": batch_id,
                            "coupon_id": coupon_id,
                            "city_id": self.city_id
                        }
                    )
                    if swell_coupon_response.status_code == 200:
                        swell_coupon_data = swell_coupon_response.json()
                        if swell_coupon_data.get("errno") == 0:
                            if swell_coupon_data.get("data", {}).get("is_swell"):
                                print(f"用户【“{self.user_phone}】, ===膨胀成功🎉===")
                                continue
                            else:
                                print(f"用户【“{self.user_phone}】, ===膨胀失败, {swell_coupon_data}===")
                        else:
                            print(f"用户【“{self.user_phone}】, ===膨胀失败, {swell_coupon_data}===")
                    else:
                        print(f"===膨胀周周领券请求异常, {swell_coupon_response.text}===")

    async def receive_travel_insurance(self):
        """
        领取行程意外险
        :return: 
        """
        privileges_list = await self.inquire_benefits_details()
        for privilege in privileges_list:
            if privilege.get('name') == "行程意外险":
                need_received = privilege.get('need_received')
                if need_received == 1:  # 0为未领取，1为已领取
                    print(f"用户【“{self.user_phone}】, ===已经领取过了行程意外险===")
                    return
                elif need_received == 0:
                    print(f"用户【“{self.user_phone}】, ===开始领取行程意外险===")
                    receive_travel_insurance_response = await self.client.post(
                        url="https://member.xiaojukeji.com/dmember/h5/bindPrivilege",
                        json={"token": self.token, "type": 3}
                    )
                    if receive_travel_insurance_response.status_code == 200:
                        receive_travel_insurance_data = receive_travel_insurance_response.json()
                        if receive_travel_insurance_data.get("errno") == 0:
                            print(f"用户【“{self.user_phone}】, ===领取行程意外险成功🎉===")
                        else:
                            print(
                                f"用户【“{self.user_phone}】, ===领取行程意外险失败, {receive_travel_insurance_data}===")
                    else:
                        print(f"===领取行程意外险请求异常, {receive_travel_insurance_response.text}===")

    async def receive_memberday_discount_multi(self):
        """
        领取周三折上折权益
        :return: 
        """
        privileges_list = await self.inquire_benefits_details()
        for privilege in privileges_list:
            if privilege.get('name') == "周三折上折":
                need_received = privilege.get('need_received')
                if need_received == 1:  # 0为未领取，1为已领取
                    print(f"用户【“{self.user_phone}】, ===已经领取过了周三折上折===")
                    return
                elif need_received == 0:
                    print(f"用户【“{self.user_phone}】, ===开始领取周三折上折===")
                    receive_memberday_discount_multi_response = await self.client.post(
                        url="https://member.xiaojukeji.com/dmember/h5/receiveMemberDayDiscount",
                        json={"token": self.token, "privilege_type": 1}
                    )
                    if receive_memberday_discount_multi_response.status_code == 200:
                        receive_memberday_discount_multi_data = receive_memberday_discount_multi_response.json()
                        if receive_memberday_discount_multi_data.get("errno") == 0:
                            print(f"用户【“{self.user_phone}】, ===领取周三折上折成功🎉===")
                            return
                        else:
                            print(
                                f"用户【“{self.user_phone}】, ===领取周三折上折失败, {receive_memberday_discount_multi_data}===")
                    else:
                        print(f"===领取周三折上折请求异常, {receive_memberday_discount_multi_response.text}===")

    async def receive_wyc_order_finish(self):
        """
        领取气泡奖励完单返福利金
        :return: 
        """
        get_bubble_response = await self.client.post(
            url="https://ut.xiaojukeji.com/ut/welfare/api/home/getBubble",
            json={
                "token": self.token,
                "lat": self.lat,
                "lng": self.lng,
                "platform": "na",
                "env": "{}"
            }
        )
        get_bubble_data = get_bubble_response.json()
        bubble_list = get_bubble_data.get('data', {}).get('bubble_list', [])
        for bubble in bubble_list:
            if bubble.get('pre_content') == "完单返":
                cycle_id = bubble.get('cycle_id')
                reward_count = bubble.get('reward_count')
                receive_wyc_order_finish_response = await self.client.post(
                    url="https://ut.xiaojukeji.com/ut/welfare/api/action/clickBubble",
                    json={
                        "token": self.token,
                        "lat": self.lat,
                        "lng": self.lng,
                        "platform": "na",
                        "env": "{}",
                        "cycle_id": cycle_id,
                        "bubble_type": "wyc_order_finish"
                    }
                )
                if receive_wyc_order_finish_response.status_code == 200:
                    receive_wyc_order_finish_data = receive_wyc_order_finish_response.json()
                    if receive_wyc_order_finish_data.get("errno") == 0:
                        print(
                            f"用户【“{self.user_phone}】, ===领取气泡奖励完单返福利金成功🎉, 获得{reward_count}福利金！===")
                        return
                    else:
                        print(
                            f"用户【“{self.user_phone}】, ===领取气泡奖励完单返福利金失败, {receive_wyc_order_finish_data}===")
                else:
                    print(f"===领取气泡奖励完单返福利金请求异常, {receive_wyc_order_finish_response.text}===")

    async def claim_coupon_check_in(self):
        """
        领取天天神券签到
        :return: 
        """
        claim_coupon_check_in_response = await self.client.post(
            url="https://ut.xiaojukeji.com/ut/janitor/api/action/sign/do",
            headers={'Didi-Ticket': self.token}
        )
        if claim_coupon_check_in_response.status_code == 200:
            claim_coupon_check_in_data = claim_coupon_check_in_response.json()
            if claim_coupon_check_in_data.get("errno") == 0:
                current_progress = claim_coupon_check_in_data.get("data").get("current_progress")
                total_progress = claim_coupon_check_in_data.get("data").get("total_progress")
                print(
                    f"用户【“{self.user_phone}】, ===领取天天神券签到成功🎉签到进度：{current_progress}/{total_progress}===")
                return
            else:
                print(f"用户【“{self.user_phone}】, ===领取天天神券签到失败, {claim_coupon_check_in_data}===")
        else:
            print(f"===领取天天神券签到请求异常, {claim_coupon_check_in_response.text}===")

    async def claim_coupon_lottery(self):
        """
        天天神券抽奖
        :return: 
        """
        get_draw_times_response = await self.client.post(
            url="https://api.didi.cn/webx/chapter/product/init",
            headers={'Didi-Ticket': self.token},
            json={
                "dchn": "dKlklLa",
                "args": {
                    "runtime_args":
                        {
                            "token": self.token,
                            "lat": self.lat,
                            "lng": self.lng,
                            "env": {},
                            "platform": "na",
                            "Didi-Ticket": self.token,
                        }
                }
            }
        )
        if get_draw_times_response.status_code == 200:
            get_draw_times_data = get_draw_times_response.json()
            # 新增健壮性检查
            data = get_draw_times_data.get('data')
            if not data:
                print(f"【抽奖】接口返回异常，无data字段，原始返回: {get_draw_times_data}")
                return
            conf = data.get('conf')
            if not conf:
                print(f"【抽奖】接口返回异常，无conf字段，原始返回: {get_draw_times_data}")
                return
            strategy_data = conf.get('strategy_data')
            if not strategy_data:
                print(f"【抽奖】接口返回异常，无strategy_data字段，原始返回: {get_draw_times_data}")
                return
            strategy_data_data = strategy_data.get('data')
            if not strategy_data_data:
                print(f"【抽奖】接口返回异常，无strategy_data.data字段，原始返回: {get_draw_times_data}")
                return
            lottery_chance = strategy_data_data.get('lottery_chance')
            act_id = conf.get('ext', {}).get('act_conf', {}).get('act_id')
            if lottery_chance is None or act_id is None:
                print(f"【抽奖】接口返回异常，lottery_chance或act_id缺失，原始返回: {get_draw_times_data}")
                return
            for _ in range(lottery_chance):
                lucky_draw_response = await self.client.post(
                    url="https://ut.xiaojukeji.com/ut/janitor/api/action/lottery/doLottery",
                    headers={'Didi-Ticket': self.token},
                    json={
                        "act_id": act_id
                    }
                )
                lucky_draw_data = lucky_draw_response.json()
                if lucky_draw_data.get("errno") == 0:
                    print(
                        f"用户【“{self.user_phone}】, ===抽奖成功🎉, 获得{lucky_draw_data.get('data').get('prize_data')[0].get('name')}===")
                    await asyncio.sleep(5)
                    continue
                else:
                    print(f"用户【“{self.user_phone}】, ===天天神券抽奖失败, {lucky_draw_data}===")
                    return
        else:
            print(f"===天天神券获取抽奖次数请求异常, {get_draw_times_response.text}===")

    async def run_scratch(self):
        """
        运行刮刮乐
        :return: 
        """
        if await self.get_carve_up_action_id():
            print(f"用户【“{self.user_phone}】, ===开始完成今日瓜分活动===")
            if self.status_today == 2:
                await self.complete_carve_up_action()
            elif self.status_today == 3:
                print(f"用户【“{self.user_phone}】, ===今日瓜分活动已完成，无需重复完成！===")
            elif self.status_today == 4:
                print(f"用户【“{self.user_phone}】, ===今日已领取瓜分活动奖励！===")
            else:
                print(f"用户【“{self.user_phone}】, ===今日瓜分活动完成失败！肯昨日未报名！===")
            print(f"用户【“{self.user_phone}】, ===开始报名明日瓜分活动===")
            if self.status_tomorrow == 1:
                await self.apply_carve_up_action()
            elif self.status_tomorrow == 2:
                print(f"用户【“{self.user_phone}】, ===明日瓜分活动已报名，无需重复报名！===")
            else:
                print(f"用户【“{self.user_phone}】, ===明日瓜分活动报名失败！===")

    async def today_pick(self):
        """
        每日精选
        :return: 
        """
        get_batch_config_response = await self.client.post(
            url="https://api.didi.cn/webx/chapter/page/batch/config",
            headers={'Didi-Ticket': self.token},
            json={
                "dchn": "PxJanq9",
                "args": [
                    {"dchn": "kkXgpzO",
                     "prod_key": "ut-limited-seckill",
                     "runtime_args":
                         {
                             "token": self.token,
                             "lat": self.lat,
                             "lng": self.lng,
                             "env": {},
                             "Didi-Ticket": self.token,
                         }
                     },
                    {"dchn": "gL3E8qZ",
                     "prod_key": "ut-support-coupon",
                     "runtime_args": {
                         "token": self.token,
                         "lat": self.lat,
                         "lng": self.lng,
                         "env": {},
                         "Didi-Ticket": self.token}
                     }
                ]
            }
        )
        if get_batch_config_response.status_code == 200:
            get_batch_config_data = get_batch_config_response.json()
            activity_list = get_batch_config_data.get("data").get("conf")
            for activity in activity_list:
                if activity.get("dchn") == "gL3E8qZ":
                    print(f"用户【“{self.user_phone}】, ===开始领取每日精选===")
                    coupons_list = activity.get("strategy_data").get("data").get("daily_coupon").get("coupons")
                    coupons_status_name_dict = {
                        '1': '可领取',
                        '2': '已经领取',
                        '4': '已抢光',
                        '6': '待前置条件完成'
                    }
                    for coupon_index, coupon in enumerate(coupons_list):
                        coupons_name = coupon.get("name")
                        coupons_status = coupon.get("status")  # 1为可领取 2为已经领取 4为抽奖抢券
                        print(f"==={coupon_index + 1}.券名：{coupons_name} "
                                 f"状态：{coupons_status_name_dict.get(str(coupons_status))}===")
                        if coupons_status == 1:
                            print(f"===开始领取券：{coupons_name}===")
                            activity_id = coupon.get("activity_id")
                            if coupons_name == "打车5元券":
                                print(f"用户【{self.user_phone}】, ===【打车5元券】为分享助力才能领券，不支持自动领券===")
                                continue
                            if activity_id == "10010":
                                print(
                                    f"用户【{self.user_phone}】, ===该券为明天在目的地栏搜“领券”必得1张快车优惠券，不支持自动领取===")
                                continue
                            group_id = coupon.get("group_id")
                            coupon_conf_id = coupon.get("coupon_conf_id")
                            group_date = coupon.get("group_date")
                            bind_coupon_response = await self.client.post(
                                url="https://ut.xiaojukeji.com/ut/janitor/api/action/coupon/bind",
                                headers={'Didi-Ticket': self.token},
                                json={
                                    'group_date': group_date,
                                    "activity_id": activity_id,
                                    "group_id": group_id,
                                    "coupon_conf_id": coupon_conf_id
                                }
                            )
                            bind_coupon_data = bind_coupon_response.json()
                            if bind_coupon_data.get("errno") == 0:
                                print(f"用户【{self.user_phone}】, ===领取成功🎉===")
                                await asyncio.sleep(0.5)
                                continue
                            else:
                                print(f"用户【{self.user_phone}】, ===领取失败，{bind_coupon_data}===")
                                return
                if activity.get("dchn") == "kkXgpzO":
                    print(f"用户【“{self.user_phone}】, ===开始领取限时抢===")
                    seckill_list = activity.get("strategy_data").get("data").get("seckill")  # 秒杀列表
                    seckill_status_name_dict = {
                        '1': '正在热抢',
                        '2': '即将开始',
                        '3': '已经开抢'
                    }
                    coupons_status_name_dict = {
                        '1': '可领取',
                        '2': '已经领取',
                        '4': '抽奖抢券',
                        '5': '未到时间'
                    }
                    for seckill in seckill_list:
                        seckill_name = seckill.get("start_at")
                        seckill_status = int(seckill.get("status"))  # 1为正在热抢 2为即将开始 3为已经开抢
                        print(f"☆☆场次：{seckill_name} 状态：{seckill_status_name_dict[str(seckill_status)]}")
                        if seckill_status in [1, 3]:
                            coupons_list = seckill.get("coupons")
                            for coupon_index, coupon in enumerate(coupons_list):
                                coupons_name = coupon.get("name")
                                coupons_status = coupon.get("status")  # 1为可领取 2为已经领取 4为抽奖抢券
                                print(f"==={coupon_index + 1}.券名：{coupons_name} "
                                         f"状态：{coupons_status_name_dict.get(str(coupons_status))}===")
                                if coupons_status == 1:
                                    print(f"===开始领取券：{coupons_name}===")
                                    activity_id = coupon.get("activity_id")
                                    group_id = coupon.get("group_id")
                                    coupon_conf_id = coupon.get("coupon_conf_id")
                                    group_date = coupon.get("group_date")
                                    bind_coupon_response = await self.client.post(
                                        url="https://ut.xiaojukeji.com/ut/janitor/api/action/coupon/bind",
                                        headers={'Didi-Ticket': self.token},
                                        json={
                                            "activity_id": activity_id,
                                            "group_id": group_id,
                                            'group_date': group_date,
                                            "coupon_conf_id": coupon_conf_id
                                        }
                                    )
                                    bind_coupon_data = bind_coupon_response.json()
                                    if bind_coupon_data.get("errno") == 0:
                                        print(f"用户【{self.user_phone}】, ===领取成功🎉===")
                                        await asyncio.sleep(0.5)
                                        continue
                                    else:
                                        print(f"用户【{self.user_phone}】, ===领取失败，{bind_coupon_data}===")
                                        return
        else:
            print(f"===每日精选请求异常， {get_batch_config_response.text}===")

    async def run(self):
        await self.get_user_info()
        print(f"用户【{self.user_phone}】, ===当前福利金数量为：{await self.get_welfare_payments()}===")
        task = [
            self.today_pick(),
            self.sign_in(),
            self.run_scratch(),
            self.receive_level_gift_week(),
            self.receive_level_gift_month(),
            self.swell_coupon(),
            self.receive_travel_insurance(),
            self.receive_memberday_discount_multi(),
            self.receive_wyc_order_finish(),
            self.claim_coupon_check_in(),
            self.claim_coupon_lottery()
        ]
        await asyncio.gather(*task)
        print(f"用户【{self.user_phone}】, ===当前福利金数量为：{await self.get_welfare_payments()}===")


def get_code_from_plugin(wxid, appid="wxaf35009675aa0b2a"):
    """
    通过wex_get模块获取小程序code
    Args:
        wxid (str): 微信ID
        appid (str): 小程序的appid，默认滴滴出行
    Returns:
        dict: {success, code, data, error}
    """
    try:
        code = wx_code_auth(wxid, appid)
        if code:
            return {"success": True, "code": code, "data": {"code": code}}
        else:
            return {"success": False, "error": "获取code失败"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def signin_by_openid(code, ticket, other_params=None, headers=None):
    """
    用code和ticket发起滴滴出行登录请求，输出响应，并返回ticket字段
    Args:
        code (str): 小程序code（oauthcode）
        ticket (str): ticket参数
        other_params (dict): 额外q参数内容（可选）
        headers (dict): 请求头（可选，若None用默认）
    Returns:
        dict: {response, ticket, json}
    """
    q_dict = {
        "api_version": "1.0.1",
        "app_version": "7.0.15",
        "appid": 35009,
        "role": 1,
        "extra_info": {"channel": 1100000013},
        "device_name": "microsoft",
        "sec_session_id": "",
        "ddfp": "c37e53c1ec6153722717aa13de548aa607cb",
        "lang": "zh-CN",
        "wsgenv": "",
        "model": "microsoft microsoft",
        "unionid_through_login": True,
        "oauthcode": code,
        "ticket": ticket,
        "with_temp_ticket": True,
        "risk_info": "{}"
    }
    if other_params:
        q_dict.update(other_params)
    q_str = json.dumps(q_dict, ensure_ascii=False)
    body = f"lang=zh-CN&access_key_id=9&appversion=7.0.15&channel=1100000013&_ds=&q={q_str}"
    if headers is None:
        headers = {
            "didi-header-hint-content": '{"lang":"zh-CN","Cityid":38}',
            "mpxlogin-ver": "5.6.3",
            "wsgsig": "dd05-30pAWNfQDCU/Pr9aB4wLB9bKf9E9pVlk31wE9GGj6BkSYmUBE4SAGbbvBBkkoqaA8LSUAcCzfaaBZtedJ+2e9GnsfdkUTl9a43w/BbgWbBrxwreeB326eGCJcEAPOt96g4MYAgWQbcA5jq91L3Se9GCucdEqmrAFA2w2e0CpDAkARr9F3NSE89CRfdBTOh/T755AHbCpfdqEjX9L",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090c33)XWEB/14185",
            "didi-header-rid": "19fc74df6879e07c9f5475c237b61958",
            "content-type": "application/x-www-form-urlencoded",
            "xweb_xhr": "1",
            "secdd-authentication": "8a0d6f65db63c27642d73a9d986a4e19b6852c8cea45d3d8c7ebf3bbcdd983ce18b7b7274109bf0715b93ceb2095efb195e5141c9801000001000000",
            "secdd-challenge": "3|2.0.41||||||",
            "accept": "*/*",
            "sec-fetch-site": "cross-site",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": "https://servicewechat.com/wxaf35009675aa0b2a/1041/page-frame.html",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "zh-CN,zh;q=0.9",
            "priority": "u=1, i"
        }
    url = "https://epassport.diditaxi.com.cn/passport/login/v5/signInByOpenid"
    resp = requests.post(url, headers=headers, data=body, timeout=15)
    print(resp.status_code)
    print(resp.text)
    try:
        resp_json = resp.json()
        ticket_value = resp_json.get("ticket")
    except Exception:
        resp_json = None
        ticket_value = None
    return {"response": resp, "ticket": ticket_value, "json": resp_json}


def init_dd_tokens_from_wxidlist(wxidlist):
    """
    根据微信ID列表批量获取ticket，返回dd_tokens列表
    """
    dd_tokens = []
    for wxid in wxidlist:
        print(f"\n处理wxid: {wxid}")
        code_result = get_code_from_plugin(wxid)
        if not code_result.get("success"):
            print(f"❌ 获取code失败: {code_result.get('error')}")
            continue
        code = code_result["code"]
        # 初始ticket可为空字符串或指定初始ticket
        ticket = "_HhBaGWkpEOu-j0kxzY_NAcYC7H6ZK_Prs_JNduBsLAkzDmuwzAMQMG7vJowSNESJd7mL87SKECCVIbvHiCuppudqSS-6KII00gTZiG9qg5hOmlRh5dmbt2qC3MlVZiVBOHn5JcsY2iLElbc21qE_2-3kTuvx_v5t5FVVcchXEhrvXnrESFcSay3GFGraUG4ne2d1OMTAAD__w=="
        result = signin_by_openid(code, ticket)
        new_ticket = result["ticket"]
        if new_ticket:
            print(f"接口返回ticket: {new_ticket}")
            dd_tokens.append(new_ticket)
        else:
            print("未获取到ticket，跳过该账号")
    return dd_tokens


async def main():
    # 从环境变量获取微信ID列表
    dd_wxid_data = os.getenv("dd_wxid_data")
    if not dd_wxid_data:
        print("❌ 未设置环境变量dd_wxid_data，请检查环境变量")
        return
    
    # 支持多种分隔符
    MULTI_ACCOUNT_SPLIT = ["\n", "@", "&"]
    split_char = None
    for sep in MULTI_ACCOUNT_SPLIT:
        if sep in dd_wxid_data:
            split_char = sep
            break
    
    if not split_char:
        # 如果都没有分隔符，默认当作单账号
        wxidlist = [dd_wxid_data]
    else:
        wxidlist = [x.strip() for x in dd_wxid_data.split(split_char) if x.strip()]
    
    print(f"获取到 {len(wxidlist)} 个账号")
    dd_tokens = init_dd_tokens_from_wxidlist(wxidlist)
    print(f"最终dd_tokens: {dd_tokens}")
    task = []
    didi_objs = []
    for token in dd_tokens:
        dd = DiDi(token)
        didi_objs.append(dd)
        task.append(dd.run())
    await asyncio.gather(*task)
    # 主动关闭所有 httpx.AsyncClient
    await asyncio.gather(*(dd.aclose() for dd in didi_objs))


if __name__ == '__main__':
    asyncio.run(main())
    print("滴滴出行通知 - {}".format(datetime.datetime.now().strftime("%Y/%m/%d")))
# 当前脚本来自于http://script.345yun.cn脚本库下载！