Alpine is a lightweight & safe server system.

# Install System

Download: https://alpinelinux.org/downloads/

```sh
# Boot into CD live system and execute this command
# Then the installation wizard will appear
setup-alpine
```

## Install Packages

Set source:

```sh
vim /etc/apk/repositories
---
#/media/cdrom/apks
http://mirrors.aliyun.com/alpine/v3.15/main
http://mirrors.aliyun.com/alpine/v3.15/community
http://mirrors.aliyun.com/alpine/edge/main
http://mirrors.aliyun.com/alpine/edge/community
#http://mirrors.aliyun.com/alpine/edge/testing
```

Apk:

```sh
# Install a package
apk add <package-name>
# Update db
apk update
```

## Install zsh & OhMyZsh

```sh
apk add zsh
vim /etc/passwd
root:x:0:0:root:/root:/bin/zsh
```

```sh
# Install OhMyZsh
git clone https://mirrors.tuna.tsinghua.edu.cn/git/ohmyzsh.git
cd ohmyzsh/tools
REMOTE=https://mirrors.tuna.tsinghua.edu.cn/git/ohmyzsh.git sh install.sh
```

## Service Management

```sh
# Start a service
systemctl <service-name>  start
# Enable autostart
rc-update add <service-name> 
```
