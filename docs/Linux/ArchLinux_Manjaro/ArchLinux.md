
- 使用 pacman 安装的软件包，Arch/Manjaro 同样适用
- [[Linux 镜像源#Manjaro Linux]]

自用安装命令：
```zsh
pacman -Syy
pacman -S \
  vim neofetch htop tmux net-tools \
  git nodejs npm docker \
  keepassxc seahorse \
  nginx
```
## pacman 命令

- `pacman -Syu` = 执行全面系统更新
- `pacman -Ss <package>` = 搜索 包
- `pacman -S <package>` = 安装 包
- `pacman -Sy <package>` = 安装 包 之前更新源
- `pacman -R <package>` = 移除 包
- `pacman -Rc <package>` = 移除 包 及其依赖项
- `pamac` TODO

## 办公创作

- `vim` `gedit`(Gnome) `mousepad`(Xfce) `kate`(KDE) = 文本编辑器
- `calibre` `foliate` `xchm` = 文档阅读器
- `flameshot` = 截图
- `gimp` = PhotoShop
- `inkscape` = 矢量图编辑
- `krita` = 插画绘制
- `handbrake` = 视频转码

## 字体

- `noto-fonts-emoji` = 表情符号
- `noto-fonts-cjk` Google Noto CJK 字体
- `wqy-microhei wqy-bitmapfont wqy-zenhei` = 文泉驿字体系列

## 输入法

- Fcitx + KDE：`fcitx fcitx-configtool kcm-fcitx fcitx-googlepinyin fcitx-libpinyin fcitx-rime`

## 系统工具

- `screenfetch` `neofetch` `hardinfo` = 系统信息
- `htop` = 任务管理器
- `partitionmanager`(KDE) `gparted` = 分区管理器
- `tmux` = 终端分屏工具
- `seahorse` = 密码管理
- `ncdu` = 交互式地显示目录和子目录的磁盘空间使用情况，并允许您删除文件。

## 文件管理

- `pcmanfm` `thunar` `dolphin`(KDE) = 文件管理器
- `xarchiver` `ark`(KDE) = 压缩软件
- `gnome-commander` `krusader` = 类 TotalCommander 双面板文件管理器
- `dupeguru`  = 文件去重
- `convmv` = 文件名乱码修复
- `krename` = 批量重命名
- `ifuse` = 挂载 iOS 设备

## 网络

- `nextcloud-client` = Nextcloud 客户端
- `barrier` = 多设备键鼠互联

## 开发

- `sqlitebrowser` = SQLite 数据库浏览器
- `python2`
- `nginx`
- `jdk8-openjdk`
- `ghex` = 十六进制查看器
- `docker`
