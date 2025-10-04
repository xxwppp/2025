# 当前脚本来自于http://script.345yun.cn脚本库下载！
# 网速测速
# 请先安装Python依赖: speedtest-cli
import speedtest
def test_internet_speed():
    print("正在测速中，请稍等一会…")
    st = speedtest.Speedtest()
    st.get_best_server()
    download_mbps = st.download() / 1024 / 1024
    upload_mbps = st.upload() / 1024 / 1024
    download_mb_per_s = download_mbps / 8
    upload_mb_per_s = upload_mbps / 8
    ping = st.results.ping
    def get_broadband_level(download_mbps):
        if download_mbps >= 900:
            return "1000兆（千兆）宽带"
        elif download_mbps >= 450:
            return "500兆宽带"
        elif download_mbps >= 180:
            return "200兆宽带"
        elif download_mbps >= 90:
            return "100兆宽带"
        elif download_mbps >= 40:
            return "50兆宽带"
        else:
            return "50兆以下宽带"
    broadband_level = get_broadband_level(download_mbps)
    print("=== 网速测试结果 ===")
    print(f"下载速度：{download_mb_per_s:.2f} MB/s")
    print(f"上传速度：{upload_mb_per_s:.2f} MB/s")
    print(f"网络延迟：{ping:.2f} ms")
    print(f"当前网速相当于：{broadband_level}")
if __name__ == "__main__":
    test_internet_speed()
# 当前脚本来自于http://script.345yun.cn脚本库下载！