> 使用 apt/dpkg 安装的软件包，Debian/Ubuntu 同样适用
## 常用

- [[Linux 镜像源#Debian]]
- 查看发行版
	- `hostnamectl`
	- `cat /etc/issue`
	- `lsb_release -a` (Ubuntu专用)
- [Debian 12 Bookworm : Download : Server World](https://www.server-world.info/en/note?os=Debian_12&p=download)
	- 服务器版镜像，tuna镜像站 [debian-live-12.6.0-amd64-standard.iso](https://mirrors.tuna.tsinghua.edu.cn/debian-cd/current-live/amd64/iso-hybrid/debian-live-12.6.0-amd64-standard.iso)

##  实用软件

- 浏览器
	- Chrome
		- `wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb`
		- `sudo dpkg -i ./google-chrome-stable_current_amd64.deb`
		- 如果以上命令安装失败，请执行 `sudo apt install -f` 后再重复执行上一行的命令
	- [Firefox](https://www.mozilla.org/en-US/firefox/linux/)
- [VS Code](https://code.visualstudio.com/download)
- Wine 模拟器
	- `sudo apt install wine`
	- wine32: `sudo dpkg --add-architecture i386 && sudo apt-get update && sudo apt-get install wine32`
- [[Ubuntu Server 安装 TigerVNC + Xfce4 桌面环境]]
- 密码管理：`gnome-keyring` `seahorse` `keepassxc`

自用安装命令：
```bash
apt update
apt upgrade
apt install \
  zsh vim neofetch htop tmux curl wget net-tools p7zip-full \
  git nodejs npm docker.io \
  nginx openssh-server \
  tigervnc-standalone-server tigervnc-common \
  fonts-noto-cjk fonts-noto-cjk-extra fonts-noto-color-emoji \
  keepassxc seahorse
```

### 字体

- 思源黑体 `sudo apt install fonts-noto-cjk fonts-noto-cjk-extra`
- 颜文字 `sudo apt install fonts-noto-color-emoji`
- [fonts-wqy-microhei](http://packages.ubuntu.com/trusty/fonts-wqy-microhei) -「文泉驛微米黑」
- [fonts-wqy-zenhei](http://packages.ubuntu.com/trusty/fonts-wqy-zenhei) -「文泉驛正黑體」
### oh-my-zsh

Ubuntu 上安装 Oh My Zsh 的步骤

1. **安装 Zsh**:
```bash
sudo apt update
sudo apt install zsh
```

2. **更改默认 Shell**（可选）:
```bash
chsh -s $(which zsh)
```

3. **安装 Oh My Zsh**（使用 curl）:
```bash
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
```

4. **打开配置文件**:
```bash
vim ~/.zshrc
```
修改主题 [主题预览](https://github.com/ohmyzsh/ohmyzsh/wiki/Themes)
- `robbyrussell` 默认主题
- `agnoster` 美观但需要字体支持
- `ys` 轻量级且信息齐全，包含 Git 状态信息
- `bira` 提供更丰富的信息，适合日常使用
```bash
ZSH_THEME="ys"
```
重新进入终端即可生效。
