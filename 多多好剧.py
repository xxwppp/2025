# 当前脚本来自于http://script.345yun.cn脚本库下载！
import requests
import random
import requests
import json
import time



while True:

# 生成随机延迟时间
  delay = random.uniform(0.2, 0.5)  # 设置延迟时间范围，单位为秒

# 执行延迟
  time.sleep(delay)
# 多个变量的列表
  variables = ['addRedBag=1&desc=task&em=1&num=400&sign=HNlMTzoFXgTXmOYdwrIbneeCaw5IKM1HrZQn5pvigWw0fuKrKmdNSs79A/lgmXoMbNx5azgCNrf3XfiUaLubTg%3D%3D','addRedBag=1&desc=task&em=1&num=400&sign=HNlMTzoFXgTXmOYdwrIbneeCaw5IKM1HrZQn5pvigWw0fuKrKmdNSs79A/lgmXoMbNx5azgCNrf3XfiUaLubTg%3D','addRedBag=1&desc=task&em=1&num=400&sign=HNlMTzoFXgTXmOYdwrIbneeCaw5IKM1HrZQn5pvigWw0fuKrKmdNSs79A/lgmXoMbNx5azgCNrf3XfiUaLubTg']
# 使用random.sample()函数从列表中随机选择3个不同的变量
  random_variables = random.sample(variables, 1)
# 打印随机选择的变量
  for variable in random_variables:
    print("当前随机请求值:" + str(variable))
    print("正在刷金币！返回json则成功： \n")



  url = "https://bp-api.hainanshaoying.com/bubuduo-hjttk/ad/lookVideo"

  payload = variable

  headers = {
  'User-Agent': "ddhj/1.0.1 (iPhone; iOS 16.6; Scale/3.00)",
  'Content-Type': "application/x-www-form-urlencoded",
  'appId': "填你的",
  'userId': "填你的",
  'brand': "Apple",
  'channel': "AppStore",
  'appVersion': "1.0.1",
  'appPkgName': "com.ys.ddhj",
  'pkgId': "664",
  'romVersion': "16.6",
  'os': "iOS",
  'accessKey': "填你的",
  'deviceId': "0000-0000-0000-0000",
  'Accept-Language': "zh-Hans-CN;q=1",
  'model': "iPhone15,3",
  'product': "hjttk",
  'osVersion': "16.6",
  'gps': "default"
  }

  response = requests.post(url, data=payload, headers=headers)

  print(response.text)

  print("\n\n")
# 生成随机延迟时间
  delay = random.uniform(0.2, 0.5)  # 设置延迟时间范围，单位为秒

# 执行延迟
  time.sleep(delay)


# 当前脚本来自于http://script.345yun.cn脚本库下载！