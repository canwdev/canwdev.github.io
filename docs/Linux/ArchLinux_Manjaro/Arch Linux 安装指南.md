# Arch Linux 安装指南

日期：2025.12.22
参考：https://github.com/SHORiN-KiWATA/ShorinArchExperience-ArchlinuxGuide/wiki

## Live CD 准备

连接WiFi

```shell
iwctl
station wlan0 connect <SSID>
<PASSOWD>
```

配置国内镜像

```sh
vim /etc/pacman.d/mirrorlist
```

```
输入 /China 回车
找到 tuna 或 ustc 那一行
yy   复制一行
gg   回到顶部
p    粘贴
:wq  保存并退出
```

安装更新

```sh
pacman -Syu
pacman -S archinstall
```

## 启动 `archinstall`

稍等片刻启动，全程需要联网，部分操作需要联网请耐心等待

- Mirrors and repos -> Selecting regions -> China
- Disk config -> Partitioning -> Manual 分3个区
    - 【引导区】格式化为：fat32；分区大小：512MB；挂载点：/boot/efi
    - 【根目录】强烈推荐 btrfs，ext4 次之，挂载点：/
        - 选择Mark/Unmark as compressed设置透明压缩；再选择Set subvolumes（创建子卷）> Add subvolume
        - 至少需要创建root子卷和home子卷。Subvolume name设置成 @，对应Subvolume mountpoint是 / ； @home 对应 /home
        - confirm and exit > confirm and exit > back 退出硬盘分区
    - 【swap】必要的 linux-swap 建议大于物理内存
- Bootloader -> Grub
- Authencation -> 设置 root 密码和创建用户 user
- Profile -> Type -> Minimal 最小化安装
- Applications -> Bluetooth -> on | Audio -> pipewire
- Network config -> Use Network Manager
- Additional packages -> vim (提示：输入 /vim 可过滤，回车键确认)
- Timezone -> Aisa/Shanghai
- Install -> 等待！

安装完成后重启

## 初次进入系统

连接WiFi：

```shell
# 推荐！
nmtui

# 或
nmcli dev wifi list
nmcli wev wifi connect <SSID> --ask
nmcli conn up <SSID>
```

连接上WiFi后即可安装常用软件

```shell
pacman -S fastfetch btop cmatrix
```

设置默认编辑器：`vim /etc/environment`，写入 `EDITOR=vim`

archlinuxcn源：`sudo vim /etc/pacman.conf` 文件底部写入（ctrl+shift+V粘贴）

```conf
[archlinuxcn]
Server = https://mirrors.ustc.edu.cn/archlinuxcn/$arch 
Server = https://mirrors.tuna.tsinghua.edu.cn/archlinuxcn/$arch 
Server = https://mirrors.hit.edu.cn/archlinuxcn/$arch 
Server = https://repo.huaweicloud.com/archlinuxcn/$arch 
```

同步数据库并安装archlinuxcn密钥：`sudo pacman -Sy archlinuxcn-keyring`

字体：`pacman -S wqy-zenhei noto-fonts noto-fonts-emoji`

## 安装KDE

强烈推荐KDE，开箱即用、功能完善、操作效率高，不推Niri（平铺式，学习成本高）或Gnome（需要装许多插件才好用）。

```shell
pacman -S plasma-meta konsole dolphin kate firefox qt6-multimedia-ffmpeg pipewire-jack
```

登录管理器

```shell
systemctl start sddm
systemctl enable sddm 
```

## flatpak 相关

```shell
pacman -S flatpak flatpak-kcm
```

更换flatpak国内源 `sudo flatpak remote-modify flathub --url=https://mirror.sjtu.edu.cn/flathub`
注意：即使更换来源，可能也需要挂代理才能使用。