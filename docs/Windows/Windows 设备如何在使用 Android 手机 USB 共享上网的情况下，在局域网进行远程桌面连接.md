
Android 手机(服务端) USB 共享上网的 Windows 设备(客户端) 会被分配到一个Android内网的地址，如：`192.16.48.2`，但 Android 手机所在的局域网ip往往是 `192.168.0.3` 。这样就造成了无法直接访问  Windows 客户端的问题。

通过使用 `frp` ([[setup-frp]]) 内网穿透工具，我们可以很方便地解决这个问题。

首先在要使用远程桌面的客户端（我们正在使用的电脑）上配置 `frps.ini`
```
[common]
bind_port = 7000

# auth token
token = abcd1234567890
```

然后在要被控制的 Windows 设备上配置 `frpc.ini`
假设我们正在使用的电脑 ip 是 `192.168.0.2`，下述 `server_addr` 就填写这个地址。

```
[common]
server_addr = 192.168.0.2
server_port = 7000
# auth token
token = abcd1234567890

[rdp]
type = tcp
local_ip = 127.0.0.1
local_port = 3389
remote_port = 13389
```

- 然后在服务端启动服务：`.\frps.exe -c .\frps.ini`
- 在客户端启动服务：`.\frpc.exe -c .\frpc.ini`

这样就可以在我们正在使用的电脑上运行 `mstsc` ，并且输入地址：`192.168.0.2:13389` 进行愉快的远程桌面连接了。如果你想免密码连接，参考 [[RDP 使用空密码登录]]

