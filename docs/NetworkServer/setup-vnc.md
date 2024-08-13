## LinuxMint 安装 TigerVNC Server


### 1. 安装 tigervnc

```shell script
sudo apt install tigervnc-standalone-server tigervnc-common
```

### 2. vnc 服务相关命令

```shell script
# 查看帮助
vncserver --help

# 启动服务，初次启动会询问vnc密码，如果要重设vnc密码请运行 vncpasswd
# 默认监听端口号是 1
vncserver

# 停止在端口为 1 上面的vnc服务
vncserver -kill :1
# 停止所有
vncserver -kill :*

# 查看所有运行中的vnc服务
vncserver -list

# 查看端口使用情况
# 其中的 5901 对应的就是 1 端口
ss -tulpn
```

## 3. 桌面环境设置

LinuxMint 使用的是 Cinnamon 桌面，所以需要对 `~/.vnc/xstartup` 进行如下配置（注意最后一行）：

```
#!/bin/sh

xrdb $HOME/.Xresources
xsetroot -solid grey
# x-terminal-emulator -geometry 80x24+10+10 -ls -title "$VNCDESKTOP Desktop" &
# x-window-manager &
# Fix to make GNOME work
export XKL_XMODMAP_DISABLE=1
/etc/X11/Xsession &
exec dbus-launch cinnamon-session
```

- kde: `startkde &`
- gnome: `gnome-session &`
- xfce: `startxfce4 &`
- lxde: `lxsession &`

配置好后，重启vnc服务，用 VNC Viewer 之类的软件输入ip地址和端口号就可以连接了~。

> 如果连接的时候提示：“the connection was refused by the computer”，可能是因为 vnc 服务器只允许了 127.0.0.1 的连接，
在 `/etc/vnc.conf` 添加一行 `$localhost = "no";` 然后重启服务可以解决这个问题。
