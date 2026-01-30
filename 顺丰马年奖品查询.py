"""
顺丰速运马年活动奖品查询脚本
Author: 爱学习的呆子
Version: 1.0
Date: 2026-01-30
活动代码: YEAREND_2025

功能说明:
- 查询马年活动奖品(6元及以上寄件券+所有实物奖品)
- 支持批量查询多个账号
- 自动过滤并显示符合条件的奖品

配置说明:
- ENV_NAME: 环境变量名称，默认为 sfsyUrl
"""

import hashlib
import json
import os
import random
import time
from datetime import datetime
from typing import Dict, Optional, Any, List
from urllib.parse import unquote
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

CONCURRENT_NUM = int(os.getenv('SFBF', '1'))
if CONCURRENT_NUM > 20:
    CONCURRENT_NUM = 20
    print(f'⚠️ 并发数量超过最大值20，已自动调整为20')
elif CONCURRENT_NUM < 1:
    CONCURRENT_NUM = 1
    print(f'⚠️ 并发数量小于1，已自动调整为1（串行模式）')

print_lock = Lock()


class Config:
    """全局配置"""
    APP_NAME: str = "顺丰马年活动奖品查询"
    VERSION: str = "1.0"
    ENV_NAME: str = "sfsyUrl"
    ACTIVITY_CODE: str = "YEAREND_2025"
    TOKEN: str = 'wwesldfs29aniversaryvdld29'
    SYS_CODE: str = 'MCS-MIMP-CORE'


class SFHttpClient:
    """顺丰HTTP客户端"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False
        
        self.headers = {
            'Host': 'mcs-mimp-web.sf-express.com',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 16; PJE110 Build/TP1A.220905.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/134.0.6998.135 Mobile Safari/537.36 mediaCode=SFEXPRESSAPP-Android-ML',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Content-Type': 'application/json',
            'sec-ch-ua-platform': '"Android"',
            'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Android WebView";v="134"',
            'sec-ch-ua-mobile': '?1',
            'channel': 'daluapp',
            'syscode': 'MCS-MIMP-CORE',
            'platform': 'SFAPP',
            'origin': 'https://mcs-mimp-web.sf-express.com',
            'x-requested-with': 'com.sf.activity',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'priority': 'u=1, i'
        }
    
    def _generate_sign(self) -> Dict[str, str]:
        """生成签名"""
        timestamp = str(int(round(time.time() * 1000)))
        data = f'token={Config.TOKEN}&timestamp={timestamp}&sysCode={Config.SYS_CODE}'
        signature = hashlib.md5(data.encode()).hexdigest()
        
        return {
            'timestamp': timestamp,
            'signature': signature
        }
    
    def login(self, url: str) -> tuple[bool, str, str]:
        """登录获取session"""
        try:
            decoded_url = unquote(url)
            self.session.get(decoded_url, headers=self.headers, timeout=15)
            
            cookies = self.session.cookies.get_dict()
            session_id = cookies.get('sessionId', '')
            phone = cookies.get('_login_mobile_', '')
            
            if session_id and phone:
                return True, session_id, phone
            else:
                return False, '', ''
        except Exception as e:
            print(f'登录异常: {str(e)}')
            return False, '', ''
    
    def query_year_end_awards(self, session_id: str) -> Dict[str, Any]:
        """查询马年活动奖品"""
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~activityCore~userAwardService~queryUserAward'
        
        sign_data = self._generate_sign()
        self.headers.update(sign_data)
        self.headers['Cookie'] = f'sessionId={session_id}'
        
        data = {
            "tag": Config.ACTIVITY_CODE,
            "productType": "",
            "pageNo": 1,
            "pageSize": 200
        }
        
        try:
            response = self.session.post(url, headers=self.headers, json=data, timeout=15)
            result = response.json()
            
            if result.get('success'):
                return result.get('obj', {})
            else:
                error_msg = result.get('errorMessage', '未知错误')
                print(f'查询失败: {error_msg}')
                return {}
        except Exception as e:
            print(f'查询异常: {str(e)}')
            return {}


class AwardProcessor:
    """奖品处理器"""
    
    @staticmethod
    def process_awards(award_list: List[Dict]) -> Dict[str, List[str]]:
        """处理奖品列表,筛选6元及以上寄件券和所有实物奖品"""
        coupon_awards = []
        physical_awards = []
        
        for award in award_list:
            try:
                product_type = award.get('productType', '')
                product_name = award.get('productName', '未知奖品')
                amount = award.get('amount', 1)
                expiration_date = award.get('expirationDate', '')
                
                if product_type == 'SFC':
                    coupon_name = award.get('couponName', '')
                    denomination = award.get('denomination', '0')
                    coupon_type = award.get('couponType', 1)
                    
                    try:
                        denom_value = int(denomination)
                        if denom_value >= 6:
                            type_text = "立减券" if coupon_type == 1 else "折扣券"
                            if amount > 1:
                                award_info = f"  • {coupon_name} x{amount}张 | 面额: {denomination}元 | 过期: {expiration_date}"
                            else:
                                award_info = f"  • {coupon_name} | 面额: {denomination}元 | 过期: {expiration_date}"
                            coupon_awards.append(award_info)
                    except:
                        continue
                        
                elif product_type == 'SFP':
                    # 排除所有优惠券相关的关键词
                    exclude_keywords = ['积分', '券', '折', '抵扣', '立减', '减免']
                    if not any(keyword in product_name for keyword in exclude_keywords):
                        if amount > 1:
                            award_info = f"  • {product_name} x{amount}"
                        else:
                            award_info = f"  • {product_name}"
                        physical_awards.append(award_info)
                else:
                    # 排除所有优惠券相关的关键词
                    exclude_keywords = ['积分', '券', '折', '抵扣', '立减', '减免']
                    if product_type and product_type not in ['SFC', 'SFP'] and not any(keyword in product_name for keyword in exclude_keywords):
                        if amount > 1:
                            award_info = f"  • {product_name} x{amount}"
                        else:
                            award_info = f"  • {product_name}"
                        physical_awards.append(award_info)
                    
            except Exception as e:
                print(f"处理奖品出错: {str(e)}")
                continue
        
        return {
            'coupons': coupon_awards,
            'physical': physical_awards
        }
    
    @staticmethod
    def format_result(phone: str, awards: Dict[str, List[str]], total: int) -> str:
        """格式化查询结果"""
        masked_phone = phone[:3] + "****" + phone[7:] if len(phone) == 11 else phone
        
        result_lines = [
            f"📱 账号: {masked_phone}",
            f"🎁 奖品总数: {total}个"
        ]
        
        if awards['coupons'] or awards['physical']:
            coupon_count = len(awards['coupons'])
            physical_count = len(awards['physical'])
            total_count = coupon_count + physical_count
            result_lines.append(f"\n🎁 马年活动奖品 ({total_count}个):")
            if awards['coupons']:
                result_lines.extend(awards['coupons'])
            if awards['physical']:
                result_lines.extend(awards['physical'])
        
        if not awards['coupons'] and not awards['physical']:
            result_lines.append("\n❌ 暂无符合条件的奖品")
        
        return '\n'.join(result_lines)


def run_single_account(account_url: str, index: int) -> Dict[str, Any]:
    """执行单个账号查询"""
    try:
        with print_lock:
            print(f"🚀 开始执行账号{index + 1}")
        
        http_client = SFHttpClient()
        award_processor = AwardProcessor()
        
        success, session_id, phone = http_client.login(account_url)
        
        if not success:
            with print_lock:
                print(f"❌ 账号{index + 1} 登录失败")
            return {
                'index': index,
                'success': False,
                'phone': '',
                'total': 0,
                'coupon_count': 0,
                'physical_count': 0
            }
        
        masked_phone = phone[:3] + "****" + phone[7:] if len(phone) == 11 else phone
        with print_lock:
            print(f"✅ 账号{index + 1} 登录成功: {masked_phone}")
        
        time.sleep(random.uniform(0.5, 1.5))
        
        award_obj = http_client.query_year_end_awards(session_id)
        
        if not award_obj:
            with print_lock:
                print(f"❌ 账号{index + 1} 查询奖品失败")
            return {
                'index': index,
                'success': False,
                'phone': phone,
                'total': 0,
                'coupon_count': 0,
                'physical_count': 0
            }
        
        award_list = award_obj.get('list', [])
        total = award_obj.get('total', 0)
        
        awards = award_processor.process_awards(award_list)
        result = award_processor.format_result(phone, awards, total)
        
        # 检查是否有重点奖品(12元寄件券或实物)
        has_12_coupon = False
        key_prizes = []
        
        for award in award_list:
            product_type = award.get('productType', '')
            product_name = award.get('productName', '')
            
            # 检查12元寄件券
            if product_type == 'SFC':
                denomination = award.get('denomination', '0')
                try:
                    if int(denomination) == 12:
                        has_12_coupon = True
                        key_prizes.append('12元寄件券')
                except:
                    pass
            
            # 检查实物奖品
            elif product_type == 'SFP':
                exclude_keywords = ['积分', '券', '折', '抵扣', '立减', '减免']
                if not any(keyword in product_name for keyword in exclude_keywords):
                    key_prizes.append(product_name)
            elif product_type and product_type not in ['SFC', 'SFP']:
                exclude_keywords = ['积分', '券', '折', '抵扣', '立减', '减免']
                if not any(keyword in product_name for keyword in exclude_keywords):
                    key_prizes.append(product_name)
        
        with print_lock:
            print(f"\n{result}")
            print(f"✅ 账号{index + 1} 查询完成")
        
        return {
            'index': index,
            'success': True,
            'phone': phone,
            'total': total,
            'coupon_count': len(awards['coupons']),
            'physical_count': len(awards['physical']),
            'has_key_prize': len(key_prizes) > 0,
            'key_prizes': key_prizes
        }
    except Exception as e:
        error_msg = f"账号{index + 1} 执行异常: {str(e)}"
        with print_lock:
            print(f"❌ {error_msg}")
        return {
            'index': index,
            'success': False,
            'phone': '',
            'total': 0,
            'coupon_count': 0,
            'physical_count': 0,
            'error': error_msg
        }


def main():
    """主函数"""
    config = Config()
    
    env_value = os.getenv(config.ENV_NAME)
    if not env_value:
        print(f"❌ 未找到环境变量 {config.ENV_NAME}，请检查配置")
        return
    
    account_urls = [url.strip() for url in env_value.split('&') if url.strip()]
    if not account_urls:
        print(f"❌ 环境变量 {config.ENV_NAME} 为空或格式错误")
        return
    
    random.shuffle(account_urls)
    print(f"🔀 已随机打乱账号执行顺序")
    
    print("=" * 80)
    print(f"🎉 {config.APP_NAME} v{config.VERSION}")
    print(f"👨‍💻 作者: 爱学习的呆子")
    print(f"🎊 活动代码: {config.ACTIVITY_CODE}")
    print(f"📱 共获取到 {len(account_urls)} 个账号")
    print(f"⚙️ 并发数量: {CONCURRENT_NUM}")
    print(f"⏰ 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    all_results = []
    
    if CONCURRENT_NUM <= 1:
        print("🔄 使用串行模式执行...")
        for index, account_url in enumerate(account_urls):
            result = run_single_account(account_url, index)
            all_results.append(result)
            
            if index < len(account_urls) - 1:
                print("=" * 80)
                print(f"⏳ 等待 2 秒后执行下一个账号...")
                time.sleep(2)
    else:
        print(f"🔄 使用并发模式执行，并发数: {CONCURRENT_NUM}")
        
        with ThreadPoolExecutor(max_workers=CONCURRENT_NUM) as executor:
            future_to_index = {
                executor.submit(run_single_account, account_url, index): index 
                for index, account_url in enumerate(account_urls)
            }
            
            for future in as_completed(future_to_index):
                result = future.result()
                all_results.append(result)
    
    all_results.sort(key=lambda x: x['index'])
    
    success_count = sum(1 for r in all_results if r['success'])
    fail_count = len(all_results) - success_count
    total_coupons = sum(r.get('coupon_count', 0) for r in all_results)
    total_physical = sum(r.get('physical_count', 0) for r in all_results)
    
    # 统计重点奖品获得者
    key_prize_winners = []
    for result in all_results:
        if result.get('has_key_prize', False):
            phone = result['phone']
            masked_phone = phone[:3] + "****" + phone[7:] if len(phone) == 11 else phone
            prizes = result.get('key_prizes', [])
            key_prize_winners.append({
                'phone': masked_phone,
                'prizes': prizes
            })
    
    print(f"\n{'=' * 80}")
    print(f"📊 查询统计")
    print("=" * 80)
    print(f"✅ 成功: {success_count}个")
    print(f"❌ 失败: {fail_count}个")
    print(f"📱 总计: {len(account_urls)}个")
    print(f"🎫 寄件券: {total_coupons}张")
    print(f"🎁 实物奖品: {total_physical}个")
    print("=" * 80)
    
    # 显示重点奖品获得者
    if key_prize_winners:
        print(f"\n{'=' * 80}")
        print(f"🎁 重点奖品获得者 (12元寄件券/实物)")
        print("=" * 80)
        for idx, winner in enumerate(key_prize_winners, 1):
            prizes_text = ', '.join(winner['prizes'])
            print(f"{idx}. 📱 {winner['phone']} - 🎁 {prizes_text}")
        print("=" * 80)
        print(f"🎉 共 {len(key_prize_winners)} 位用户获得重点奖品!")
    else:
        print(f"\n{'=' * 80}")
        print(f"💡 本次查询暂无用户获得重点奖品(12元寄件券/实物)")
        print("=" * 80)
    
    print(f"\n🎊 所有账号马年活动奖品查询完成!")


if __name__ == '__main__':
    main()
