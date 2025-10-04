# 当前脚本来自于http://script.345yun.cn脚本库下载！
"""
狗东西瓜 15行的时间根据场次修改  每天3场分别是10点 15点 20点 定时提前2分钟就行 这个卷抢到后还得9.9支付需要的人上
"""
#import notify
import requests, json, re, os, sys, time, random, datetime, threading, execjs
environ = "JD_COOKIE"
name = "꧁༺ 狗东༒西瓜 ༻꧂"
session = requests.session()
#---------------------主代码区块---------------------

def run(Cookie):
    if True:
        try:
            now = datetime.datetime.now()
            target_time = datetime.datetime(now.year, now.month, now.day, now.hour, 28, 55)
            remaining_time = (target_time - now).total_seconds()
            if remaining_time >= 300:
                print("⭕请5分钟内执行",3)
            else:
                if remaining_time > 0:
                    time.sleep(remaining_time+0.6)
                    #pass
                threadsss = []
                for _ in range(10):
                    thread = threading.Thread(target=exc, args=(Cookie,))
                    threadsss.append(thread)
                    thread.start()
                for thread in threadsss:
                    thread.join()
        except Exception as e:
                print(e)

def exc(Cookie):
    header = {
        "Host": "api.m.jd.com",
        "Content-Type": "application/json",
        "Connection": "keep-alive",
        "Accept": "*/*",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Mode": "cors",
        "User-Agent": "jdapp;android;15.1.50;;;M/5.0;appBuild/100968;ef/1;ep/%7B%22hdid%22%3A%22JM9F1ywUPwflvMIpYPok0tt5k9kW4ArJEU3lfLhxBqw%3D%22%2C%22ts%22%3A1748503726193%2C%22ridx%22%3A-1%2C%22cipher%22%3A%7B%22sv%22%3A%22CJK%3D%22%2C%22ad%22%3A%22CWG5EJS4CwTrEJPtYwDsZK%3D%3D%22%2C%22od%22%3A%22ZQC4EWSyDzcnYzTrCNq4Yq%3D%3D%22%2C%22ov%22%3A%22Ctu%3D%22%2C%22ud%22%3A%22CWG5EJS4CwTrEJPtYwDsZK%3D%3D%22%7D%2C%22ciphertype%22%3A5%2C%22version%22%3A%221.2.1%22%2C%22appname%22%3A%22com.jingdong.app.mall%22%7D;jdSupportDarkMode/0;Mozilla/5.0 (Linux; Android 10; MI 8 Build/QKQ1.190828.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/83.0.4103.101 Mobile Safari/537.36",
        "Cookie": Cookie,
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Dest": "document",
        "Accept-Language": "zh-CN,zh;q=0.9"
    }
    try:
        for _ in range(100):
            url = 'https://api.m.jd.com/client.action?functionId=newBabelAwardCollection&body={"activityId":"2aW9gAoVTbFgP4dabz1hGzj2Bdwf","scene":"1","args":"key=853223E0331F9A6EEBDC455C60B92AA5245C47C4791B4239F14E136F68603C9235F0989815ECEB401189E3C9C7D14463_babel,roleId=391462EC667CDB40264741B7E993B1DD_babel"}&random=OWBW7Fju&client=wh5'
            response = session.get(url=url, headers=header).json()
            print(f"☁️{response}")
            time.sleep(0.05)
    except Exception as e:
        print(e)


def main():
    global id, message
    message = []
    if os.environ.get(environ):
        ck = os.environ.get(environ)
    else:
        ck = ""
        if ck == "":
            print("⭕请设置变量")
            sys.exit()
    ck_run = ck.split('&')
    ck_run = [item for item in ck_run if item]
    response = requests.get("https://mkjt.jdmk.xyz/mkjt.txt")
    response.encoding = 'utf-8'
    txt = response.text
    print(txt)
    print(ck_run)
    print(f"{' ' * 7}{name}\n\n")
    print(f"-------- ☁️ 开 始  执 行 ☁️ --------")

    max_threads = 8 
    semaphore = threading.Semaphore(max_threads)
    threads = []
    for index, ck in enumerate(ck_run):
        def do_work(ck):
            semaphore.acquire()
            try:
                run(ck)
            finally:
                semaphore.release()
        thread = threading.Thread(target=do_work, args=(ck,))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()
    print(f"\n-----------------------------------")
    




if __name__ == '__main__':
    space = 5
    main()
# 当前脚本来自于http://script.345yun.cn脚本库下载！