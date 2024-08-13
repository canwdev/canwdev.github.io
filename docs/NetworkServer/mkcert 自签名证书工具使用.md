## 下载安装

- 下载最新版本 [Releases · FiloSottile/mkcert](https://github.com/FiloSottile/mkcert/releases)
- 把可执行文件放到 PATH 路径中
## 创建并安装证书（Node.js 示例）

```bash
mkdir test-cert && cd test-cert

# 创建证书
mkcert app.local "*.app.local" localhost 127.0.0.1 ::1

# 自动安装证书到系统
mkcert -install
```

Windows 检查证书是否安装：
- win+r 运行 `certmgr.msc`
- 在 `受信任的根证书颁发机构 > 证书` 下，可以找到 `mkcert` 开头的证书，说明安装成功

在当前目录初始化 nodejs 示例项目
```bash
yarn init -y
yarn add express
```

创建 index.js
```js
const express = require('express');
const https = require('https');
const fs = require('fs');
const path = require('path');

// 创建 Express 应用
const app = express();

// 读取证书和私钥文件
const certPath = path.join(__dirname, './app.local+4.pem');
const keyPath = path.join(__dirname, './app.local+4-key.pem');

const options = {
    key: fs.readFileSync(keyPath),
    cert: fs.readFileSync(certPath)
};

// 设置一个示例路由
app.get('/', (req, res) => {
    res.send('Hello, this is a secure server!');
});

// 创建 HTTPS 服务器
const httpsServer = https.createServer(options, app);

// 启动 HTTPS 服务器
const PORT = 3000; // 你可以选择其他端口
httpsServer.listen(PORT, () => {
    console.log(`HTTPS Server is running on https://localhost:${PORT}`);
});
```

启动服务：`node index.js`