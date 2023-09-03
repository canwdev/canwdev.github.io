
### Linux 安装 VMware Workstation 虚拟机

到官网下载 Linux 二进制文件：[VMware-Workstation-Full-15.5.6-16341506.x86_64.bundle](https://download3.vmware.com/software/wkst/file/VMware-Workstation-Full-15.5.6-16341506.x86_64.bundle)

```sh
chmod +x *.bundle
./VMware-Workstation-Full-15.5.6-16341506.x86_64.bundle
```

- Q: Directory must be non-empty System service scripts directory (commonly /etc/init.d)
- A: sudo mkdir `/etc/init.d`

---

启动 VMware，如果出现【VMware Kernel Module Updatert】弹窗，则需要：`sudo pacman -S linux-headers`，选择对应的版本安装，比如我的是 `linux54-headers`。安装完成后重新打开 VMWare 就可以了。更多说明请查看 [Arch VMware 文档]([https://wiki.archlinux.org/index.php/VMware_(%E7%AE%80%E4%BD%93%E4%B8%AD%E6%96%87)](https://wiki.archlinux.org/index.php/VMware_(简体中文))

[[Arch Linux 安装 VirtualBox 虚拟机]]

### VMWare vmdk 拆分与合并

> **vmware-vdiskmanager.exe** 的位置在：`C:\Program Files (x86)\VMware\VMware Workstation\vmware-vdiskmanager.exe`

#### 多个镜像合并为一个

```sh
# vmware-vdiskmanager -r <原文件路径(含文件名)> -t 0 <合并后文件路径(含文件名)>

vmware-vdiskmanager.exe -r "D:\VM\VMW7\Windows 7.vmdk" -t 0 "D:\VM\Win7-single.vmdk"
```

#### 一个镜像拆分为多个

```sh
# vmware-vdiskmanager -r <原文件路径(含文件名)> -t 1 <分割后文件路径(含文件名)>

vmware-vdiskmanager -r G:\ubuntu\Ubuntu.vmdk -t 1 G:\ubuntu\ubuntu2.vmdk
```

### VMware Workstation 与 Device/Credential Guard 不兼容

> VMware Workstation 与 Device/Credential Guard 不兼容。在禁用 Device/Credential Guard 后，可以运行 VMware Workstation。

这往往是因为开启了 Hype-V 功能导致的，先关闭 Hyper-V，然后在命令行以管理员身份执行：`bcdedit /set hypervisorlaunchtype off`，重启电脑。

### Arch Linux中使用VMware Workstation不能打开vmmon内核模块

https://www.cnblogs.com/zhuxiaoxi/p/8423544.html

解决方法1

你可以在启动VMware前运行`/etc/init.d/vmware start`来启动服务

解决方法2

在Arch Linux上可以通过安装`vmware-systemd-serverices`这个AUR包，来添加systemctl服务

- 使用`systemctl enable vmware.service`让它每次开机都运行
- 使用`systemctl start vmware.service`让它临时启动

解决方法3

添加这个文件
*/etc/systemd/system/vmware.service*

```
[Unit]
Description=VMware daemon
Requires=vmware-usbarbitrator.service
Before=vmware-usbarbitrator.service
After=network.target

[Service]
ExecStart=/etc/init.d/vmware start
ExecStop=/etc/init.d/vmware stop
PIDFile=/var/lock/subsys/vmware
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

- 使用`systemctl enable vmware.service`让它每次开机都运行
- 使用`systemctl start vmware.service`让它临时启动

### Manjaro(ArchLinux) 客户机安装 VMware Tools

```sh
sudo su
pacman -Syu
reboot

pacman -S open-vm-tools
systemctl enable vmtoolsd
systemctl enable vmware-vmblock-fuse
reboot
```


## 解决 Windows7 客户机无法安装 VMware 16+ Tools

- 方案1：使用旧版 VMware 15.5 tools
	- [网址](http://softwareupdate.vmware.com/cds/vmw-desktop/ws/15.5.0/14665864/windows/packages/)，下载并解压 tools-windows.tar
	- 解压得到 VMware-tools-windows-11.0.0-14549434.iso
- 方案2：安装补丁：kb4474419
	- 需要启用 Windows Update 服务，部分精简系统可能安装失败
	- 下载地址： https://www.catalog.update.microsoft.com/Search.aspx?q=kb4474419.


---

- [去虚拟化教程](https://www.bilibili.com/video/BV1Qh4y1Q7pk/)