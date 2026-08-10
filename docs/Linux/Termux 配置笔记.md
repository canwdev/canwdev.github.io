参考
- [Termux | The main termux site and help pages.](https://termux.dev/cn/)
- [Termux 高级终端安装使用配置教程](https://www.sqlsec.com/2018/05/termux.html)
- [Hello，Termux](https://tonybai.com/2017/11/09/hello-termux/)

## 安装 Termux

- [Releases · termux/termux-app](https://github.com/termux/termux-app/releases)
- [F-Droid](https://f-droid.org/zh_Hans/packages/com.termux/)

## 常用路径

- $HOME `/data/data/com.termux/files/home`
- $PREFIX `/data/data/com.termux/files/usr`

## 更换国内镜像

> 2026 更新：可以不用更换镜像，初次使用会自动找到合适的镜像。

[清华TUNA镜像的说明](https://mirror.tuna.tsinghua.edu.cn/help/termux/) 。编辑 `/data/data/com.termux/files/usr/etc/apt/sources.list` 文件，填入以下内容：

> 如果没有 vi 等编辑器，可以使用 `echo 'deb http://mirrors.tuna.tsinghua.edu.cn/termux stable main' > sources.list` 的方式来更新文件

```
# The main termux repository:
# deb http://termux.net stable main
deb http://mirrors.tuna.tsinghua.edu.cn/termux stable main
```

最后 `pkg update && pkg upgrade`

工具：`pkg install neovim fastfetch htop`

## on-my-zsh

```sh
apt install zsh
apt install git
git clone --depth=1 git://github.com/robbyrussell/oh-my-zsh.git ~/.oh-my-zsh
cp ~/.oh-my-zsh/templates/zshrc.zsh-template ~/.zshrc
chsh -s zsh
```

## fish

fish：开箱即用的 shell（推荐）
```shell
pkg install fish -y
chsh -s fish
```

## Termux 设置 sshd

- [电脑通过ssh连接android手机上的termux](https://www.jianshu.com/p/2e6c8152a2ba)

```shell
# 1. Termux 上安装 openssh 并启动服务
apt install openssh
sshd

# 2. 查看 Termux 用户名（如果不使用密钥登录，可通过密码登录）
whoami                          # 查看当前用户名
# 使用密码登录方式：通过 passwd 设置密码
passwd                          # 设置登录密码

# 3. 查看 Termux IP 地址
ifconfig                        # 或使用 ip addr

# 4. 从终端连接 Termux（指定端口 8022）
ssh u0_a170@192.168.0.111 -p 8022

# 5. 发送公钥到 Termux（Windows 用户可借助 git-bash 或 WSL）
#    注意：端口参数使用 -p，用户名根据实际情况修改
ssh-copy-id -p 8022 u0_a170@192.168.0.111
```

## PC rclone 挂载 Termux 存储

```shell
termux-setup-storage

rclone mount --sftp-host=192.168.0.111 --sftp-user=u0_a170 --sftp-port=8022 --sftp-key-file=C:/Users/user/.ssh/id_rsa :sftp: Z:
```

## Termux 启动 rclone 服务

```shell
apt install rclone

cd ~/storage/shared

rclone serve webdav ./ --addr 0.0.0.0:8086 --user rclone --pass rclone --vfs-cache-mode off

# PC：推荐这种方式同步！
# 先获取加密字符串
# 如果想把 D:\TestFolder 同步到服务端的 TestFolder 子目录下
rclone sync D:\TestFolder :webdav:TestFolder --webdav-url http://192.168.0.156:8086 --webdav-user rclone --webdav-pass TFzIOGd19xkmWKRH2zC0tuufjoK4Ow --progress -v --transfers 8 --checkers 16 --track-renames


# PC：挂载方式（不推荐用于同步）
# 挂载整个根目录
rclone mount :webdav: Z: --webdav-url http://192.168.0.156:8086 --webdav-vendor other --webdav-user rclone --webdav-pass TFzIOGd19xkmWKRH2zC0tuufjoK4Ow --vfs-cache-mode off --network-mode

# 或者挂载指定子目录
rclone mount :webdav:TestFolder Z: --webdav-url http://192.168.0.156:8086 --webdav-vendor other --webdav-user rclone --webdav-pass TFzIOGd19xkmWKRH2zC0tuufjoK4Ow --vfs-cache-mode off --network-mode
```

---

## 备份与恢复

参考[官方备份教程](https://wiki.termux.com/wiki/Backing_up_Termux)，通过备份 termux 的 data 数据，可以实现备份、恢复、或迁移到其他设备（仅限相同架构）。步骤见下方。

### 备份

1. 设置termux允许访问存储空间 `termux-setup-storage`
2. 切换到termux根目录 `cd /data/data/com.termux/files`
3. 备份数据：`tar -czvf /sdcard/termux-backup.tar.gz home usr`

### 恢复

1. 切换到termux根目录 `cd /data/data/com.termux/files`
2. 替换home目录
    ```sh
    rm -rf home
    tar -zxvf /sdcard/termux-backup.tar.gz home
    ```
3. 复制 busybox 二进制文件到指定位置（重要） `cp ./usr/bin/busybox ./tar`
4. 抹掉 sysroot，所有包将被删除 `rm -rf usr`
5. 从备份文件恢复 sysroot
    ```sh
    unset LD_PRELOAD
    ./tar -zxvf /sdcard/termux-backup.tar.gz usr
    ```
6. 使用通知中心的 exit 按钮退出 Termux 然后重开即可恢复完成
