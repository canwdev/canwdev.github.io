
- 推荐自己build镜像！[[基于 Docker 制作一个 Debian+Xfce4+KasmVNC 容器]]
- 使用 Docker 容器启动一个 基于 VNC 的 Ubuntu 桌面环境！

```sh
sudo su

# 安装 docker
apt update
apt install docker.io docker-compose
```

## 手动创建镜像

- Dockerfile
```Dockerfile
# 使用 Ubuntu 24.04 基础镜像
FROM ubuntu:24.04

# 更新包列表并安装工具
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    software-properties-common \
    sudo

# 添加 NodeSource 的签名密钥和 PPA 并安装 Node.js LTS 版本
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - && \
    apt-get install -y nodejs

# 安装 Xfce 桌面环境和 VNC 服务器
RUN apt-get install -y xfce4 xfce4-goodies \
    tightvncserver \
    dbus-x11 \
    x11-xserver-utils

# 创建新用户并配置密码
RUN useradd -m -s /bin/bash vncuser && echo 'vncuser:password' | chpasswd && \
    usermod -aG sudo vncuser

# 复制当前文件夹下的 noVNC 文件夹到容器内的 /app 目录!
COPY noVNC /app/noVNC
RUN ls /app/noVNC/utils

# 根用户以复制启动脚本
USER root
COPY start_vnc.sh /usr/local/bin/start_vnc.sh
RUN chmod +x /usr/local/bin/start_vnc.sh

# 设置 VNC 服务器配置
USER vncuser
ENV USER=vncuser
RUN mkdir -p /home/vncuser/.vnc && \
    echo "password" | vncpasswd -f > /home/vncuser/.vnc/passwd && \
    chmod 600 /home/vncuser/.vnc/passwd && \
    echo "startxfce4 &" > /home/vncuser/.vnc/xstartup && \
    chmod +x /home/vncuser/.vnc/xstartup

# 暴露 VNC 端口
EXPOSE 5901

# 启动 VNC 服务器和 Xfce!
CMD ["/usr/local/bin/start_vnc.sh"]
```
- init.sh
```bash
# 注意！执行前请先下载 [noVNC](https://github.com/novnc/noVNC) 到当前目录！  
docker build -t ubuntu24.04-nodejs-vnc .  
docker rm -f pp_whv  
# 5911 vnc客户端端口，8888 noVNC 网页控制端口  
docker run --name pp_whv -d -p 5911:5901 -p 8888:8888 ubuntu24.04-nodejs-vnc
```
- start_vnc.sh
```bash
#!/bin/bash  
  
# 设置环境变量  
export USER=vncuser  
export HOME=/home/vncuser  
  
# 启动 VNC 服务器并设置显示参数  
vncserver :1 -geometry 1280x800 -depth 24  
  
# 保持容器运行  
#tail -f /dev/null  
  
# 8888 是你将暴露给Web浏览器的WebSocket端口，而 localhost:5901 是你的VNC服务器运行的地址和端口。  
/app/noVNC/utils/novnc_proxy --listen 8888 --vnc localhost:5901
```

## 使用现成的镜像

```sh
# 创建工作目录
mkdir ~/ubuntu_vnc_desktop
cd ~/ubuntu_vnc_desktop
vim docker-compose.yml
```

填入以下内容：
```yml
version: '3.5'

services:
    ubuntu-xfce-vnc:
        container_name: xfce
        image: imlala/ubuntu-xfce-vnc-novnc:latest
        shm_size: "2gb"  # 防止高分辨率下Chromium崩溃,如果内存足够也可以加大一点点
        ports:
            - 5900:5900   # TigerVNC的服务端口（保证端口是没被占用的，冒号右边的端口不能改，左边的可以改）
            - 6080:6080   # noVNC的服务端口，注意事项同上
        environment: 
            - VNC_PASSWD=PAS3WorD    # 改成你自己想要的密码
            - GEOMETRY=1280x720      # 屏幕分辨率，800×600/1024×768诸如此类的可自己调整
            - DEPTH=24               # 颜色位数16/24/32可用，越高画面越细腻，但网络不好的也会更卡
        volumes: 
            - ./Downloads:/root/Downloads  # Chromium/Deluge/qBittorrent/Transmission下载的文件默认保存位置都是root/Downloads下
            - ./Documents:/root/Documents  # 映射一些其他目录
            - ./Pictures:/root/Pictures
            - ./Videos:/root/Videos
            - ./Music:/root/Music
        restart: unless-stopped
```

启动
```sh
docker-compose up -d

# 查看服务器ip
ip a
```

- 使用浏览器访问 服务器ip:6080
- 或使用 VNC Viewer 访问 服务器ip:5900
## 参考

- [【好玩的Docker项目】搭建一个Ubuntu的桌面系统（带VNC/noVNC）随时随地可以通过浏览器访问！](https://iwanlab.com/docker-compose-install-ubuntu-desktop/)
- https://github.com/fcwu/docker-ubuntu-vnc-desktop
- https://github.com/accetto/ubuntu-vnc-xfce
- https://hub.docker.com/r/imlala/ubuntu-xfce-vnc-novnc/tags