// 当前脚本来自于http://script.345yun.cn脚本库下载！
"ui";

// =================  0. 参数区  =================
const PORT        = 8080;          // 网页端口
const QUALITY     = 60;            // JPEG 质量 1-100
const SCALE       = 0.4;           // 缩放比例，越小越流畅
const FPS         = 8;             // 目标帧率
const SWIPE_TIME  = 300;           // 滑动手势时长 ms

// =================  1. 布局  =================
ui.layout(
    <vertical>
        <button id="btnStart" text="启动投屏服务" w="*" h="60"/>
        <text textSize="12" textColor="#999999" text="运行后在本机浏览器访问 http://手机IP:8080"/>
        <text id="tip" textSize="14" textColor="#ff5722" text=""/>
    </vertical>
);

// =================  2. HTTP 服务  =================
let server = null;
ui.btnStart.click(() => {
    threads.start(function () {
        try {
            server = http.createServer((req, res) => {
                let url = req.url;
                if (url === '/') {                       // 主页
                    res.statusCode = 200;
                    res.headers['Content-Type'] = 'text/html;charset=utf-8';
                    res.write(getHtml());
                    res.end();
                } else if (url === '/screen.mjpeg') {    // MJPEG 流
                    res.statusCode = 200;
                    res.headers['Content-Type'] = 'multipart/x-mixed-replace;boundary=frame';
                    let id = setInterval(() => {
                        let img = captureScreen();
                        let base64 = images.toBase64(img, 'jpg', QUALITY);
                        res.write('--frame\r\nContent-Type: image/jpeg\r\n\r\n');
                        res.write(java.lang.String(base64).getBytes('utf-8'));
                        res.write('\r\n');
                        img.recycle();
                    }, 1000 / FPS);
                    res.on('close', () => clearInterval(id));
                } else if (url.startsWith('/cmd')) {     // 控制指令
                    handleCmd(url);
                    res.statusCode = 204;
                    res.end();
                } else {
                    res.statusCode = 404;
                    res.end();
                }
            }).listen(PORT);
            ui.run(() => ui.tip.setText(`服务已启动！\n局域网访问 http://${getIp()}:${PORT}`));
        } catch (e) {
            console.log(e)
            ui.run(() => ui.tip.setText('端口被占用或权限不足'));
        }
    });
});

events.on('exit', () => server && server.close());

// =================  3. 控制指令解析  =================
function handleCmd(url) {
    let q = parseQuery(url);
    switch (q.act) {
        case 'back':
            back();
            break;
        case 'home':
            home();
            break;
        case 'recents':
            recents();
            break;
        case 'tap':
            click(parseInt(q.x), parseInt(q.y));
            break;
        case 'swipe':
            swipe(parseInt(q.x1), parseInt(q.y1), parseInt(q.x2), parseInt(q.y2), SWIPE_TIME);
            break;
        case 'input':
            let txt = decodeURIComponent(q.txt || '');
            setClip(txt);
            toast('已复制到剪贴板，可手动粘贴');
            break;
    }
}

// =================  4. 工具函数  =================
function parseQuery(url) {
    let obj = {};
    url.replace(/([^?&=]+)=([^&]*)/g, (_, k, v) => obj[k] = v);
    return obj;
}

function getIp() {
    let ifs = java.net.NetworkInterface.getNetworkInterfaces();
    while (ifs.hasMoreElements()) {
        let adr = ifs.nextElement().getInetAddresses();
        while (adr.hasMoreElements()) {
            let ip = adr.nextElement();
            if (!ip.isLoopbackAddress() && ip.getHostAddress().indexOf(':') < 0)
                return ip.getHostAddress();
        }
    }
    return '127.0.0.1';
}

// =================  5. 网页前端  =================
function getHtml() {
    return `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<title>Auto.js 网页投屏控制</title>
<style>
body{margin:0;background:#111;color:#eee;font-family:Arial;}
#screen{width:100%;max-width:600px;border:1px solid #444;}
.ctrl{padding:10px;}
button{margin:4px;padding:6px 12px;}
#log{height:60px;overflow:auto;background:#222;font-size:12px;padding:4px;}
</style>
</head>
<body>
<div class="ctrl">
    <button onclick="send('back')">返回</button>
    <button onclick="send('home')">主页</button>
    <button onclick="send('recents')">多任务</button>
    <input id="txt" placeholder="输入文字" size="15"/>
    <button onclick="send('input&txt='+encodeURIComponent(document.getElementById('txt').value))">发送</button>
</div>
<img id="screen" src="/screen.mjpeg"/>
<div id="log">实时画面加载中…</div>
<script>
const screen = document.getElementById('screen');
screen.onload = () => log('画面已连接');
screen.onclick = e => {
    let rect = screen.getBoundingClientRect();
    let x = Math.round(e.offsetX * screen.naturalWidth / rect.width);
    let y = Math.round(e.offsetY * screen.naturalHeight / rect.height);
    send('tap&x='+x+'&y='+y);
};
let startX,startY;
screen.onmousedown = e => { startX=e.offsetX; startY=e.offsetY; };
screen.onmouseup = e => {
    let rect = screen.getBoundingClientRect();
    let x1 = Math.round(startX * screen.naturalWidth / rect.width);
    let y1 = Math.round(startY * screen.naturalHeight / rect.height);
    let x2 = Math.round(e.offsetX * screen.naturalWidth / rect.width);
    let y2 = Math.round(e.offsetY * screen.naturalHeight / rect.height);
    if(Math.abs(x2-x1)>20||Math.abs(y2-y1)>20) send('swipe&x1='+x1+'&y1='+y1+'&x2='+x2+'&y2='+y2);
};
function send(q){
    fetch('/cmd?act='+q).then(()=>log('已执行: '+q));
}
function log(msg){
    let d=document.getElementById('log');
    d.innerHTML=msg+'<br/>'+d.innerHTML;
}
</script>
</body>
</html>`;
}

// 当前脚本来自于http://script.345yun.cn脚本库下载！