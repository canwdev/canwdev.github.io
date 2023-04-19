## 参考

- https://github.com/dumasss163/mirrorhub
- https://github.com/myd7349/mirrors
- [[Node.js 笔记#设置 npm/yarn 镜像]]
- [[Docker笔记#Docker Hub 镜像配置]]

## Ubuntu 

- https://mirrors.tuna.tsinghua.edu.cn/help/ubuntu/

Ubuntu 的软件源配置文件是 `/etc/apt/sources.list`。将系统自带的该文件做个备份，将该文件替换为下面内容，即可使用选择的软件源镜像。

```sh
cp /etc/apt/sources.list /etc/apt/sources.list.bak
vim /etc/apt/sources.list
# 输入 dG 删除全部内容
# 输入 i 进入插入模式
# 粘贴下面的内容（注意你的系统版本）
# Esc + :wq + 回车 保存
```

Ubuntu 版本：22.04 LTS
```properties
# 默认注释了源码镜像以提高 apt update 速度，如有需要可自行取消注释
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ jammy main restricted universe multiverse
# deb-src https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ jammy main restricted universe multiverse
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ jammy-updates main restricted universe multiverse
# deb-src https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ jammy-updates main restricted universe multiverse
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ jammy-backports main restricted universe multiverse
# deb-src https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ jammy-backports main restricted universe multiverse

# deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ jammy-security main restricted universe multiverse
# # deb-src https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ jammy-security main restricted universe multiverse

deb http://security.ubuntu.com/ubuntu/ jammy-security main restricted universe multiverse
# deb-src http://security.ubuntu.com/ubuntu/ jammy-security main restricted universe multiverse

# 预发布软件源，不建议启用
# deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ jammy-proposed main restricted universe multiverse
# # deb-src https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ jammy-proposed main restricted universe multiverse
```

```sh
# 更新源
apt update

# 升级全部
# apt upgrade
```

## Manjaro Linux

- https://mirrors.ustc.edu.cn/help/manjaro.html?utm_source=pocket_mylist#manjaro-linux

生成可用中国镜像站列表：
`sudo pacman-mirrors -i -c China -m rank`
勾选 `http://mirrors.ustc.edu.cn/manjaro/` ，然后按 `OK` 键两次。
最后刷新缓存：
`sudo pacman -Syy`

