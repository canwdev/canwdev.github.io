## 1. 给新的磁盘分区

使用 `KDE Partition Manager` 或 `gparted` 等 GUI 工具进行分区操作。命令行可以使用 `fdisk` 或 `gdisk`。

一般来说创建一个 32G 的 ext4 分区就够了。具体操作细节略。


## 2. 使用 rsync 拷贝系统文件到新的分区

注意：需要在 Live 环境下执行操作，不能在原系统启动的情况下操作。

```sh
rsync -avrh --progress /mnt/os_old/ /mnt/os_new/
```

## 3. 修改配置文件的 UUID

新的分区和原来的分区 UUID 是不同的，为了让系统正常启动，需要修改这几个文件：

- `/etc/fstab`
- `/boot/grub/grub.cfg` —— 这个文件虽然是自动生成的，但为了方便起见也可以手动修改

用 `vim /etc/fstab` 打开，可以看到里面像这样：

```
# /etc/fstab: static file system information.
#
# Use 'blkid' to print the universally unique identifier for a device; this may
# be used with UUID= as a more robust way to name devices that works even if
# disks are added and removed. See fstab(5).
#
# <file system>             <mount point>  <type>  <options>  <dump>  <pass>
UUID=45a8f854-55c1-435b-b37e-8cfce8f8a6b2 /              ext4    defaults,noatime 0 1
```

其中 `45a8f854-55c1-435b-b37e-8cfce8f8a6b2` 就是旧分区 UUID 值了，需要把它换成新分区的值。

查看分区 UUID 命令，有多种方式：

- `sudo blkid`
- `ls -l /dev/disk/by-uuid`

用任意一种，确定新分区的 UUID 然后替换上面两个文件的旧 UUID 就可以了。

## 4. 修复 GRUB 引导

### 4.1 修复 GRUB MBR 引导扇区

> 也适用于任何磁盘丢失 MBR 引导的问题

1. 使用光盘镜像启动到 Live 环境。

2. 终端运行 `lsblk` 命令找到目标系统磁盘（例如 `/dev/sda`），和包含系统的分区（例如 `/dev/sda1`）。

3. 挂载系统，并进入 `chroot` 环境：

   ```sh
   sudo su
   mount /dev/sda1 /mnt/system
   mount -t proc proc /mnt/system/proc
   mount -t sysfs sys /mnt/system/sys
   mount -o bind /dev /mnt/system/dev
   chroot /mnt/system/
   # 现在已经进入了 chroot 环境，可以看到当前根目录 `/` 下的文件都是原来文件系统里的文件。
   ```

4. 在 chroot 环境执行 `grub-install /dev/sda` ，为该磁盘安装 GRUB MBR 引导程序。

### 4.2 修复 GRUB EFI 引导

挂载分区

```sh
sudo mkdir /mnt/bootfix
sudo mount /dev/nvme0n1p3 /mnt/bootfix
sudo mount /dev/nvme0n1p1 /mnt/bootfix/boot/efi
for i in /dev /dev/pts /proc /sys /run; do sudo mount -B $i /mnt/bootfix$i; done
```

使用 chroot 修复引导

```
sudo chroot /mnt/bootfix
grub-install /dev/nvme0n1
```

如果报错：

```
正在为 x86_64-efi 平台进行安装。
EFI variables are not supported on this system.
EFI variables are not supported on this system.
grub-install：错误： efibootmgr failed to register the boot entry: 没有那个文件或目录.
```

```
# 退出到系统终端
exit
# 执行这条命令
sudo mount --bind /sys/firmware/efi/efivars/ /mnt/bootfix/sys/firmware/efi/efivars/
# 再次进入 chroot
sudo chroot /mnt/bootfix
# 重新修复引导
grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=grub --recheck
```

安装成功：

```
正在为 x86_64-efi 平台进行安装。
安装完成。没有报告错误。
```

后续工作：

```sh
# 更新grub设置
grub-mkconfig -o /boot/grub/grub.cfg 

# 或者使用 `update-grub`，其实这条命令就是封装了上一条命令的 shell 脚本
```
