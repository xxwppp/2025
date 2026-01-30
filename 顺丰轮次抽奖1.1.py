"""
顺丰速运新年活动 - 轮次抽奖脚本
Author: 爱学习的呆子
Version: 1.0.0
Date: 2026-01-28
活动代码: YEAREND_2025

功能说明:
本脚本专门用于执行顺丰新年活动的轮次抽奖功能
- 自动检查当前轮次抽奖状态
- 自动执行所有可用的轮次抽奖次数
- 支持多账号并发执行
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

PROXY_TIMEOUT = 15
MAX_PROXY_RETRIES = 5
REQUEST_RETRY_COUNT = 3

CONCURRENT_NUM = int(os.getenv('SFBF', '10'))
if CONCURRENT_NUM > 20:
    CONCURRENT_NUM = 20
    print(f'⚠️ 并发数量超过最大值20，已自动调整为20')
elif CONCURRENT_NUM < 1:
    CONCURRENT_NUM = 1
    print(f'⚠️ 并发数量小于1，已自动调整为1（串行模式）')

print_lock = Lock()


class Config:
    """全局配置"""
    APP_NAME: str = "顺丰速运新年活动-轮次抽奖"
    VERSION: str = "1.0.0"
    ENV_NAME: str = "sfsyUrl"
    PROXY_API_URL: str = os.getenv('SF_PROXY_API_URL', '')
    ACTIVITY_CODE: str = "YEAREND_2025"
    
    TOKEN: str = 'wwesldfs29aniversaryvdld29'
    SYS_CODE: str = 'MCS-MIMP-CORE'


class Logger:
    """日志管理器"""
    
    ICONS = {
        'info': '📝',
        'success': '✨',
        'error': '❌',
        'warning': '⚠️',
        'user': '👤',
        'gift': '🎁',
    }
    
    def __init__(self):
        self.messages: List[str] = []
        self.lock = Lock()
    
    def _format_msg(self, icon: str, content: str) -> str:
        return f"{icon} {content}"
    
    def _safe_print(self, msg: str):
        with print_lock:
            print(msg)
    
    def info(self, content: str):
        msg = self._format_msg(self.ICONS['info'], content)
        self._safe_print(msg)
        with self.lock:
            self.messages.append(msg)
    
    def success(self, content: str):
        msg = self._format_msg(self.ICONS['success'], content)
        self._safe_print(msg)
        with self.lock:
            self.messages.append(msg)
    
    def error(self, content: str):
        msg = self._format_msg(self.ICONS['error'], content)
        self._safe_print(msg)
        with self.lock:
            self.messages.append(msg)
    
    def warning(self, content: str):
        msg = self._format_msg(self.ICONS['warning'], content)
        self._safe_print(msg)
        with self.lock:
            self.messages.append(msg)
    
    def user_info(self, account_index: int, mobile: str):
        msg = self._format_msg(self.ICONS['user'], f"账号{account_index}: 【{mobile}】登录成功")
        self._safe_print(msg)
        with self.lock:
            self.messages.append(msg)


class ProxyManager:
    """代理管理器"""
    
    def __init__(self, api_url: str):
        self.api_url = api_url
    
    def get_proxy(self) -> Optional[Dict[str, str]]:
        try:
            if not self.api_url:
                print('⚠️ 未配置代理API地址，将不使用代理')
                return None
            
            response = requests.get(self.api_url, timeout=10)
            if response.status_code == 200:
                proxy_text = response.text.strip()
                if ':' in proxy_text:
                    if proxy_text.startswith('http://') or proxy_text.startswith('https://'):
                        proxy = proxy_text
                    else:
                        proxy = f'http://{proxy_text}'
                    
                    display_proxy = proxy
                    if '@' in proxy:
                        parts = proxy.split('@')
                        if len(parts) == 2:
                            display_proxy = f"http://***:***@{parts[1]}"
                    
                    print(f"✅ 成功获取代理: {display_proxy}")
                    return {'http': proxy, 'https': proxy}
            
            print(f'❌ 获取代理失败: {response.text}')
            return None
        except Exception as e:
            print(f'❌ 获取代理异常: {str(e)}')
            return None


class SFHttpClient:
    """顺丰HTTP客户端"""
    
    def __init__(self, config: Config, proxy_manager: ProxyManager):
        self.config = config
        self.proxy_manager = proxy_manager
        self.session = requests.Session()
        self.session.verify = False
        
        proxy = self.proxy_manager.get_proxy()
        if proxy:
            self.session.proxies = proxy
        
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
        timestamp = str(int(round(time.time() * 1000)))
        data = f'token={self.config.TOKEN}&timestamp={timestamp}&sysCode={self.config.SYS_CODE}'
        signature = hashlib.md5(data.encode()).hexdigest()
        
        return {
            'timestamp': timestamp,
            'signature': signature
        }
    
    def request(
        self, 
        url: str, 
        method: str = 'POST', 
        data: Optional[Dict] = None,
        max_retries: int = REQUEST_RETRY_COUNT
    ) -> Optional[Dict[str, Any]]:
        sign_data = self._generate_sign()
        self.headers.update(sign_data)
        
        retry_count = 0
        proxy_retry_count = 0
        
        while proxy_retry_count < MAX_PROXY_RETRIES:
            try:
                if retry_count >= 2:
                    print('请求已失败2次，尝试切换代理IP')
                    new_proxy = self.proxy_manager.get_proxy()
                    if new_proxy:
                        self.session.proxies = new_proxy
                    else:
                        print('⚠️ 切换代理失败，无可用代理')
                    retry_count = 0
                
                try:
                    if method.upper() == 'GET':
                        response = self.session.get(url, headers=self.headers, timeout=PROXY_TIMEOUT)
                    elif method.upper() == 'POST':
                        response = self.session.post(url, headers=self.headers, json=data or {}, timeout=PROXY_TIMEOUT)
                    else:
                        raise ValueError(f'不支持的请求方法: {method}')
                    
                    response.raise_for_status()
                    
                    try:
                        res = response.json()
                        if res is None:
                            print(f'响应内容为空，正在重试 ({retry_count + 1}/{max_retries})')
                            retry_count += 1
                            time.sleep(2)
                            continue
                        return res
                    except (json.JSONDecodeError, ValueError) as e:
                        print(f'JSON解析失败: {str(e)}, 响应内容: {response.text[:200]}')
                        retry_count += 1
                        if retry_count < max_retries:
                            print(f'正在进行第{retry_count + 1}次重试...')
                            time.sleep(2)
                            continue
                        return None
                
                except requests.exceptions.RequestException as e:
                    retry_count += 1
                    print(f'请求失败，正在重试 ({retry_count}/{max_retries}): {str(e)}')
                    if 'ProxyError' in str(e) or 'SSLError' in str(e):
                        proxy_retry_count += 1
                        print(f'代理连接失败，尝试切换代理 ({proxy_retry_count}/{MAX_PROXY_RETRIES})')
                        if proxy_retry_count < MAX_PROXY_RETRIES:
                            new_proxy = self.proxy_manager.get_proxy()
                            if new_proxy:
                                self.session.proxies = new_proxy
                    time.sleep(2)
                    continue
            
            except Exception as e:
                print(f'请求发生异常: {str(e)}')
                proxy_retry_count += 1
                if proxy_retry_count < MAX_PROXY_RETRIES:
                    print(f'尝试切换代理 ({proxy_retry_count}/{MAX_PROXY_RETRIES})')
                    time.sleep(2)
                    continue
                else:
                    print('达到最大代理重试次数，返回None')
                    return None
        
        print('请求最终失败，返回None')
        return None
    
    def login(self, url: str, timeout: int = PROXY_TIMEOUT) -> tuple[bool, str, str]:
        try:
            decoded_url = unquote(url)    #适合编码后的url跑  也就是插件提交上来 用&分割的
            #decoded_url = url            #适合未编码的url跑  也就是正常的URL  手动抓的那种  用\n换行分割  需修改500行的&分割为\n
            self.session.get(decoded_url, headers=self.headers, timeout=timeout)
            
            cookies = self.session.cookies.get_dict()
            user_id = cookies.get('_login_user_id_', '')
            phone = cookies.get('_login_mobile_', '')
            
            if phone:
                return True, user_id, phone
            else:
                return False, '', ''
        except Exception as e:
            print(f'登录异常: {str(e)}')
            return False, '', ''


class LotteryDrawService:
    """轮次抽奖服务"""
    
    def __init__(self, http_client: SFHttpClient, logger: Logger):
        self.http = http_client
        self.logger = logger
    
    def check_lottery_status(self) -> tuple[bool, List[Dict[str, Any]]]:
        """检查轮次抽奖状态
        
        Returns:
            tuple[bool, List[Dict]]: (是否有可抽奖轮次, 可抽奖轮次列表)
        """
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~yearEnd2025ForwardService~forwardStatus'
        data = {}
        
        response = self.http.request(url, data=data)
        if response and response.get('success'):
            obj = response.get('obj', {})
            current_level = obj.get('currentLevel', '')
            level_list = obj.get('levelList', [])
            
            self.logger.info(f'当前轮次: {current_level}')
            
            available_levels = []
            for level in level_list:
                currency = level.get('currency', '')
                balance = level.get('balance', 0)
                total_amount = level.get('totalAmount', 0)
                self.logger.info(f'  - {currency}: 可抽奖 {balance}/{total_amount} 次')
                
                if balance > 0:
                    available_levels.append({
                        'currency': currency,
                        'balance': balance,
                        'total_amount': total_amount
                    })
            
            if available_levels:
                total_draws = sum(level['balance'] for level in available_levels)
                return True, available_levels
            else:
                self.logger.warning('所有轮次抽奖次数已用完')
                return False, []
        else:
            error_msg = response.get('errorMessage', '未知错误') if response else '请求失败'
            self.logger.error(f'查询轮次抽奖状态失败: {error_msg}')
            return False, []
    
    def do_lottery_draw(self, currency: str) -> tuple[bool, Optional[Dict[str, Any]]]:
        """执行轮次抽奖
        
        Args:
            currency: 轮次标识（如 LU, FU, HAPPY, LUCKY, RAISE）
            
        Returns:
            tuple[bool, Optional[Dict]]: (是否抽奖成功, 奖品详情)
        """
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~yearEnd2025LotteryService~prizeDraw'
        data = {"currency": currency}
        
        response = self.http.request(url, data=data)
        if response and response.get('success'):
            obj = response.get('obj', {})
            gift_bag_name = obj.get('giftBagName', '未知奖励')
            gift_bag_worth = obj.get('giftBagWorth', 0)
            product_list = obj.get('productDTOList', [])
            
            reward_details = []
            prize_info = {
                'gift_bag_name': gift_bag_name,
                'gift_bag_worth': gift_bag_worth,
                'products': []
            }
            
            for product in product_list:
                product_name = product.get('productName', '')
                amount = product.get('amount', 0)
                if product_name:
                    reward_details.append(f'{product_name} x{amount}')
                    prize_info['products'].append({
                        'name': product_name,
                        'amount': amount
                    })
            
            reward_text = ', '.join(reward_details) if reward_details else f'{gift_bag_name} (价值{gift_bag_worth}元)'
            self.logger.success(f'🎁 轮次抽奖成功！获得: {reward_text}')
            return True, prize_info
        else:
            error_msg = response.get('errorMessage', '未知错误') if response else '请求失败'
            self.logger.error(f'轮次抽奖失败: {error_msg}')
            return False, None
    
    def run(self) -> Dict[str, Any]:
        """执行轮次抽奖任务"""
        print('-' * 50)
        
        can_lottery, available_levels = self.check_lottery_status()
        
        if not can_lottery or not available_levels:
            self.logger.info('当前无可用的轮次抽奖次数')
            return {
                'success': True,
                'lottery_count': 0,
                'levels_drawn': [],
                'prizes': []
            }
        
        total_lottery_count = 0
        levels_drawn = []
        all_prizes = []
        
        for level_info in available_levels:
            currency = level_info['currency']
            balance = level_info['balance']
            
            
            level_lottery_count = 0
            for i in range(balance):
                success, prize_info = self.do_lottery_draw(currency)
                if success:
                    level_lottery_count += 1
                    total_lottery_count += 1
                    if prize_info:
                        all_prizes.append(prize_info)
                    time.sleep(1)
                else:
                    break
            
            if level_lottery_count > 0:
                levels_drawn.append({
                    'currency': currency,
                    'count': level_lottery_count
                })
        
        if total_lottery_count > 0:
            self.logger.success(f'所有轮次抽奖完成，总计抽奖 {total_lottery_count} 次')
        
        return {
            'success': True,
            'lottery_count': total_lottery_count,
            'levels_drawn': levels_drawn,
            'prizes': all_prizes
        }


class AccountManager:
    """账号管理器"""
    
    def __init__(self, account_url: str, account_index: int, config: Config):
        self.account_url = account_url
        self.account_index = account_index + 1
        self.config = config
        self.logger = Logger()
        self.proxy_manager = ProxyManager(config.PROXY_API_URL)
        
        self.login_success = False
        self.user_id = None
        self.phone = None
        self.http_client = None
        
        retry_count = 0
        while retry_count < MAX_PROXY_RETRIES and not self.login_success:
            try:
                self.http_client = SFHttpClient(config, self.proxy_manager)
                
                success, self.user_id, self.phone = self.http_client.login(account_url)
                
                if success:
                    masked_phone = self.phone[:3] + "*" * 4 + self.phone[7:]
                    self.logger.user_info(self.account_index, masked_phone)
                    self.login_success = True
                    break
                else:
                    if retry_count < MAX_PROXY_RETRIES - 1:
                        print(f'账号{self.account_index} 登录失败，尝试重新获取代理 ({retry_count + 1}/{MAX_PROXY_RETRIES})')
                        time.sleep(2)
            except Exception as e:
                print(f'账号{self.account_index} 登录异常: {str(e)[:100]}')
            
            retry_count += 1
        
        if not self.login_success:
            self.logger.error(f'账号{self.account_index} 登录失败，已重试{MAX_PROXY_RETRIES}次，所有代理均不可用')
    
    def run(self) -> Dict[str, Any]:
        if not self.login_success:
            return {
                'success': False,
                'phone': '',
                'lottery_count': 0,
                'levels_drawn': [],
                'prizes': []
            }
        
        wait_time = random.randint(1000, 3000) / 1000.0
        time.sleep(wait_time)
        
        lottery_service = LotteryDrawService(self.http_client, self.logger)
        result = lottery_service.run()
        
        result['phone'] = self.phone
        return result


def run_single_account(account_info: str, index: int, config: Config) -> Dict[str, Any]:
    try:
        with print_lock:
            print(f"🚀 开始执行账号{index + 1}")
        
        account = AccountManager(account_info, index, config)
        result = account.run()
        
        if result['success']:
            with print_lock:
                print(f"✅ 账号{index + 1}执行完成")
        else:
            with print_lock:
                print(f"❌ 账号{index + 1}执行失败")
        
        result['index'] = index
        return result
    except Exception as e:
        error_msg = f"账号{index + 1}执行异常: {str(e)}"
        with print_lock:
            print(f"❌ {error_msg}")
        return {
            'index': index,
            'success': False,
            'phone': '',
            'lottery_count': 0,
            'levels_drawn': [],
            'prizes': [],
            'error': error_msg
        }


def main():
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

    print("=" * 50)
    print(f"🎉 {config.APP_NAME} v{config.VERSION}")
    print(f"👨‍💻 作者: 爱学习的呆子")
    print(f"🎊 活动代码: {config.ACTIVITY_CODE}")
    print(f"📱 共获取到 {len(account_urls)} 个账号")
    print(f"⚙️ 并发数量: {CONCURRENT_NUM}")
    print(f"⏰ 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    all_results = []
    
    if CONCURRENT_NUM <= 1:
        print("🔄 使用串行模式执行...")
        for index, account_url in enumerate(account_urls):
            account = AccountManager(account_url, index, config)
            result = account.run()
            result['index'] = index
            all_results.append(result)
            
            if index < len(account_urls) - 1:
                print("=" * 50)
                print(f"⏳ 等待 2 秒后执行下一个账号...")
                time.sleep(2)
    else:
        print(f"🔄 使用并发模式执行，并发数: {CONCURRENT_NUM}")
        
        with ThreadPoolExecutor(max_workers=CONCURRENT_NUM) as executor:
            future_to_index = {
                executor.submit(run_single_account, account_url, index, config): index 
                for index, account_url in enumerate(account_urls)
            }
            
            for future in as_completed(future_to_index):
                result = future.result()
                all_results.append(result)
    
    all_results.sort(key=lambda x: x['index'])
    
    success_count = sum(1 for r in all_results if r['success'])
    fail_count = len(all_results) - success_count
    total_lottery = sum(r.get('lottery_count', 0) for r in all_results)
    
    print(f"\n" + "=" * 100)
    print(f"📊 轮次抽奖统计")
    print("=" * 100)
    print(f"{'序号':<6} {'手机号':<15} {'抽奖轮次':<30} {'抽奖次数':<10} {'状态':<10}")
    print("-" * 100)
    
    for result in all_results:
        index = result['index'] + 1
        phone = result['phone'][:3] + "****" + result['phone'][7:] if result['phone'] else "未登录"
        levels_drawn = result.get('levels_drawn', [])
        levels_text = ', '.join([f"{l['currency']}({l['count']})" for l in levels_drawn]) if levels_drawn else '-'
        lottery_count = result.get('lottery_count', 0)
        status = "✅成功" if result['success'] else "❌失败"
        
        print(f"{index:<6} {phone:<15} {levels_text:<30} {lottery_count:<10} {status:<10}")
    
    print("-" * 100)
    print(f"{'汇总':<6} {'总数: ' + str(len(all_results)):<15} {'':<30} {'抽奖: ' + str(total_lottery):<10} {'成功: ' + str(success_count):<10}")
    print("=" * 100)
    
    voucher_12_winners = []
    physical_prize_winners = []
    
    for result in all_results:
        if not result['success'] or not result.get('prizes'):
            continue
        
        index = result['index'] + 1
        phone = result['phone'][:3] + "****" + result['phone'][7:] if result['phone'] else "未登录"
        
        voucher_12_items = []
        physical_items = []
        
        for prize in result.get('prizes', []):
            for product in prize.get('products', []):
                product_name = product.get('name', '')
                amount = product.get('amount', 0)
                
                if '12元' in product_name and '寄件券' in product_name:
                    voucher_12_items.append(f"{product_name} x{amount}")
                
                if '券' not in product_name and '积分' not in product_name:
                    physical_items.append(f"{product_name} x{amount}")
        
        if voucher_12_items:
            voucher_12_winners.append({
                'index': index,
                'phone': phone,
                'items': voucher_12_items
            })
        
        if physical_items:
            physical_prize_winners.append({
                'index': index,
                'phone': phone,
                'items': physical_items
            })
    
    if voucher_12_winners or physical_prize_winners:
        print("\n" + "=" * 100)
        print("🎁 重点奖品获奖名单")
        print("=" * 100)
        
        if voucher_12_winners:
            print("\n💰 【12元寄件券】获奖用户:")
            print("-" * 100)
            for winner in voucher_12_winners:
                items_text = ', '.join(winner['items'])
                print(f"  账号{winner['index']}: {winner['phone']} - {items_text}")
        
        if physical_prize_winners:
            print("\n🎀 【实物奖品】获奖用户:")
            print("-" * 100)
            for winner in physical_prize_winners:
                items_text = ', '.join(winner['items'])
                print(f"  账号{winner['index']}: {winner['phone']} - {items_text}")
        
        print("=" * 100)
    
    print("\n🎊 所有账号轮次抽奖执行完成!")


if __name__ == '__main__':
    main()
