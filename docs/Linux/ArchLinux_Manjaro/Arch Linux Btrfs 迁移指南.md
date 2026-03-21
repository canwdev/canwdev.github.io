# Arch Linux Btrfs 迁移指南

日期：2025.12.22

如何将一台电脑的archlinux迁移到另一台电脑？

源电脑使(Source) 文件系统是 btrfs，并且有两个子卷 @ -> /     @home -> /home
目标电脑(Target) 有一块全新未分区的硬盘，直接分一个btrfs分区和一个swap分区（32G）。
想要使用源电脑相同的文件系统和子卷，并且不想要源电脑的任何驱动程序。
想通过在目标电脑运行arclinux livecd 的方式，并通过网络传输源电脑的所有数据。


## 准备目标电脑 (Target)

在目标电脑上启动 LiveCD，联网，并对新硬盘进行分区。

```shell
# 格式化分区
mkfs.vfat -F32 /dev/nvme0n1p1
mkswap /dev/nvme0n1p2
swapon /dev/nvme0n1p2
mkfs.btrfs /dev/nvme0n1p3

# 挂载 Btrfs 根并创建接收路径
mount /dev/nvme0n1p3 /mnt
```

## 在目标电脑安装 openssh 并开启临时root密码登录

```shell
pacman -S openssh
vim /etc/ssh/sshd_config
```

在文件中找到（或手动添加）以下行，并将值改为 yes：

```
PermitRootLogin yes
PasswordAuthentication yes
```

启动 SSH 服务

```shell
systemctl start sshd
```

获取当前 IP 地址：`ip a`

现在，你可以在另一台电脑上通过终端连接了：`ssh root@<你的IP地址>`

## 网络传输数据 (Source -> Target)

我们将利用 btrfs send/receive 通过 SSH 将子卷直接“流”向新电脑。这种方式比 rclone 更适合克隆整个系统。

在源电脑上： 首先为当前的子卷创建只读快照（这是 send 的前提）：

```bash
# 创建临时快照
btrfs subvolume snapshot -r / /root_backup
btrfs subvolume snapshot -r /home /home_backup
sync

# 后续迁移完成后，可删除源电脑的零时快照
# sudo btrfs subvolume delete /root_backup
# sudo btrfs subvolume delete /home_backup
# 确认是否删除成功
# sudo btrfs subvolume list /
```


在目标电脑上： 确保已安装 openssh 并临时允许 root 登录（或开启服务）。

从源电脑发起传输：

```bash
# 传输根分区
btrfs send /root_backup | ssh root@目标IP "btrfs receive /mnt"

# 传输 home 分区
btrfs send /home_backup | ssh root@目标IP "btrfs receive /mnt"
```

## 恢复子卷结构与清理

传输完成后，目标电脑的 /mnt 下会有 root_backup 和 home_backup。我们需要将它们重命名为原本的子卷名称。

在目标电脑上：

```bash
# 将只读快照转为可写子卷
btrfs subvolume snapshot /mnt/root_backup /mnt/@
btrfs subvolume snapshot /mnt/home_backup /mnt/@home

# 删除临时的只读快照
btrfs subvolume delete /mnt/root_backup
btrfs subvolume delete /mnt/home_backup

# 重新挂载到正确的位置
umount /mnt
mount -o subvol=@ /dev/nvme0n1p3 /mnt
mkdir /mnt/home
mount -o subvol=@home /dev/nvme0n1p3 /mnt/home
mkdir -p /mnt/boot/efi
mount /dev/nvme0n1p1 /mnt/boot/efi
```

## 驱动与配置调整

更新 fstab：由于新硬盘的 UUID 发生了变化，必须更新配置文件。

```bash
# 更新 fstab (因为 UUID 变了)
# https://wiki.archlinux.org/title/Genfstab
genfstab -U /mnt > /mnt/etc/fstab
```

由于硬件改变，你需要进入新系统的 chroot 环境更新配置。

```bash
# 进入环境
arch-chroot /mnt
```

以下操作在chroot环境下执行：

重新安装内核：
运行以下命令。这会下载内核文件并将其放入 /boot，同时触发 mkinitcpio 钩子。因为你不需要原电脑的驱动，重新安装内核会自动根据当前硬件（或使用通用配置）生成新的 initrd。

```bash
pacman -Syu linux linux-firmware
```
注意： 如果你使用的是其他内核（如 linux-lts 或 linux-zen），请替换相应包名。

执行完这一步后，/boot/vmlinuz-linux 就会出现

```bash
# 移除旧驱动
# Arch 默认不安装特定驱动（除非你手动装了 nvidia 等）。
# 如果有 nvidia，建议卸载： pacman -Rs nvidia
# 安装通用或新硬件驱动：
# pacman -S mesa xf86-video-amdgpu  # 示例：如果是转到 AMD 显卡

# 重新生成 initramfs (这一步会扫描新硬件并包含所需模块)
mkinitcpio -P

# 重新安装 GRUB 引导
grub-install --target=x86_64-efi --efi-directory=/boot --bootloader-id=GRUB

# 重新生成 GRUB 配置
grub-mkconfig -o /boot/grub/grub.cfg
```

## 其他：删除 btrfs assistant 创建的快照设置

在 Btrfs 系统迁移后，出现 Deleting config failed (deleting snapshot failed) 错误，可以按照以下步骤通过“强制手动清理”的方式解决：

```shell
snapper list-configs
sudo snapper -c <配置名称> delete-config

# 如果命令删除失败，还可以手动删除：
# 删除配置文件
sudo rm /etc/snapper/configs/<config_name>
# 删除配置名
sudo vim /etc/conf.d/snapper
# 内容为 SNAPPER_CONFIGS=""

# 重启服务
sudo systemctl restart snapperd

# 重新创建 root 配置（推荐在 btrfs assistant 创建）
# https://github.com/SHORiN-KiWATA/ShorinArchExperience-ArchlinuxGuide/wiki/%E5%BF%AB%E7%85%A7#snapper
# sudo snapper -c root create-config /
```