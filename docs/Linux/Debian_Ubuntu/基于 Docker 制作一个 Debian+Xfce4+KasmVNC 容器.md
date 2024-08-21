
完整的代码仓库：[debian-kasmvnc](https://github.com/canwdev/docker-services/tree/master/debian-kasmvnc)
## 步骤

1. 切换到root用户，创建工作目录 `mkdir test-vnc && cd test-vnc`
2. 创建文件夹并下载 [KasmVNC](https://github.com/kasmtech/KasmVNC/releases)
```sh
mkdir root
mkdir app && cd app
```
3. 创建 `start-vnc.sh` 并写入以下内容
```sh
#!/bin/bash

echo Starting vncserver, please wait...
export DISPLAY=:1
vncserver -kill $DISPLAY
vncserver $DISPLAY
echo VNC session closed

# 保持容器运行
tail -f /dev/null
```
创建 `setup-vnc.sh`
```shell
#!/bin/bash
# 某一条命令失败后立即退出整个脚本
set -e

# 覆盖默认配置
cp /etc/kasmvnc/kasmvnc.yaml /etc/kasmvnc/kasmvnc.yaml.bak
cp /app/kasmvnc.yaml /etc/kasmvnc/kasmvnc.yaml

mkdir -p /root/.vnc

# 设置 VNC 密码
printf "debian\ndebian\n\n" | vncpasswd -u root -ow

# 配置 VNC 使用 XFCE 作为桌面环境
cat << EOF > /root/.vnc/xstartup
#!/bin/bash
set -x
exec xfce4-session
EOF
chmod +x ~/.vnc/xstartup

touch /root/.vnc/.de-was-selected

# 创建 .Xauthority 文件
touch ~/.Xauthority
```
给与可执行权限：`chmod +x *.sh`
创建覆盖默认配置文件 `kasmvnc.yaml`
```yaml
# https://www.kasmweb.com/kasmvnc/docs/latest/configuration.html#default-configurations
logging:
  log_writer_name: all
  log_dest: logfile
  level: 100
network:
  # 防止 stun 查询公网 ip，提升启动速度
  udp:
    public_ip: 127.0.0.1
```
返回到上级目录 (`test-vnc`)
4. 编写 Dockerfile 以及启动脚本
Dockerfile:
```Dockerfile
# 使用官方的 Debian 12 基础镜像
FROM debian:12

# 设置环境变量，避免交互式提示
ENV DEBIAN_FRONTEND=noninteractive

# 更新包索引，并安装常用工具
RUN apt update && apt install -y \
  zsh vim neofetch htop tmux curl wget net-tools

# 安装桌面环境
RUN apt install -y xfce4 dbus-x11

RUN neofetch

# 安装 kasmvncserver
WORKDIR '/tmp'
RUN wget -O kasmvncserver.deb https://github.com/kasmtech/KasmVNC/releases/download/v1.3.1/kasmvncserver_bookworm_1.3.1_amd64.deb 
RUN apt install -y ./kasmvncserver.deb

# 安装常用软件
RUN apt install -y mousepad iproute2 xfce4-terminal

ADD ./app /app
RUN /app/setup-vnc.sh

# 使用脚本启动 VNC 服务器
CMD ["/app/start-vnc.sh"]
```
build-docker.sh
```sh
docker build -t test-vnc:latest .
```
init.sh
```sh
docker rm -f tvnc

docker run --restart=always --name tvnc \
  --net=host \
  -d test-vnc

#  -v $PWD/config-override/.vnc/kasmvnc.yaml:/root/.vnc/kasmvnc.yaml \
#  -v $PWD/config-override/ssl:/root/ssl \
```
4. 以上文件创建完成后按照以下步骤执行
	1. `chmod +x *.sh`
	2. 构建镜像（请稍候） `./build-docker.sh`
	3. 创建并启动容器 `./init.sh
	4. 此时容器应该已经正在运行，使用 `docker ps -a` 查看
	5. 输入 `ip a` 查看 ip 地址，由于设置了 `--net=host` 可以直接通过本机 ip 访问
	6. 访问 `https://192.168.xx.xx:8444/` (注意是https)进行VNC连接
		- 输入用户名 `root` 和密码 `debian`，检查是否可用
		- 如果无法访问，请查看日志：`docker logs -ft tvnc`
		- 或进入交互式命令行：`docker exec -it tvnc /bin/bash`
1. 完成！
## 参考

- [Installation — KasmVNC 1.0.0 documentation](https://www.kasmweb.com/kasmvnc/docs/latest/install.html)