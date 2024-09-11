参考：
- [2021.02. Arch Linux 安装小记](https://zhuanlan.zhihu.com/p/348370646)
- [安装指南 - Arch Linux 中文维基](https://wiki.archlinuxcn.org/wiki/%E5%AE%89%E8%A3%85%E6%8C%87%E5%8D%97)

如果您觉得用命令行安装过于繁琐，可以试试官方的安装脚本 `archinstall`。详情可参见 [archinstall](https://wiki.archlinuxcn.org/wiki/Archinstall "Archinstall")。

```zsh
archinstall
```

## 1. 准备安装

前置条件：

- [x] 能联网的电脑（纯ArchLinux需要网络安装）
- [x] 一个大于 1GiB 的U盘

下载 iso 镜像：https://mirrors.tuna.tsinghua.edu.cn/archlinux/iso/

将 iso 镜像写入到U盘：

- Windows环境：使用 rufus 工具
- Linux环境：`sudo dd bs=4M if=archlinux.iso of=/dev/<你的u盘> conv=fdatasync status=progress`

## 2. 启动U盘系统并联网

在 BIOS 中配置 U 盘启动。

进入 u 盘系统后，可以看到 `root@archiso ~ #`，后续需要联网来下载软件包

- 有线网（DHCP动态分配IP）
  - 直接执行 `dhcpcd`
- 无线网（Wi-Fi）
  - 进入 iwd 命令行：`iwctl`，进入以后长这样：`[iwd]# `
  - 查询无线网卡：`device list`
  - 扫描 Wi-Fi：`station <devicename> scan`
  - 输出扫描的结果：`station <devicename> get-networks`
  - 连接热点 SSID：`station <devicename> connect <wifi-ssid>`
  - 输入密码连接即可，最后 `exit` 退出 iwd 命令行
  - 执行 `dhcpcd`

查看是否联网：`ip a` 或 `ping archlinux.org`

同步系统时间：`timedatectl set-ntp true`，并验证 `timedatectl status`

## 3. 安装到硬盘

### 3.1 硬盘分区

列出所有设备：`fdisk -l`

进入图形界面分区工具：`cfdisk /dev/sd<?>`

创建一个 EFI 分区和一个 Linux Filesystem 分区（略）

格式化分区：

- EFI 分区：`mkfs.fat /dev/sda<?1>`
- 根文件系统：`mkfs.ext4 /dev/sda<?2>`

挂载根目录：`mount /dev/sda<?2> /mnt`

挂载 EFI 分区：

- `mkdir /mnt/efi`
- `mount /dev/sda<?1> /mnt/efi`

### 3.2 安装 ArchLinux 到硬盘

ArchLinux 是网络安装，所以需要配置国内镜像源

`vim /etc/pacman.d/mirrorlist`，参考：[Arch Linux 软件仓库镜像使用帮助](https://mirrors.tuna.tsinghua.edu.cn/help/archlinux/)

```sh
# 安装 ArchLinux
pacstrap /mnt base linux linux-firmware

# 配置 fstab
genfstab -U /mnt >> /mnt/etc/fstab
```

此时系统安装完成，但如果缺少必要的配置和软件将无法正常工作。

## 4. chroot 后续配置

```sh
# 进入 chroot 环境
# 可以理解为进入新装系统的运行环境
arch-chroot /mnt
```

在 chroot 环境中，执行的命令将直接作用于新装的系统。

```sh
# 设置主机名和 hosts
echo "ArchLinuxPC" > /etc/hostname
echo "127.0.0.1 localhost" >> /etc/hosts
echo "::1 localhost" >> /etc/hosts

# 设置时区
ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
hwclock --systohc
locale-gen

# 本地化（略）
# 本地化可以在重启进入系统后修改
# vim /etc/locale.gen
# locale-gen
# vim /etc/locale.conf

# 安装配置 GRUB 引导程序
pacman -S grub efibootmgr
grub-install --efi-directory=/efi --bootloader-id=ArchLinux
grub-mkconfig -o /boot/grub/grub.cfg

# 无线和有线网络配置
pacman -S iwd dhcpcd
systemctl enable iwd
systemctl enable systemd-resolvecd
systemctl enable dhcpcd
# 安装网络管理工具
sudo pacman -S networkmanager
systemctl enable NetworkManager
# 开机启动蓝牙服务
sudo systemctl enable bluetooth

# 音频驱动
sudo pacman -S alsa-utils pulseaudio pulseaudio-alsa

# 安装 X 显示服务和登录管理器
pacman -S xorg sddm sddm-kcm
systemctl enable kcm
systemctl enable sddm

# 安装 KDE 桌面环境和应用软件
pacman -S plasma-meta plasma-nm
pacman -S konsole kate dolphin firefox gwenview okular spectacle vlc
pacman -S htop neofetch git p7zip zsh noto-fonts-cjk noto-fonts-emoji

# root
pacman -S sudo vim 

# 新增普通用户(arch)，加入到 wheel 组
useradd -m -G wheel arch

# 设置新用户密码
passwd arch

# 设置 root 密码
passwd

# 给普通用户提权
# 去掉这一行的注释: %wheel ALL=(ALL) ALL
visudo

```

## 5. 重启进入新系统

```sh
# 退出 chroot 环境
exit
# 重启拔出U盘
reboot
```

