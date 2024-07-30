> 系统环境：Ubuntu 24.04 LTS

## 安装环境

安装Xfce4桌面环境（安装很慢，请耐心等待）
```bash
sudo apt update
sudo apt install xfce4 xfce4-goodies
```

安装TigerVNC Server
```bash
sudo apt install tigervnc-standalone-server tigervnc-common
```

## 配置 VNC

配置vnc密码
```bash
vncpasswd
# 输入两遍密码，如：PAS3WorD
# Would you like to enter a view-only password (y/n)? 敲 n 回车
```

编辑启动配置
```bash
mkdir -p ~/.vnc
vim ~/.vnc/xstartup
```
填入以下内容：
```bash
#!/bin/sh
unset SESSION_MANAGER
unset DBUS_SESSION_BUS_ADDRESS
exec startxfce4 
```
给予权限：
```bash
chmod u+x ~/.vnc/xstartup
```

编辑 config 配置分辨率
```bash
vim ~/.vnc/config
```
填入以下内容：
```
geometry=1920x1080
dpi=96
```

## 启动 VNC 服务器

```bash
# 注意：只有将-localhost选项的值设置为no时，才允许远程连接到VNC服务器
# 外网服务器不建议使用  -localhost no 参数，可使用 ssh 端口转发功能访问。
vncserver -localhost no

# 如果启用了防火墙，允许5901端口，否则无需操作
sudo ufw allow 5901

# 查看启动的vnc服务
vncserver -list

# 停止一个vnc服务，:1 代表 5901，:2 代表 5902，以此类推。
vncserver -kill :1
```

使用 `vncviewer` 客户端连接 VNC 服务器

- Ubuntu 客户端，`sudo apt install tigervnc-viewer`
- Windows 客户端
	- [tigervnc viewer](https://sourceforge.net/projects/tigervnc/) (比 realvnc 体验更好)
	- [UltraVNC](https://uvnc.com/downloads/ultravnc.html)
	- [Download TightVNC](https://www.tightvnc.com/download.php)

连接地址：`server_ip:5901`，使用 `ip a` 命令查看服务器ip

如果要让外部网络访问，请使用端口转发（[[ssh 笔记#端口转发]]）：

```bash
ssh -L 5901:127.0.0.1:5901 -N -f -l username remote_server_ip
```

## 安装为系统服务（请勿使用root用户）

编辑启动配置
```bash
sudo vim /etc/systemd/system/vncserver@.service
```
填入以下内容：
```sh
[Unit]
Description=Remote desktop service (VNC)
After=syslog.target network.target

[Service]
Type=simple
#这里改成你的用户名！
User=ubuntu
PAMName=login
PIDFile=/home/%u/.vnc/%H%i.pid
ExecStartPre=/bin/sh -c '/usr/bin/vncserver -kill :%i > /dev/null 2>&1 || :'
#外网服务器不建议使用 -localhost no 参数！
ExecStart=/usr/bin/vncserver :%i -geometry 1440x900 -alwaysshared -fg -localhost no
ExecStop=/usr/bin/vncserver -kill :%i

[Install]
WantedBy=multi-user.target
```
设置开机自启
```bash
#重新加载单元文件
sudo systemctl daemon-reload
#启用单元文件
sudo systemctl start vncserver@1.service
#设置开机自启
sudo systemctl enable vncserver@1.service
```
## 参考


- https://www.myfreax.com/how-to-install-and-configure-vnc-on-ubuntu-22-04/
- https://vegastack.com/tutorials/how-to-install-and-configure-vnc-on-ubuntu-22-04/
- https://www.inktea.eu.org/2021/49123.html
- [Ubuntu 24.04 LTS : VNC サーバーの設定 : Server World](https://www.server-world.info/query?os=Ubuntu_24.04&p=desktop&f=6)
- [[setup-vnc]]

---
## 安装 XRDP

- 推荐使用一键安装脚本：[xRDP Installation Script (Free)](https://www.c-nergy.be/products.html)
- 以下是手动安装教程：

安装 xrdp
```bash
sudo apt install xrdp
```

你需要创建或修改 `~/.xsession` 文件，以便 XRDP 知道使用 XFCE 作为桌面环境。运行以下命令：
```bash
echo xfce4-session > ~/.xsession
```

确保 xrdp 服务正在运行并已设置为开机自启：
```bash
sudo systemctl enable xrdp
sudo systemctl start xrdp
```

配置防火墙（如果适用）
```bash
sudo ufw allow 3389
```

在 Windows 启动 `mstsc.exe`，连接 IP 地址即可

> 注意：xrdp 不可和 vncserver 一起使用，否则连接不上，如果启动了 vncserver，请使用 `vncserver -kill :1` 命令关闭！


## 使用 MobaXterm 的 X11 Server 连接

首先使用 MobaXterm 的 ssh 连接到 Linux 服务器，然后执行以下命令

~/startwm.sh
```bash
#!/bin/sh
# https://www.server-world.info/query?os=Ubuntu_24.04&p=desktop&f=7
dbus-launch --exit-with-session /usr/bin/startxfce4
```

## 总结

使用上述方法都会有各种各样的问题，比如 VSCode 的 `gnome-keyring` 失效，以及部分软件在 VNC, XRDP, X11 Server 下不可用。。。所以如果要使用 GUI 软件，最好还是使用实体机