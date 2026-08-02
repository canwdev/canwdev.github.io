## iSH 启动 sshd

```shell
# iPhone iSH
/usr/sbin/sshd

# PC 连接 iPhone
ssh root@192.168.0.111

# 发送公钥（Windows 用户可以借助 git-bash）
ssh-copy-id root@192.168.0.111
```

## PC rclone 挂载 sftp

```shell
rclone mount --sftp-host=192.168.0.111 --sftp-user=root --sftp-port=22 --sftp-key-file=C:/Users/user/.ssh/id_rsa.pub --vfs-cache-mode writes sftp: Z:
```
## iSH 设置镜像站

```shell
cp /etc/apk/repositories /etc/apk/repositories.bak

echo "https://mirrors.ustc.edu.cn/alpine/v3.18/main" > /etc/apk/repositories
echo "https://mirrors.ustc.edu.cn/alpine/v3.18/community" >> /etc/apk/repositories

apk update
```

## 安装 fish

```shell
apk add fish

# 设为默认shell
vim /etc/passwd
# 找到以 `root` 开头的第一行，它原本看起来像这样
root:x:0:0:root:/root:/bin/ash
# 改为（注意是 /usr/bin/fish）
root:x:0:0:root:/root:/usr/bin/fish
```