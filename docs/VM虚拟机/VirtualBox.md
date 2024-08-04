### Arch Linux 安装 VirtualBox 虚拟机

```sh
sudo pacman -S virtualbox
# 选择内核对应的版本安装

# 初次启动报错：Kernel driver not installed (rc=-1908)
sudo pacman -S linux-headers
sudo pacman -S virtualbox-host-dkms
sudo modprobe vboxdrv
```

### 如何在 Linux 客户机挂载 VirtualBox 共享文件夹

首先需要安装增强工具。

如果勾选了自动挂载，并设置了挂载点（如 `VMShared`），则一般来说会挂载到 `/media/sf_VMShared/`，但这个目录只有 `root` 用户或 `vboxsf` 组的用户才有权限访问（[参考](https://stackoverflow.com/a/26981786)）。

```sh
# 添加当前用户到 vboxsf 组
sudo adduser $USER vboxsf
# 如果上面那条执行失败就用这一条
sudo usermod --append --groups vboxsf $USER
```

需要重新登录或重启才能生效。

如果没有自动挂载成功，下面是手动挂载的方法：

参考：[Mounting VirtualBox shared folders on Ubuntu Server 16.04 LTS](https://gist.github.com/estorgio/1d679f962e8209f8a9232f7593683265)

首先，要确保安装了增强功能。然后在「设置-共享文件夹」中添加一个共享文件夹，勾选「自动挂载」并填入挂载点，例如「VMShared」。

到客户机，执行以下命令：

```sh
# 创建挂载目标
sudo mkdir /mnt/VMShared

# 挂载共享目录
sudo mount -t vboxsf VMShared /mnt/VMShared

# 挂载为可写，用户是 user
sudo mount -t vboxsf LinuxZone -o rw,dmode=777,gid=user,uid=user /mnt/LinuxZone1
```

这样就可以完成挂载。

## 将 VHDX 转换为 VDI

首先需要安装 [qemu](https://www.qemu.org/download/) 从而使用其内置的 `qemu-img` 转换工具，然后执行命令：
```bash
qemu-img convert -f vhdx -O vdi input.vhdx output.vdi`
```

## 备注

- 在开启了 Hyper-V 的主机，不建议设置硬件加速的半虚拟化接口为 Hyper-V，否则运行可能会更慢（保持默认即可）