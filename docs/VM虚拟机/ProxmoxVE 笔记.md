Based on Proxmox Virtual Environment 7.0-11

## 修改主机IP地址

参考：https://zhuanlan.zhihu.com/p/354038479

修改下面的3个文件，把其中的IP地址改成你网络中可用的静态IP地址，重启后生效。

```
/etc/network/interfaces
/etc/issue
/etc/hosts
```

## 设置 TUNA 镜像源

参考：[Proxmox 镜像使用帮助](https://mirrors.tuna.tsinghua.edu.cn/help/proxmox/)

## 常用路径

```sh
# 镜像路径
/var/lib/vz/template/iso

# 虚拟机配置文件路径
/etc/pve/qemu-server

```

## 避免循环引导

```sh
echo "options kvm ignore_msrs=Y" >> /etc/modprobe.d/kvm.conf && update-initramfs -k all -u
```



## 强制关闭虚拟机

如果有时无法通过GUI关闭虚拟机，可以用命令行强行关闭。[参考](https://www.cnblogs.com/faberbeta/p/proxmox-qemu-01.html)

```sh
ls -l /run/lock/qemu-server
# 101 是目标虚拟机代号
rm -f /run/lock/qemu-server/lock-101.conf
qm unlock 101
qm stop 101
qm status 101
```



## 重设 root 账户密码

参考：https://pve.proxmox.com/wiki/Root_Password_Reset

```sh
# Remount / as Read/Write
mount -rw -o remount /
# Change the root account password with
passwd
# Change any other account password with
passwd username
# type new password, confirm and hit enter and then reboot.
```



## 删除虚拟磁盘

在删除之前，请先在【虚拟机/硬件】设置中将磁盘分离。

```sh
# 查看所有虚拟磁盘
lvs

# 输出如下：
root@pve:~# lvs
  LV                                VG  Attr       LSize    Pool Origin          Data%  Meta%  Move Log Cpy%Sync Convert
  base-101-disk-0                   pve Vri---tz-k   64.00g data                                                        
  data                              pve twi-aotz-- <795.77g                      11.08  0.78                            
  root                              pve -wi-ao----   96.00g                                                             
  snap_vm-100-disk-0_Init_NoDrivers pve Vri---tz-k  128.00g data vm-100-disk-0                                          
  snap_vm-104-disk-0_InitInstall    pve Vri---tz-k    4.00m data vm-104-disk-0                                          
  snap_vm-104-disk-1_InitInstall    pve Vri---tz-k  128.00g data vm-104-disk-1                                          
  swap                              pve -wi-ao----    7.00g                                                             
  vm-100-disk-0                     pve Vwi-a-tz--  128.00g data                 13.77                                  
  vm-102-disk-0                     pve Vwi-a-tz--   64.00g data base-101-disk-0 25.30                                  
  vm-103-disk-0                     pve Vwi-a-tz--  128.00g data                 7.31                                   
  vm-103-disk-1                     pve Vwi-a-tz--    4.00m data                 3.12                                   
  vm-103-disk-2                     pve Vwi-a-tz--   32.00g data                 12.78                                  
  vm-103-disk-3                     pve Vwi-a-tz--   32.00g data                 0.00                                   
  vm-104-disk-0                     pve Vwi-a-tz--    4.00m data                 3.12                                   
  vm-104-disk-1                     pve Vwi-a-tz--  128.00g data                 25.50 

# 假设 vm-103-disk-3 是需要删除的磁盘，使用 lvremove 命令删除。
lvremove pve/vm-103-disk-3
```



## 移动虚拟机中的磁盘到另一个虚拟机

参考：https://pve.proxmox.com/wiki/Moving_disk_image_from_one_KVM_machine_to_another

LVM存储：

> 假设原虚拟机编号是 `400`，目标虚拟机编号是 `2300`，`mala` 是示例主机名

查看所有磁盘

```sh
lvs
#(...)
#vm-400-disk-1 pve Vwi-aotz--   42.00g
```

在虚拟机配置文件中，找到磁盘名：

```sh
cat /etc/pve/nodes/mala/qemu-server/400.conf | grep lvm
#scsi1: local-lvm:vm-400-disk-1,size=42G
```

有两个关键步骤来移动磁盘。第一步是 根据目标虚拟机 重命名逻辑卷：

```sh
lvrename pve/vm-400-disk-1 pve/vm-2300-disk-1
#Renamed "vm-400-disk-1" to "vm-2300-disk-1" in volume group "pve"
```

第二部是修改原来的虚拟机设置文件，移除原虚拟机的磁盘

```sh
sed -i.backup '/vm-400-disk-1/d' /etc/pve/nodes/mala/qemu-server/400.conf
```

然后把磁盘添加到目标虚拟机，磁盘名字是之前用 `lvrename` 重命名过后的

```sh
echo "scsi1: local-lvm:vm-2300-disk-1,size=42G" >> /etc/pve/nodes/mala/qemu-server/2300.conf
```

完成！

## Win10 VM 独显直通（Intel 机型）

前置条件：主机必须在 BIOS 中开启【虚拟化技术】和【VT-d】。

插入独显后必须先启用核显并将核显设置为默认输出设备。[参考](https://www.bilibili.com/video/BV1si4y1d73r/)

```sh
# 编辑启动参数
vim /etc/default/grub

# 修改下面这行
# GRUB_CMDLINE_LINUX_DEFAULT="quiet"
# 如果是 AMD CPU 可以设置 amd_iommu=on，不过没试过。
GRUB_CMDLINE_LINUX_DEFAULT="quiet intel_iommu=on iommu=pt pcie_acs_override=downstream,multifunction nofb textonly nomodeset video=efifb:off"

# 重新生成 grub 配置文件
# 等同于这条命令：grub-mkconfig -o /boot/grub/grub.cfg
update-grub

# 重启生效。重启之后可能不会有显示输出，除非在虚拟机中设置了显卡直通。
```

虚拟机配置文件参考：

```conf
agent: 1
bios: ovmf
boot: order=sata0;sata1;ide2
cores: 4
efidisk0: local-lvm:vm-103-disk-1,size=4M
hostpci0: 0000:00:02,pcie=1,x-vga=1  # 直通的显卡，可以在【硬件】设置中添加。勾选`所有功能`、`主GPU`、`PCI-Express`
ide2: local:iso/Win10PE_Ver.3.7.1.iso,media=cdrom
machine: pc-q35-6.0  # 必须使用 q35 机型，才能开启 `PCI-Express`
memory: 4096
name: Win10-1
net0: virtio=A2:0E:B3:BE:E4:38,bridge=vmbr0,firewall=1
numa: 0
ostype: win10
sata0: local-lvm:vm-103-disk-0,size=128G,ssd=1
sata1: local-lvm:vm-103-disk-2,size=32G,ssd=1
scsihw: virtio-scsi-pci
smbios1: uuid=6d14343b-e888-41b6-b984-7d2064b77969
sockets: 1
unused0: local-lvm:vm-103-disk-3
vga: virtio
vmgenid: 75c18187-16a7-4c01-9d8e-16b4e6ca0df8
```

可能需要将虚拟显卡设置为【无】才能正常启用显卡。

虚拟显卡禁用以后无法进行虚拟机的控制台 VNC 连接，建议直通 USB 键鼠以进行后续操作。



## KVM-Hackintosh 安装流程

参考：

- https://www.nicksherlock.com/2021/10/installing-macos-12-monterey-on-proxmox-7/
- https://www.bilibili.com/video/BV1uq4y1g7ui
- https://www.bilibili.com/video/BV1ML411E7eH
- https://www.bilibili.com/video/BV1si4y1d73r
