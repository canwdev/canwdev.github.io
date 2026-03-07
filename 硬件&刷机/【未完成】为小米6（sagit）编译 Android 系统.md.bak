# 为小米6（sagit）编译 Android 系统

## 官方教程

- [Build for sagit | LineageOS](https://wiki.lineageos.org/devices/sagit/build)

## 参考资料 & 镜像源

- [USTC - AOSP(Android) 镜像使用帮助](https://lug.ustc.edu.cn/wiki/mirrors/help/aosp/)
- [TUNA - Android 镜像使用帮助](https://mirrors.tuna.tsinghua.edu.cn/help/AOSP/)
- [TUNA - lineageOS 源代码镜像使用帮助](https://mirrors.tuna.tsinghua.edu.cn/help/lineageOS/)
- [中科大镜像源aosp下载源码过程](https://www.jianshu.com/p/60ec9db36871)

## 编译环境

- 200G 可用磁盘空间（`300G SSD`）
- 16G 或更大的内存（`32G`）
- 较新的 CPU（`i7-1165G7`）
- 安装有 Linux 系统（`ubuntu-20.04.3-live-server-amd64`）
- 可靠的网络连接（需要访问互联网或设置镜像）

## 编译步骤

### 设置 Ubuntu apt 镜像源

参考：https://mirrors.ustc.edu.cn/help/ubuntu.html

编辑文件：`vim /etc/apt/sources.list`

```
# 默认注释了源码仓库，如有需要可自行取消注释
deb https://mirrors.ustc.edu.cn/ubuntu/ focal main restricted universe multiverse
# deb-src https://mirrors.ustc.edu.cn/ubuntu/ focal main restricted universe multiverse

deb https://mirrors.ustc.edu.cn/ubuntu/ focal-security main restricted universe multiverse
# deb-src https://mirrors.ustc.edu.cn/ubuntu/ focal-security main restricted universe multiverse

deb https://mirrors.ustc.edu.cn/ubuntu/ focal-updates main restricted universe multiverse
# deb-src https://mirrors.ustc.edu.cn/ubuntu/ focal-updates main restricted universe multiverse

deb https://mirrors.ustc.edu.cn/ubuntu/ focal-backports main restricted universe multiverse
# deb-src https://mirrors.ustc.edu.cn/ubuntu/ focal-backports main restricted universe multiverse

# 预发布软件源，不建议启用
# deb https://mirrors.ustc.edu.cn/ubuntu/ focal-proposed main restricted universe multiverse
# deb-src https://mirrors.ustc.edu.cn/ubuntu/ focal-proposed main restricted universe multiverse
```

```sh
# 更新
apt update
```

### 安装 Android 平台工具（platform-tools）

```sh
apt install android-platform-tools-base
apt install fastboot
```

### 安装依赖工具

```sh
apt install bc bison build-essential ccache curl flex g++-multilib gcc-multilib git gnupg gperf imagemagick lib32ncurses5-dev lib32readline-dev lib32z1-dev liblz4-tool libncurses5 libncurses5-dev libsdl1.2-dev libssl-dev libxml2 libxml2-utils lzop pngcrush rsync schedtool squashfs-tools xsltproc zip zlib1g-dev
apt install python
```

我这次构建的是 LineageOS 18.1，所以不需要额外安装 OpenJDK 11 (included in source download)。

### 创建目录

```sh
mkdir -p ~/bin
mkdir -p ~/android/lineage
```

### 安装 `repo` 命令

推荐使用tuna的[git-repo镜像](https://mirrors.tuna.tsinghua.edu.cn/help/git-repo/)

```sh
cd ~/bin/repo
curl https://mirrors.tuna.tsinghua.edu.cn/git/git-repo -o repo
chmod +x repo
```

谷歌官方：

```sh
# 如果下载失败请使用代理
# set ALL_PROXY="socks5://127.0.0.1:7891"
curl https://storage.googleapis.com/git-repo-downloads/repo > ~/bin/repo
chmod a+x ~/bin/repo
```

### 添加环境变量

```sh
# vim ~/.profile 
# set PATH so it includes user's private bin if it exists
if [ -d "$HOME/bin" ] ; then
    PATH="$HOME/bin:$PATH"
fi

# 运行 source ~/.profile 使其生效
```

### 初始化 git 设置

```sh
git config --global user.email "you@example.com"
git config --global user.name "Your Name"
```

### 设置 ccache 加速构建

```sh
# vim ~/.bashrc
export USE_CCACHE=1
export CCACHE_EXEC=/usr/bin/ccache

# source ~/.bashrc
```

```sh
# 设置缓存大小，具体设置多少请参考官方文档
ccache -M 50G

# 开启缓存压缩，略微降低性能以较少磁盘空间占用
ccache -o compression=true
```

### 初始化 LineageOS 源代码存储库（repo）

```sh
cd ~/android/lineage

# 设置 repo 镜像源
export REPO_URL='https://mirrors.tuna.tsinghua.edu.cn/git/git-repo'

# 忽略证书错误
export GIT_SSL_NO_VERIFY=1

# repo init -u https://mirrors.tuna.tsinghua.edu.cn/git/lineageOS/LineageOS/android.git -b lineage-18.1
repo init -u https://github.com/LineageOS/android.git -b lineage-18.1
```

### 同步源码

参考：[没有VPN的情况下同步LineageOS源代码](https://ittat.github.io/2017/08/27/%E6%B2%A1%E6%9C%89VPN%E7%9A%84%E6%83%85%E5%86%B5%E4%B8%8B%E5%90%8C%E6%AD%A5LineageOS%E6%BA%90%E4%BB%A3%E7%A0%81.html)

```
编辑文件：
vim .repo/manifests/default.xml

找到这一段：
<remote name="aosp"
        fetch="https://android.googlesource.com"
        review="android-review.googlesource.com"
        revision="refs/tags/android-11.0.0_r46" />

将：
fetch="https://android.googlesource.com"

改成：
fetch="https://mirrors.ustc.edu.cn/aosp"
或：
fetch="https://aosp.tuna.tsinghua.edu.cn"
```

```sh
# 开始同步（由于源码过大，约123G，这里需要很多时间）
repo sync
```

