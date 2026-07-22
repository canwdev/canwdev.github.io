## 下载安装 mkcert

- 下载最新版本 [Releases · FiloSottile/mkcert](https://github.com/FiloSottile/mkcert/releases)
- 把可执行文件放到 PATH 路径中
## 创建并安装证书

```bash
# 创建证书，支持 *.app.local localhost、127.0.0.1、::1 等多个域名和IP地址
# 注意：如果使用其他IP地址，需要手动添加到下面
mkcert app.local "*.app.local" localhost 127.0.0.1 ::1

# 自动安装证书到系统
mkcert -install

# 卸载证书
mkcert -uninstall
```

## Windows 检查证书是否安装：

- win+r 运行 `certmgr.msc`
- 在 `受信任的根证书颁发机构 > 证书` 下，可以找到 `mkcert` 开头的证书，说明安装成功

## 在目标计算机上信任证书

参考 [Installing the CA on other systems](https://github.com/FiloSottile/mkcert?tab=readme-ov-file#installing-the-ca-on-other-systems)

1. 在本机运行 `mkcert -CAROOT` 打开证书目录，获取 `rootCA.pem` 文件
2. 在目标计算机运行 `mkcert -CAROOT` 打开证书目录
3. 复制本机 `rootCA.pem` 文件到目标计算机的证书目录下
4. 在目标计算机上运行 `mkcert -install`

 请勿在生产环境中使用自签名证书


## 示例：在 Express 中使用 https

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