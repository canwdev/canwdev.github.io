
## 步骤

1. 切换到root用户，创建工作目录 `mkdir test-vnc && cd test-vnc`
2. 创建文件夹并下载 [KasmVNC](https://github.com/kasmtech/KasmVNC/releases)
```sh
mkdir root
mkdir app && cd app
wget https://github.com/kasmtech/KasmVNC/releases/download/v1.3.1/kasmvncserver_bookworm_1.3.1_amd64.deb
```
3. 编写 Dockerfile 以及启动脚本
Dockerfile
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
ADD ./app /app
RUN apt install -y /app/kasmvncserver_bookworm_1.3.1_amd64.deb

# 这一步等配置完vncserver后再加上
# ADD ./root /root

WORKDIR /root

# 先随便启动一个命令保持容器运行
CMD ["vim"]

# 这一步等配置完vncserver后再修改
# CMD ["/root/start-vnc.sh"]

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
  -v $PWD/root:/root \
  -d test-vnc
```
4. 以上文件创建完成后按照以下步骤执行
	1. `chmod +x *.sh`
	2. 构建镜像（请稍候） `./build-docker.sh`
	3. 创建并启动容器 `./init.sh
	4. 此时容器应该已经正在运行，使用 `docker ps -a` 查看
	5. 进入容器内部 `docker exec -it ppwhv /bin/bash`
	6. 执行 `vncserver` 开始配置 KasmVNC，根据提示配置即可
	7. 完成后访问 `https://192.168.xx.xx:8444/` ，输入用户名和密码，检查是否可用
5. 如果上述步骤没有任何问题，则可继续构建一键启动镜像
6. 退出容器shell，删除并停止容器：`docker rm -f tvnc`
7. 创建 `./root/start-vnc.sh` 并写入以下内容
```sh
#!/bin/bash
vncserver

# 保持容器运行
tail -f /root/.vnc/*.log
```
给与可执行权限：`chmod +x *.sh`
8. 修改文件：
修改 Dockerfile，使其使用已经配置好root用户目录，并直接启动
```Dockerfile
# 使用官方的 Debian 12 基础镜像
FROM debian:12

... 不变

#（取消注释）
ADD ./root /root

WORKDIR /root

# （注释这个步骤）
# CMD ["vim"]

#（取消注释）
CMD ["/root/start-vnc.sh"]
```
修改 init.sh，因为使用了固定的配置文件
```sh
docker rm -f tvnc

# 注释并移动到这里
 # -v $PWD/root:/root \

docker run --restart=always --name tvnc \
  --net=host \
  -d test-vnc
```
9. 重新 build 和一键启动
	1. `./build-docker.sh`
	2. `./init.sh`
	3. 此时应该可以直接访问 `https://192.168.xx.xx:8444/` 进行VNC连接
10. 完成！
## 参考

- [Installation — KasmVNC 1.0.0 documentation](https://www.kasmweb.com/kasmvnc/docs/latest/install.html)