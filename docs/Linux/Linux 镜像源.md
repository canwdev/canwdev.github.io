## 参考

- https://github.com/dumasss163/mirrorhub
- https://github.com/myd7349/mirrors
- [[Node.js 笔记#设置 npm/yarn 镜像]]
- [[Docker笔记#Docker Hub 镜像配置]]
- [[安装 Python#TUNA pypi 镜像使用帮助]]

## Ubuntu 

- 清华大学 https://mirrors.tuna.tsinghua.edu.cn/help/ubuntu/
- USTC [repository file generator](https://mirrors.ustc.edu.cn/repogen/)

Ubuntu 的软件源配置文件是 `/etc/apt/sources.list`。将系统自带的该文件做个备份，将该文件替换为下面内容，即可使用选择的软件源镜像。

```sh
cp /etc/apt/sources.list /etc/apt/sources.list.bak
vim /etc/apt/sources.list
# 输入 dG 删除全部内容
# 输入 i 进入插入模式
# 粘贴下面的内容（注意你的系统版本）
# Esc + :wq + 回车 保存
```

> 使用 `lsb_release -a` 命令查看 Ubuntu 版本

/etc/apt/sources.list 
Ubuntu 版本：24.04 LTS
```shell
deb https://mirrors.ustc.edu.cn/ubuntu/ noble main restricted universe multiverse
deb-src https://mirrors.ustc.edu.cn/ubuntu/ noble main restricted universe multiverse

deb https://mirrors.ustc.edu.cn/ubuntu/ noble-security main restricted universe multiverse
deb-src https://mirrors.ustc.edu.cn/ubuntu/ noble-security main restricted universe multiverse

deb https://mirrors.ustc.edu.cn/ubuntu/ noble-updates main restricted universe multiverse
deb-src https://mirrors.ustc.edu.cn/ubuntu/ noble-updates main restricted universe multiverse

deb https://mirrors.ustc.edu.cn/ubuntu/ noble-backports main restricted universe multiverse
deb-src https://mirrors.ustc.edu.cn/ubuntu/ noble-backports main restricted universe multiverse

## Not recommended
# deb https://mirrors.ustc.edu.cn/ubuntu/ noble-proposed main restricted universe multiverse
# deb-src https://mirrors.ustc.edu.cn/ubuntu/ noble-proposed main restricted universe multiverse
```

```sh
# 更新源
apt update

# 升级全部
# apt upgrade
```

## Manjaro Linux

> 设置[China镜像源](https://mirrors.ustc.edu.cn/help/manjaro.html?utm_source=pocket_mylist#manjaro-linux)可加快下载速度。Arch Linux 也可用

推荐方式 1：一行命令即可设置：`sudo pacman-mirrors --country China`
推荐方式 2：在“软件更新”中，点击菜单-首选项，将【官方软件库】的使用镜像改成 China，然后刷新镜像列表。

也可以使用命令行的方式设置软件源：[archlinux | 镜像站使用帮助 | 清华大学开源软件镜像站 | Tsinghua Open Source Mirror](https://mirrors.tuna.tsinghua.edu.cn/help/archlinux/)

编辑 /etc/pacman.d/mirrorlist， 在文件的最顶端添加：

```
Server = https://mirrors.tuna.tsinghua.edu.cn/archlinux/$repo/os/$arch
```

更新软件包缓存：

```sh
sudo pacman -Syy
```
