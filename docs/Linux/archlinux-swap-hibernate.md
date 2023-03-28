---
title: ArchLinux 开启swap分区与休眠
date: 2021-08-07 23:24:15
categories:
  - technology
  - manual
tags:
  - Linux
---

参考：

- [Archlinux Hibernating（休眠） - WEREWOLFGHOST - 博客园 (cnblogs.com)](https://www.cnblogs.com/WEREWOLFGHOST-Zedekiah/p/6347123.html)
- [Swap (简体中文) - ArchWiki (archlinux.org)](https://wiki.archlinux.org/title/Swap_(简体中文))


## 激活 swap

首先需要有一个swap分区，可以使用 KDE Partition Manager 创建分区。

创建过程略。

查看是否有 Linux swap 分区：`sudo fdisk -l`。示例输出如下结果：

```
...略...
Device             Start        End    Sectors   Size Type
/dev/nvme0n1p1      2048     616447     614400   300M EFI System
/dev/nvme0n1p2    616448     878591     262144   128M Microsoft reserved
/dev/nvme0n1p3    878592  269316095  268437504   128G Linux filesystem
/dev/nvme0n1p4 269316096  286095359   16779264     8G Linux swap
...略...
```

可以看到 `/dev/nvme0n1p4` 是 swap 分区。

查看该分区的 UUID：`sudo blkid`。输出如下：

```
...略...
/dev/nvme0n1p4: UUID="889cbc57-96b5-4e7d-8e27-549221dc9ace" TYPE="swap" PARTUUID="356879a9-5556-6240-8023-8b25dd2c2f41"
...略...
```

编辑 `sudo vim /etc/fstab`，添加如下内容，其中的UUID是上述查询到的。

```
UUID=889cbc57-96b5-4e7d-8e27-549221dc9ace       none    swap    defaults        0       0
```

重启即可激活swap。

## 查看 swap 激活后的效果

要检查交换空间的状态，使用 `swapon --show`

```
NAME           TYPE      SIZE USED PRIO
/dev/nvme0n1p4 partition   8G   0B   -2 
```

显示物理内存以及交换使用情况 `free -h`：

```
               total        used        free      shared  buff/cache   available
Mem:            30Gi       2.4Gi        25Gi       475Mi       3.5Gi        27Gi
Swap:          8.0Gi          0B       8.0Gi
```

## 启用休眠

1. **配置 grub**

编辑 grub 配置，添加启动参数 `sudo vim /etc/default/grub`：

添加 `resume=UUID=`，从交换分区恢复休眠

```
...略...
GRUB_CMDLINE_LINUX_DEFAULT="resume=UUID=889cbc57-96b5-4e7d-8e27-549221dc9ace apparmor=1 security=apparmor udev.log_priority=3"
...略...
```

更新 grub.cfg 配置文件：`sudo grub-mkconfig -o /boot/grub/grub.cfg`

2. **配置 initramfs**

编辑文件 `sudo vim /etc/mkinitcpio.conf`

按 `shift-g` 跳转到文件底部，修改 `HOOKS=` 的内容，在 `filesystems` 之前添加 `resume`

```
...略...
HOOKS="base udev resume autodetect modconf block keyboard keymap filesystems fsck"
...略...
```

重新生成[initramfs](https://wiki.archlinux.org/title/Mkinitcpio_(%E7%AE%80%E4%BD%93%E4%B8%AD%E6%96%87))：`mkinitcpio -p linux`

重启，即可拥有休眠功能。
