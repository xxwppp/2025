# 当前脚本来自于http://script.345yun.cn脚本库下载！
"""
 作者:  Echo
 日期:  2024/11/27
 小程序:  北京社服
 功能:  签到、答题、抽奖等
 变量:  bjsf_wxid_data (微信id) 多个账号用换行分割 
        PROXY_API_URL (代理api，返回一条txt文本，内容为代理ip:端口)
 定时:  一天三次
 cron:  0 8,14,17 * * *
 更新日志：
 2024/11/27  V1.0 初始化脚本
 2025/7/7   V1.1 使用wex_get模块统一微信授权接口
"""
import requests, json, re, os, sys, time, random, datetime
# 导入wex_get模块中的wx_code_auth方法
from wex_get import wx_code_auth

def get_wxapp_code(wxid, appid="wx8ac1f54b8fc39c6c"):
    """
    通过wex_get模块获取小程序code
    Args:
        wxid (str): 微信ID
        appid (str): 小程序的appid，默认北京社服
    Returns:
        dict: 请求结果，包含success字段和提取的code
    """
    try:
        code = wx_code_auth(wxid, appid)
        if code:
            return {
                'success': True,
                'data': {"code": code},
                'extracted_code': code
            }
        else:
            print("❌ 获取code失败")
            return {
                'success': False,
                'error': '获取code失败',
                'extracted_code': None
            }
    except Exception as e:
        print(f"❌ 获取code异常: {str(e)}")
        return {
            'success': False,
            'error': f'获取code异常: {str(e)}',
            'extracted_code': None
        }

environ = "bjsf"
name = "北京༒社服"

def handle_compressed_response(response, request_name=""):
    """
    处理响应数据
    Args:
        response: requests.Response对象
        request_name: 请求名称，用于错误信息
    Returns:
        dict: 解析后的JSON数据，失败时返回None
    """
    try:
        # 检查Content-Encoding头
        content_encoding = response.headers.get('content-encoding', '').lower()
        if content_encoding:
            print(f"{request_name}检测到压缩数据: {content_encoding}")
            
            # 如果仍然收到压缩数据，尝试解压缩
            if content_encoding == 'br':
                try:
                    import brotli
                    print(f"原始数据长度: {len(response.content)} 字节")
                    decompressed_data = brotli.decompress(response.content)
                    text_data = decompressed_data.decode('utf-8')
                    print(f"Brotli解压缩成功，数据长度: {len(text_data)} 字符")
                    return json.loads(text_data)
                except Exception as brotli_err:
                    print(f"❌ Brotli解压缩失败: {brotli_err}")
                    return None
            else:
                # gzip和deflate由requests自动处理
                try:
                    return response.json()
                except json.JSONDecodeError as json_err:
                    print(f"❌ {request_name}解压缩后JSON解析失败: {json_err}")
                    print(f"响应内容: {response.text[:200]}...")
                    return None
        else:
            # 未压缩数据
            try:
                return response.json()
            except json.JSONDecodeError as json_err:
                print(f"❌ {request_name}JSON解析失败: {json_err}")
                print(f"响应内容: {response.text[:200]}...")
                return None
    except Exception as e:
        print(f"❌ {request_name}响应处理异常: {e}")
        return None

#---------------------主代码区块---------------------
def request_chatgpt_function(question):
    model = "lite"
    url = "https://spark-api-open.xf-yun.com/v1/chat/completions"
    APIPassword = "UMhCtGWNOXbgQLOdJtNH:msLSYQCtyTjlhLADKyYd"

    header = {"Content-Type": "application/json", "Authorization": f"Bearer {APIPassword}"}
    prompt = "你是知识渊博的助理。"
    data={"model": model,"messages": [{"role": "system","content": prompt},{"role": "user","content": f"{question}；请给出答案，只要字母"}],"temperature": 0}
    response = requests.post(url=url, headers=header, json=data).json()
    if response.get('choices'):
        result = response['choices'][0]['message']['content']
        # 使用正则表达式提取第一个大写字母，答题专用
        match = re.search(r'[A-D]', result)
        if match:
            result = match.group()
        else:
            return False
        #print(result)
        return result
    else:
        print(response)
        return False

def run(token=None):
    try:
        header = {
            "xweb_xhr": "1",
            "x-token": token,
            "project-name": "xld",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090c33)XWEB/14185",
            "content-type": "application/json;charset=UTF-8",
            "accept": "*/*",
            "sec-fetch-site": "cross-site",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": "https://servicewechat.com/wx8ac1f54b8fc39c6c/16/page-frame.html",
            "accept-encoding": "identity",  # 明确要求不压缩
            "accept-language": "zh-CN,zh;q=0.9",
            "priority": "u=1, i"
        }
        
        # 1. 获取用户信息
        try:
            url = 'https://ylapi.luckystarpay.com/api/getUserInfo'
            response = requests.post(url=url, headers=header, json={})
            print(f"响应状态码: {response.status_code}")
            
            # 检查响应状态码
            if response.status_code != 200:
                print(f"❌ HTTP错误: {response.status_code}")
                return
                
            # 使用通用函数处理响应
            response_data = handle_compressed_response(response, "获取用户信息")
            if response_data is None:
                return
                    
            userInfo = response_data["data"]["userInfo"]
            print(f"☁️{userInfo['nickname']}：{userInfo['levelName']}")
        except requests.exceptions.RequestException as req_err:
            print(f"❌ 网络请求失败: {req_err}")
            return
        except Exception as e:
            print(f"❌ 获取用户信息失败: {e}")
            return
            
        # 2. 用户签到
        try:
            url = 'https://ylapi.luckystarpay.com/api/userSign'
            response = requests.post(url=url, headers=header, json={})
            
            if response.status_code != 200:
                print(f"❌ 签到请求HTTP错误: {response.status_code}")
                return
                
            # 使用通用函数处理响应
            response_data = handle_compressed_response(response, "用户签到")
            if response_data is None:
                return
                
            if "已签到" in response_data["message"] or "ok" in response_data["message"]:
                print("☁️签到状态：已签到")
        except requests.exceptions.RequestException as req_err:
            print(f"❌ 签到网络请求失败: {req_err}")
        except Exception as e:
            print(f"❌ 用户签到失败: {e}")
            
        # 3. 获取首页活动列表
        try:
            url = 'https://ylapi.luckystarpay.com/api/home'
            response = requests.post(url=url, headers=header, json={})
            
            if response.status_code != 200:
                print(f"❌ 获取首页活动列表HTTP错误: {response.status_code}")
                activity_list = []
                return
                
            # 使用通用函数处理响应
            response_data = handle_compressed_response(response, "获取首页活动列表")
            if response_data is None:
                activity_list = []
                return
                
            # print(response_data)
            activity_list = response_data.get("data", {}).get("activity", [])
            if not isinstance(activity_list, list):
                activity_list = []
        except requests.exceptions.RequestException as req_err:
            print(f"❌ 获取首页活动列表网络请求失败: {req_err}")
            activity_list = []
        except Exception as e:
            print(f"❌ 获取首页活动列表失败: {e}")
            activity_list = []
            
        for i in activity_list:
            statusView = i.get("statusView", "")
            next = False
            if "进行中" in statusView:
                id = i.get("id")
                # # 健壮处理title
                title = i.get("title", "")
                # titlestart, titleend = "", ""
                # try:
                #     title_split = title.split("·")[0].split("｜")
                #     print(title_split)
                #     if len(title_split) > 1:
                #         titlestart = title_split[1].rsplit("第", 2)[-2][:3] if len(title_split[1].rsplit("第", 2)) > 1 else title_split[1]
                #         titleend = title_split[1].rsplit("第", 2)[-1] if len(title_split[1].rsplit("第", 2)) > 1 else ""
                # except Exception as e:
                #     print(f"title解析异常: {e}, title={title}")
                print(f"\n---{title}---\n☁️开 始 静 默 答 题")
                for m in range(5):
                    for n in range(20):
                        if n == 0:
                            url = "https://ylapi.luckystarpay.com/api/v2/startAnswer"
                            data = {"id": id}
                        else:
                            url = "https://ylapi.luckystarpay.com/api/v2/getQuestion"
                            data = {"id": id, "examId": examId, "number": n + 1}
                        aa=random.randint(30, 40)
                        print(f"等待:{aa}秒")
                        time.sleep(aa)
                        
                        # 4. 开始答题或获取题目
                        try:
                            response = requests.post(url=url, headers=header, json=data)
                            
                            if response.status_code != 200:
                                print(f"❌ 答题请求HTTP错误 (第{n+1}题): {response.status_code}")
                                break
                                
                            # 使用通用函数处理响应
                            response_data = handle_compressed_response(response, f"答题请求(第{n+1}题)")
                            if response_data is None:
                                break
                                
                            print(response_data)
                        except requests.exceptions.RequestException as req_err:
                            print(f"❌ 答题网络请求失败 (第{n+1}题): {req_err}")
                            break
                        except Exception as e:
                            print(f"❌ 答题请求失败 (第{n+1}题): {e}")
                            break
                            
                        if "用户未认证或未添加企微" in response_data.get("message", ""):
                            print(f"⭕未认证或未添加企微")
                            next = True
                            break
                        elif "此活动参与次数已达上限" in response_data.get("message",""):
                            print(f"⭕活动参与次数已上限")
                            next = True
                            break
                        else:
                            try:
                                explain = response_data["data"]["question"]["explain"] # 答案
                                body = response_data["data"]["question"]["body"]  # 问题
                                options=""
                                for op in response_data["data"]["question"]["options"]:  #选项
                                    label=op["label"]  # A OR B
                                    value=op["value"] # 选项内容
                                    options=f"{options} {label}:{value}"
                                quest=f"以下是题目:{body}；题目的提示:{explain}；题目的选项:{options}，请输出答案"
                                # print(quest)
                                # answer=request_chatgpt_function(quest) # 让ai给答案
                                answer=response_data["data"]["question"]["answer"]
                                if not answer:
                                    return
                                if n == 0:
                                    examId = response_data["data"]["examId"]
                                    
                                # 5. 提交答案
                                try:
                                    url = "https://ylapi.luckystarpay.com/api/submitAnswer"
                                    data = {"examId": examId, "id": id, "answer": answer, "number": n + 1}
                                    response = requests.post(url=url, headers=header, json=data)
                                    
                                    if response.status_code != 200:
                                        print(f"❌ 提交答案HTTP错误 (第{n+1}题): {response.status_code}")
                                        break
                                        
                                    # 使用通用函数处理响应
                                    submitAnswer = handle_compressed_response(response, f"提交答案(第{n+1}题)")
                                    if submitAnswer is None:
                                        break
                                        
                                    print(f"第{n + 1}题回答：{answer}答题结果：", submitAnswer["data"]["isCorrect"])
                                except requests.exceptions.RequestException as req_err:
                                    print(f"❌ 提交答案网络请求失败 (第{n+1}题): {req_err}")
                                    break
                                except Exception as e:
                                    print(f"❌ 提交答案失败 (第{n+1}题): {e}")
                                    break
                                    
                            except Exception as e:
                                print(f"❌ 解析题目数据失败 (第{n+1}题): {e}")
                                break
                                
                        try:
                            questionNum = response_data["data"]["questionNum"] # 答题数量
                            if int(questionNum)-1==n:
                                break
                        except Exception as e:
                            print(f"❌ 获取题目数量失败: {e}")
                            break
                            
                        time.sleep(random.randint(1, 2))
                    if next:
                        print("退出答题")
                        break
                    else:
                        # 6. 交卷
                        try:
                            url = "https://ylapi.luckystarpay.com/api/v2/submitExam"
                            data = {"id":id,"examId":examId}
                            response = requests.post(url=url, headers=header, json=data)
                            
                            if response.status_code != 200:
                                print(f"❌ 交卷HTTP错误: {response.status_code}")
                                break
                                
                            # 使用通用函数处理响应
                            response_data = handle_compressed_response(response, "交卷")
                            if response_data is None:
                                break
                                
                            print(f"交卷：{response_data['message']}")
                        except requests.exceptions.RequestException as req_err:
                            print(f"❌ 交卷网络请求失败: {req_err}")
                            break
                        except Exception as e:
                            print(f"❌ 交卷失败: {e}")
                            break
                            
                        # 7. 获取交卷结果
                        try:
                            url = "https://ylapi.luckystarpay.com/api/examResult"
                            data = {"id":id,"examId":examId}
                            response = requests.post(url=url, headers=header, json=data)
                            
                            if response.status_code != 200:
                                print(f"❌ 获取交卷结果HTTP错误: {response.status_code}")
                                continue
                                
                            # 使用通用函数处理响应
                            response_data = handle_compressed_response(response, "获取交卷结果")
                            if response_data is None:
                                continue
                                
                            print(f"交卷结果：{response_data['message']}")
                        except requests.exceptions.RequestException as req_err:
                            print(f"❌ 获取交卷结果网络请求失败: {req_err}")
                        except Exception as e:
                            print(f"❌ 获取交卷结果失败: {e}")
                            
                        # 8. 抽奖
                        try:
                            url = "https://ylapi.luckystarpay.com/api/lottery"
                            data = {"id":id,"examId":examId}
                            for _ in range(5):
                                try:
                                    response = requests.post(url=url, headers=header, json=data)
                                    
                                    if response.status_code != 200:
                                        print(f"❌ 抽奖HTTP错误: {response.status_code}")
                                        break
                                        
                                    # 使用通用函数处理响应
                                    response_data = handle_compressed_response(response, "抽奖")
                                    if response_data is None:
                                        break
                                    
                                    # print(response_data)
                                    
                                    try:
                                        isCanAgain = response_data["data"]["isCanAgain"]
                                        isWin = response_data["data"]["isWin"]
                                        if isWin:
                                            money = response_data["data"]["money"]
                                            print(f"🌈抽奖结果：{money} 现金")
                                        else:
                                            #print(f'⭕抽奖结果：未中奖呦')
                                            pass
                                        if not isCanAgain:
                                            break
                                    except Exception as e:
                                        if response_data.get("code")==500:
                                            print(response_data.get("message", "未知错误"))
                                            break
                                        print(f'⭕抽奖异常:{e}')
                                except requests.exceptions.RequestException as req_err:
                                    print(f"❌ 抽奖网络请求失败: {req_err}")
                                    break
                                except Exception as e:
                                    print(f"❌ 抽奖请求失败: {e}")
                                    break
                                time.sleep(30)
                        except Exception as e:
                            print(f"❌ 抽奖流程异常: {e}")
                            
        # 9. 获取用户信息和活动记录
        try:
            url = 'https://ylapi.luckystarpay.com/api/getUserInfo'
            response = requests.post(url=url, headers=header, json={})
            
            if response.status_code != 200:
                print(f"❌ 获取用户信息HTTP错误: {response.status_code}")
                totalMoney = 0
            else:
                response_data = handle_compressed_response(response, "获取用户信息")
                if response_data is None:
                    totalMoney = 0
                else:
                    try:
                        totalMoney = response_data["data"]["userInfo"]['totalMoney']
                        print(totalMoney)
                    except Exception as e:
                        print(f"❌ 解析用户信息失败: {e}")
                        totalMoney = 0
                    
            url = 'https://ylapi.luckystarpay.com/api/getUserActivity'
            response = requests.post(url=url, headers=header, json={"page":1})
            
            if response.status_code != 200:
                print(f"❌ 获取用户活动记录HTTP错误: {response.status_code}")
                items = []
                money = 0
            else:
                response_data = handle_compressed_response(response, "获取用户活动记录")
                if response_data is None:
                    items = []
                    money = 0
                else:
                    try:
                        print(response_data)
                        items = response_data["data"]["items"]
                        money = 0
                    except Exception as e:
                        print(f"❌ 解析用户活动记录失败: {e}")
                        items = []
                        money = 0
        except requests.exceptions.RequestException as req_err:
            print(f"❌ 获取用户信息和活动记录网络请求失败: {req_err}")
            items=[]
            money = 0
            totalMoney = 0
        except Exception as e:
            print(f"❌ 获取用户信息和活动记录失败: {e}")
            items=[]
            money = 0
            totalMoney = 0
            
        for i in items:
            try:
                endAt = i["endAt"]
                if datetime.datetime.fromtimestamp(endAt).day == datetime.datetime.now().day:
                    money = money + float(i["money"])
            except Exception as e:
                print(f"❌ 处理活动记录失败: {e}")
                continue
                
        print(f"--------------------\n☁️累计获得：{totalMoney}元\n🌈今日获得：{money:.1f}元")
    except Exception as e:
        print(f"❌ run函数主流程异常: {e}")

def main(wxid_list):
    for idx, wxid in enumerate(wxid_list):
        print(f"\n🎉 开始处理账号 {idx+1}/{len(wxid_list)}: {wxid}")
        # 1. 获取code
        code_result = get_wxapp_code(wxid)
        if not code_result.get('success') or not code_result.get('extracted_code'):
            print(f"❌ 获取code失败: {code_result.get('error')}")
            continue
        code = code_result['extracted_code']
        # 2. silenceLogin获取token
        url = "https://ylapi.luckystarpay.com/api/silenceLogin"
        headers = {
            "content-type": "application/json;charset=UTF-8",
            "project-name": "xld",
            "charset": "utf-8",
            "referer": "https://servicewechat.com/wx8ac1f54b8fc39c6c/16/page-frame.html",
            "user-agent": "Mozilla/5.0 (Linux; Android 10; Redmi Note 7 Build/QKQ1.190910.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/134.0.6998.136 Mobile Safari/537.36 XWEB/1340129 MMWEBSDK/20250201 MMWEBID/6160 MicroMessenger/8.0.60.2860(0x28003C55) WeChat/arm64 Weixin NetType/WIFI Language/zh_CN ABI/arm64 MiniProgramEnv/android",
            "accept-encoding": "gzip, deflate, br"
        }
        payload = {"code": code}
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=20)
            # print(resp.text)
            result = resp.json()
            token = result.get("data", {}).get("token")
            if not token:
                print(f"❌ silenceLogin未获取到token: {result}")
                continue
            # print(f"✅ silenceLogin获取token成功: {token}")
        except Exception as e:
            print(f"❌ silenceLogin请求异常: {e}")
            continue
        # 3. 业务主流程
        run(token)
    print(f'\n----------- 🎊 所有账号执行结束 🎊 -----------')

if __name__ == '__main__':
    # 从环境变量获取微信ID列表
    bjsf_wxid_data = os.getenv("bjsf_wxid_data")
    if not bjsf_wxid_data:
        print("❌ 未设置环境变量bjsf_wxid_data，请检查环境变量")
        exit(1)
    
    # 支持多种分隔符
    MULTI_ACCOUNT_SPLIT = ["\n", "@", "&"]
    split_char = None
    for sep in MULTI_ACCOUNT_SPLIT:
        if sep in bjsf_wxid_data:
            split_char = sep
            break
    
    if not split_char:
        # 如果都没有分隔符，默认当作单账号
        wxid_list = [bjsf_wxid_data]
    else:
        wxid_list = [x.strip() for x in bjsf_wxid_data.split(split_char) if x.strip()]
    
    print(f"获取到 {len(wxid_list)} 个账号")
    main(wxid_list)
# 当前脚本来自于http://script.345yun.cn脚本库下载！