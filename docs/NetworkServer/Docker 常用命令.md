
## 构建镜像

```bash
docker build -t 镜像名:latest .
```

## 运行容器

```bash
# 强制删除容器
docker rm -f 容器名

# 运行新的容器（常用参数示例）
docker run --restart=always --name 容器名 \
  --net=host \
  --env DISPLAY=:1 \
  -p 8080:80 \
  -v $PWD/ssl:/root/ssl \
  -d 镜像名
```

## 进入正在运行的容器的 shell

> **注意**：exec 命令只能在运行中的容器中执行（容器停止后不能使用exec进入容器），如果容器始终无法启动（比如配置有误），可使用 `docker run -it --name <容器名> <镜像名> sh` 的方法进入容器调试。

```bash
docker exec -it 容器名 /bin/bash
```

## 实时查看容器日志

```bash
docker logs -ft 容器名
```

## 备份与还原镜像

```bash
# 备份并压缩镜像
docker save -o 镜像名.tar 镜像名:latest
7z a 镜像名.tar.7z 镜像名.tar

# 解压缩并还原镜像
7z x 镜像名.tar.7z -y
docker load -i 镜像名.tar
```

## 容器的导出和导入

```bash
# 导出容器
docker export 容器ID > filename.tar

# 导入容器
docker import filename.tar 新容器名字
```

## 清理（慎用）

```bash
# 删除容器
docker rm 容器名

# 强制删除运行中的容器
docker rm -f 容器名


# 清除已停止的容器
docker container prune

## 删除所有容器（危，请勿使用）
# docker rm `docker ps -a -q`

## 删除异常停止的容器（慎用）
docker rm `docker ps -a | grep Exited | awk '{print $1}'`
```

```bash
# 删除镜像
docker rmi 镜像名

# 删除名称或标签为`<none>`的镜像：
docker rmi -f `docker images | grep '<none>' | awk '{print $3}'`

# 自动清理命令
# -a 一并清除所有未被使用的镜像和悬空镜像
# -f 用以强制删除，不提示信息
docker system prune
```