## 准备工作

1. 推荐到微软应用商店下载最新的Ubuntu发行版（ubuntu22.04），自带wslg功能，[wsl官方文档](https://learn.microsoft.com/en-us/windows/wsl/tutorials/gui-apps) 下载的包可能不支持wslg
2. 按照提示升级wsl内核到最新
3. 进入系统后，修改镜像源 [[Linux Repository 国内镜像汇总]]
4. `sudo apt update && sudo apt upgrade`
5. 进行最精简的测试 `sudo apt install x11-apps`
6. 运行其中一个命令，检查窗口是否成功开启 `xcalc`, `xclock`, `xeyes`
7. 至此，wslg已正常运行
## 安装 xfce4 桌面环境

- 安装桌面环境 `sudo apt install xfce4 xfce4-goodies`
- 启动程序进行测试
	- 文件管理器 `thunar`

## 安装远程桌面服务

- 如果之前安装过，可以先卸载 `sudo apt purge xrdp`
- 安装 xrdp `sudo apt install xrdp`
- 执行以下命令，完成配置
```sh
sudo cp /etc/xrdp/xrdp.ini /etc/xrdp/xrdp.ini.bak
sudo sed -i 's/max_bpp=32/#max_bpp=32\nmax_bpp=128/g' /etc/xrdp/xrdp.ini
sudo sed -i 's/xserverbpp=24/#xserverbpp=24\nxserverbpp=128/g' /etc/xrdp/xrdp.ini
echo xfce4-session > ~/.xsession
```
- 修改xrdp配置
```
sudo vim /etc/xrdp/startwm.sh

...
# 添加这两行：
unset DBUS_SESSION_BUS_ADDRESS
unset XDG_RUNTIME_DIR

# 注意：在这行的上面，这行下面的不要动
test -x /etc/X11/Xsession && exec /etc/X11/Xsession
...
```
- 启动 xrdp `sudo systemctl start xrdp`
	- 如果再次修改了配置，需要重启 xrdp `sudo systemctl restart xrdp`
- 查看虚拟机的 IP `ip a`
- 在宿主机运行 `mstsc` 连接虚拟机的 IP
- 输入你的用户名和密码完成登录

## 参考

- [wslg官方文档](https://learn.microsoft.com/en-us/windows/wsl/tutorials/gui-apps) 
- [How to install XRDP with XFCE4 on Ubuntu? [SOLVED]](https://www.golinuxcloud.com/install-xrdp-with-xfce4-on-ubuntu/#Step-1_Install_XFCE)
- [Windows10/11上安装图形用户界面 (GUI)并在 WSL 2 中运行 Ubuntu 22.04](https://updayday.notion.site/Windows10-11-GUI-WSL-2-Ubuntu-22-04-fa5b638b838f4047904bae9b80bdb648)