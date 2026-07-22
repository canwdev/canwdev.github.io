> 参考教程：[自建远程桌面连接服务，RustDesk搭建教程 - 雨月空间站](https://www.mintimate.cn/2023/08/27/guideToHostRustDesk/)

### 1. 下载

首先下载客户端和服务端，服务端安装在任意一台机器上，客户端两台机器都要安装，两台机器必须可以通过（局域网）网络访问

- [客户端 · rustdesk/rustdesk](https://github.com/rustdesk/rustdesk/releases)
- [服务端 · rustdesk/rustdesk-server](https://github.com/rustdesk/rustdesk-server/releases)

### 2. 启动服务端

首先启动服务端，服务端包含两个可执行文件，两个服务都需要启动。
- `hbbs` RustDesk的ID服务，用于分配和注册ID
- `hbbr` RustDesk的中继服务
服务启动后会自动生成密钥文件，其中 `id_ed25519.pub` 是公钥，也就是下面需要的 Key

使用 `ip a` 命令查看服务器地址，如 `192.168.xxx.xx`

### 3. 启动客户端

客户端安装好后，进行配置，进入【设置-网络】界面：
- ID 服务器：`192.168.xxx.xx`
- 中继服务器：`192.168.xxx.xx`
- API服务器：不用填写
- Key：填写 `id_ed25519.pub` 的内容

所有客户端都要进行如上设置

### 4. 连接

在客户端的【主页】，复制 ID，在另一个客户端粘贴 ID 即可进行远程连接