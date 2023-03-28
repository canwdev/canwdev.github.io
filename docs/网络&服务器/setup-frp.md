官方文档：https://github.com/fatedier/frp/blob/master/README_zh.md


## 服务器端 · frps

到Github上[下载](https://github.com/fatedier/frp/releases)对应的版本，解压到例如`/usr/www/frp`文件夹下：

```sh
wget https://github.com/fatedier/frp/releases/download/v0.25.3/frp_0.25.3_linux_amd64.tar.gz
tar xzvf frp_0.25.3_linux_amd64.tar.gz
mv frp_0.25.3_linux_amd64 frp
```

修改`frps.ini`，直接运行`./frps -c frpc.ini`即可启动成功

附上`frps.ini`基础配置内容

```
[common]
bind_port = 7000

# dashboard_addr = 0.0.0.0
# dashboard_port = 7500

# 仪表盘访问的用户名密码，如果不设置，则默认都是 admin
# dashboard_user = admin
# dashboard_pwd = admin

# auth token
token = abcd1234567890
```

## frps 守护服务、开机启动：systemd/systemctl 配置

https://blog.xinshangshangxin.com/2018/06/18/frp/

添加 `/etc/systemd/system/frps.service`

```sh
[Unit]
Description=frps
After=network.target

[Service]
TimeoutStartSec=30
ExecStart=/usr/www/frp/frps -c /usr/www/frp/frps.ini
ExecStop=/bin/kill $MAINPID

[Install]
WantedBy=multi-user.target
```

```sh
# 启动服务
systemctl start frps
# 查看状态
systemctl status frps
# 开机启动
systemctl enable frps
```

## 客户端 · frpc

运行`frpc -c frpc.ini`可启动客户端服务，

* windows可使用[NSSM](./windows-setup-mongodb.md)来实现自动运行服务

### frpc 守护服务、开机启动：systemd/systemctl 配置

添加 `/etc/systemd/system/frpc.service`

```sh
[Unit]
Description=frpc daemon
After=syslog.target  network.target
Wants=network.target

[Service]
Type=simple
ExecStart=/usr/www/frp/frpc -c /usr/www/frp/frpc.ini
Restart= always
RestartSec=1min
ExecStop=/bin/kill $MAINPID

[Install]
WantedBy=multi-user.target
```


### 附上`frpc.ini`内容

```
[common]
server_addr = 47.xxx.xxx.xxx 
server_port = 7000
# auth token
token = abcd1234567890


[web]
type = tcp
local_ip = 127.0.0.1
local_port = 80
remote_port = 8080

[ftp]
type = tcp
local_ip = 127.0.0.1
local_port = 21
remote_port = 8082

[ftp_port1]
type = tcp
local_ip = 127.0.0.1
local_port = 5100
remote_port = 5100


[ftp_port2]
type = tcp
local_ip = 127.0.0.1
local_port = 5101
remote_port = 5101


[ftp_port3]
type = tcp
local_ip = 127.0.0.1
local_port = 5102
remote_port = 5102

[rdp]
type = tcp
local_ip = 127.0.0.1
local_port = 3389
remote_port = 3389

[ssh]
type = tcp
local_ip = 127.0.0.1
local_port = 22
remote_port = 2222
use_encryption = true
use_compression = false
```
