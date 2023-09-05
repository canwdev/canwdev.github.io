系统环境：Ubuntu 22.04.2 LTS
```
root@hyperv:~/.vnc# lsb_release -a
No LSB modules are available.
Distributor ID: Ubuntu
Description:    Ubuntu 22.04.2 LTS
Release:        22.04
Codename:       jammy
```

安装Xfce4桌面环境：
```bash
sudo apt update
sudo apt install xfce4 xfce4-goodies
```

安装TigerVNC Server
```bash
sudo apt install tigervnc-standalone-server
```

配置vnc密码
```bash
vncpasswd
# 输入两遍密码，如：PAS3WorD
# Would you like to enter a view-only password (y/n)? 敲 n 回车
```

编辑启动配置
```bash
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

启动 VNC 服务器
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

- Ubuntu系统，`sudo apt install tigervnc-viewer`
- Windows系统，[下载tigervnc客户端](https://sourceforge.net/projects/tigervnc/files/stable/1.12.0/vncviewer64-1.12.0.exe/download)

连接地址：`server_ip:5901`，使用 `ip a` 命令查看服务器ip

安装为系统服务（请勿使用root用户）：
编辑启动配置
```bash
sudo vim /etc/systemd/system/vncserver@.service
```
填入以下内容：
```
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

- [[ssh 笔记#端口转发]] `ssh -L 5901:127.0.0.1:5901 -N -f -l username remote_server_ip`
- https://www.myfreax.com/how-to-install-and-configure-vnc-on-ubuntu-22-04/
- https://vegastack.com/tutorials/how-to-install-and-configure-vnc-on-ubuntu-22-04/
- https://www.inktea.eu.org/2021/49123.html