使用 Docker 容器启动一个 基于 VNC 的 Ubuntu 桌面环境！
## 步骤

```sh
sudo su

# 安装 docker
apt update
apt install docker.io docker-compose

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