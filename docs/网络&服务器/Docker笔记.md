链接：

- [第一本 Docker 书 源码](https://github.com/turnbullpress/dockerbook-code)
- [learn-docker 学习项目](https://gitee.com/canwdev/learn-docker)
- [docker-server 实用化项目](https://gitee.com/canwdev/docker-server)

## Docker 基础

### 安装 Docker

ubuntu: [Install Docker Engine on Ubuntu | Docker Documentation](https://docs.docker.com/engine/install/ubuntu/)
```sh
sudo apt install docker-ce

sudo docker info
# 如果没有报错，则你的 Docker 安装成功了。
```

docker 的全部操作都要在 root 下进行。

### 运行第一个容器

```sh
docker run -i -t ubuntu /bin/bash
```

第一次运行，没有ubuntu镜像，将会从 DockerHub 下载（如果下载失败请看 [[#Docker Hub 镜像配置]]），完成后会自动 **附着** 到该容器里。

在容器环境里，运行 ps -aux 可以查看容器容器中运行的全部进程，当 /bin/bash 退出之后，容器也就停止运行。

使用这条命令可以附着到运行中的容器上：`docker attach bob_the_container`

### 容器命名

包含以下字符：小写字母a、z、大写字母A-z、数字0、9、下划线、圆点、横线（如果用正则表达式来表示这些符号，就是 `[a-zA-Z0-9_.-]`，可以用容器命名代替容器id，因此容器命名必须是唯一的

- 启动新的时命名：`docker --name bob_the_container run -i -t ubuntu /bin/bash`

- 重命名：`docker rename 3d0746cf585e bob_the_container`

- 查看最后运行的容器：`docker ps -l`

- 删除容器：`docker rm 3d0746cf585e`

- 启动容器：`docker start bob_the_container`（重启则是 restart）

### 创建守护式容器

上面所创建的容器都是交互式运行的容器，也可以创建长期运行的容器，叫做守护式容器，没有交互式会话，非常适合运行应用程序和服务。

```
docker run --name daemon_dave -d ubuntu /bin/sh -c "while true; do echo hello world; sleep 1; done"
```

这段代码创建一个守护式容器，作用是每隔一秒输出一句 hello world。

### 查看容器内部的日志

使用 `docker logs -ft daemon_dave` 查看容器的日志输出，其中 **f** 是 follow 即实时输出（和 tail -f 类似），t 是时间戳。

### 在容器内部运行进程（进入容器内部的shell）

打开shell交互式任务：

```
sudo docker exec -t -i daemon_dave /bin/bash
```

> -t -i 标志为我们的进程创建了可交互的 TTY

执行一条命令，创建一个空文件：

```
docker exec -d daemon_dave touch /etc/new_config_file
```

> -d 表示要运行一个后台进程

> **注意**：exec命令只能在运行中的容器中执行（容器停止后不能使用exec进入容器），如果容器始终无法启动（比如配置有误），可使用 `docker run -it --name <容器名> <镜像名> sh` 的方法进入容器调试。

### 输出容器信息

使用 `docker inspect daemon_dave` 命令，可以输出大量容器信息。

也可以添加 --format 参数以显示指定的信息：

```sh
docker inspect --format='{{ .State.Running }}' daemon_dave
```

--format 非常强大，其支持完整的 Go 语言模板

### 自动重启容器

添加 --restart 标志，在服务器启动时让docker自动启动容器。

```
docker run --restart=always --name daemon_dave -d ubuntu /bin/sh -c "while true; do echo hello world; sleep 1; done"
```

`--restart=on-faliure:5` 意思是只在容器退出代码为非0时才会自动重启，最多重启5次

要修改一个已经启动的容器，使用命令：`docker update --restart=always my-container`

要关闭自动启动，使用 `--restart=no` 选项。

### 删除容器

不仅可以使用 `docker rm daemon_dave` 来删除容器，还可以用这条命令来删除所有容器：

```sh
## 删除所有容器（危）
docker rm `docker ps -a -q`

## 删除异常停止的容器（慎用）
docker rm `docker ps -a | grep Exited | awk '{print $1}'`
```

### Docker Hub 镜像配置

国内要设置 Docker Hub 的镜像源，否则可能下载失败。

编辑 /etc/docker/daemon.json 文件（不存在则新建），内容如下：

```
{
    "registry-mirrors": ["https://hub-mirror.c.163.com/"]
}
```

然后重启 docker 服务：

```
sudo systemctl daemon-reload
sudo systemctl restart docker  
```

命令行执行 docker info，如果从结果中看到了配置的镜像，说明配置成功。

更多镜像列表：

| **镜像加速器**                                               | **镜像加速器地址**                      | 专属加速器       | 其它加速                                                     |
| ------------------------------------------------------------ | --------------------------------------- | ---------------- | ------------------------------------------------------------ |
| [Docker 中国官方镜像](https://docker-cn.com/registry-mirror) | https://registry.docker-cn.com          |                  | Docker Hub                                                   |
| [DaoCloud 镜像站](https://daocloud.io/mirror)                | http://f1361db2.m.daocloud.io           | 可登录，系统分配 | Docker Hub                                                   |
| [Azure   中国镜像](https://github.com/Azure/container-service-for-azure-china/blob/master/aks/README.md#22-container-registry-proxy) | https://dockerhub.azk8s.cn              |                  | Docker Hub、GCR、Quay                                        |
| [科大镜像站](https://mirrors.ustc.edu.cn/help/dockerhub.html) | https://docker.mirrors.ustc.edu.cn      |                  | Docker Hub、[GCR](https://github.com/ustclug/mirrorrequest/issues/91)、[Quay](https://github.com/ustclug/mirrorrequest/issues/135) |
| [阿里云](https://cr.console.aliyun.com)                      | https://<your_code>.mirror.aliyuncs.com | 需登录，系统分配 | Docker Hub                                                   |
| [七牛云](https://kirk-enterprise.github.io/hub-docs/#/user-guide/mirror) | https://reg-mirror.qiniu.com            |                  | Docker Hub、GCR、Quay                                        |
| [网易云](https://c.163yun.com/hub)                           | https://hub-mirror.c.163.com            |                  | Docker Hub                                                   |
| [腾讯云](https://cloud.tencent.com/document/product/457/9113) | https://mirror.ccs.tencentyun.com       |                  | Docker Hub                                                   |


## Docker 镜像

### 什么是 Docker 镜像

docker 镜像是分层的，利用了写时复制机制，上面的层不会影响下面的层。

### 列出镜像

使用 `docker images` 列出本地的 Docker 镜像（使用 docker ps 列出容器）
相同镜像用不同的 tag 来区分版本，如果需要安装指定的 tag，可以在仓库名后面加上一个冒号和标签名来指定：

```
docker run -t -i --name new_container ubuntu:12.04 /bin/bash
```

### 拉取镜像
如果本地宿主机上没有镜像，Docker 会自动从 Docker Hub 下载，如果想手动拉取，可以使用 pull 命令：
```
docker pull fedora
```

### 查找镜像
使用 `docker search` 命令来查找所有公开的镜像
然后运行 `docker run -i -t node /bin/bash` 就可以启动该镜像

### 构建镜像
要构建自己的镜像，首先要注册一个 [Docker Hub](https://hub.docker.com/) 账号。

### 用 Dockerfile 构建镜像
并不推荐使用 docker commit 的方式构建镜像，推荐使用 Dockerfile。
创建一个 Dockerfile（空文件）：
```
root@mint-virtual-machine:/home/mint# mkdir static_web
root@mint-virtual-machine:/home/mint# cd static_web/
root@mint-virtual-machine:/home/mint/static_web# touch Dockerfile
```
推荐使用VSCode Remote + Docker 插件来完成编辑。
在文件中写入以下代码：
```
## Version: 0.0.1
FROM ubuntu:14.04
LABEL maintainer="canwdev"
RUN sed -i "s@http://.*archive.ubuntu.com@http://mirrors.huaweicloud.com@g" /etc/apt/sources.list
RUN sed -i "s@http://.*security.ubuntu.com@http://mirrors.huaweicloud.com@g" /etc/apt/sources.list
RUN apt-get update
RUN apt-get install -y nginx
RUN echo 'Hi, I am in your container' \
    >/usr/share/nginx/html/index.html
EXPOSE 80
```
当然，也可以使用阿里云镜像：`sudo sed -i 's/archive.ubuntu.com/mirrors.aliyun.com/g' /etc/apt/sources.list`
基于 Dockerfile 构建新镜像
```
cd static_web/
docker build -t="canwdev/static_web:v1" .
```
如果构建指令失败了，可以使用 `docker ps -a` 配合 `docker run -t -i c6c2d0078e38 /bin/bash` 进入到容器内部进行调试，该容器的状态是这次构建到目前为止已经成功的最后一步。
如果上次有构建，则会存在构建缓存。如果不想要这个缓存，可以使用 --no-cache 命令在构建时关闭缓存：
```
docker build --no-cache -t="canwdev/static_web" .
```

### 从新镜像启动容器
```
docker run -d -p 80 --name static_web canwdev/static_web nginx -g "daemon off;"
```

### 端口映射
端口绑定方式，将容器80端口映射到宿主机指定端口（8080）：

```
docker run -d -p 8080:80 --name static_web canwdev/static_web nginx -g "daemon off;"
```

使用 docker port 查看端口映射情况：`docker port app_name`


## Dockerfile 与仓库

**CMD** 命令指定一贯容器启动时要运行的命令，**ENTRYPOINT** 命令和它相似。

写法如下，每个 Dockerfile 中只能指定一条 CMD 指令：

```
CMD ["/bin/bash", "-l"]
CMD ["./frps","-c","./frps.ini"]
```

```
ENTRYPOINT ["/usr/sbin/nginx", "-g", "daemon off;"]
```

CMD 和 ENTRYPOINT 的区别是：CMD 命令会被 docker run 后面追加的命令覆盖，而 ENTRYPOINT 不会。

**WORKDIR** 指令用来在从镜像创建一个新容器时，在容器内部设置一个工作目录，ENTRYPOINT 和/或 CMD 指定的程序会在这个目录下执行。

**ENV** 用来在镜像构建过程中设定环境变量。

```
ENV RVM_PATH /home/rvm
```

**USER** 指令用来指定该镜像会以什么样的用户去运行，如果怕不设定，默认用户为 root。

```
USER nginx
```

**ADD** 指令用来将构建环境下的文件和目录复制到镜像中，对于归档文件（tar.gz）可以自动解压。

```
ENV FRP_NAME frp_0.33.0_linux_amd64
ADD ${FRP_NAME}.tar.gz /frp/
```

**COPY** 指令非常类似于ADD，它们根本的不同是COPY只关心在构建上下文中复制本地文件，而不会去做文件提取（extraction）和解压（decompression）的工作。

```
ADD software.lic /opt/application/software.lic
ADD http://wordpress.org/latest.zip /root/wordpress.zip
## 这条会自动解压：
ADD latest.tar.gz /var/www/wordpress/
COPY conf.d/ /etc/apache2/
```

对于不存在的文件夹，会自动创建（类似于 mkdir -p）。

**ONBUILD** 指令会紧跟FROM之后执行。ONPUILD指令能为镜像添加触发器(tngger)。当一个镜像被用做其他镜像的基础镜像时（比如你的镜像需要从某未准各好的位置添加源代码，或者你需要执行特定于构建镜像的环境的构建脚本），该镜像中的触发器将会被执行。

### 将镜像推送到 DockerHub
```
docker push canwdev/static_web
```

### 删除镜像

使用 `docker rmi` 来删除镜像：`docker rmi canwdev/screenfetch`

> 和 `docker rm` 用法相似，区别是 rm 是删除容器而 rmi 是删除镜像。

清理：

```sh
# 删除名称或标签为`<none>`的镜像：
docker rmi -f `docker images | grep '<none>' | awk '{print $3}'`

# 自动清理命令
# -a 一并清除所有未被使用的镜像和悬空镜像
# -f 用以强制删除，不提示信息
docker system prune
```


## 常用命令

### 镜像的导出和导入

1. 在外网环境下使用 docker pull 命令下载相应的镜像，使用docker images 列出所有镜像：

   ```
   docker images
   REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
   ubuntu              latest              74435f89ab78        2 weeks ago         73.9MB
   ```

2. 使用docker save命令对镜像进行打包：

   ```
   docker save -o ubuntu.tar ubuntu
   ls -lah
   total 73M
   drwxr-xr-x 2 root root 4.0K Jul  1 10:43 .
   drwxr-xr-x 5 mint mint 4.0K Jul  1 10:43 ..
   -rw------- 1 root root  73M Jul  1 10:43 ubuntu.tar
   ```

3. 将打包好的镜像传送至内网离线环境的机器，使用docker load 命令将镜像加载

   ```
   docker load -i ubuntu.tar
   Loaded image: ubuntu:latest
   root@mint-MacBookAir:/home/mint/Code/docker-test# docker images
   REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
   ubuntu              latest              74435f89ab78        2 weeks ago         73.9MB
   ```

4. 现在使用docker images 就可以查出刚才加载的镜像了。

---

导出和导入镜像的另一种写法：

```
docker save imageID > filename.tar
docker load < filename.tar
```

保存为压缩：

```
docker save myimage:latest | gzip > myimage_latest.tar.gz
```

### 批量导出/导入镜像

参考：[How to save all Docker images and copy to another machine](https://stackoverflow.com/a/37650072)

一次性导出所有镜像为一个大型 tar：

```sh
docker save $(docker images -q) -o /path/to/save/mydockersimages.tar
```

保存 tag 列表：

```sh
docker images | sed '1d' | awk '{print $1 " " $2 " " $3}' > mydockersimages.list
```

在另一台机器上导入：

```sh
docker load -i /path/to/save/mydockersimages.tar
```

为导入的镜像打上 tag：

```sh
while read REPOSITORY TAG IMAGE_ID
do
        echo "== Tagging $REPOSITORY $TAG $IMAGE_ID =="
        docker tag "$IMAGE_ID" "$REPOSITORY:$TAG"
done < mydockersimages.list
```

### 容器的导出和导入

```
docker export containID > filename.tar
docker import filename.tar [newname]
```

### 使用阿里云容器镜像服务

```sh
docker login --username=<用户名> registry.cn-hangzhou.aliyuncs.com
# 发布镜像
docker image tag <镜像名>:latest registry.cn-hangzhou.aliyuncs.com/<命名空间>/<镜像名>:latest
docker image push registry.cn-hangzhou.aliyuncs.com/<命名空间>/<镜像名>:latest
# 拉取镜像
docker pull registry.cn-hangzhou.aliyuncs.com/<命名空间>/<镜像名>:latest
```

