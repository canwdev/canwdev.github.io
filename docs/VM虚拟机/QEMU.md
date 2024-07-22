## 通用

- `qemu-system-x86_64` 和 `qemu-system-x86_64w` 的区别：`qemu-system-x86_64w` 不会打开命令行窗口，但也无法看到报错信息
- 转换磁盘格式 `qemu-img.exe convert -O vdi .\win7.qcow2 .\win7.vdi`
- 创建虚拟磁盘文件 `qemu-img create -f qcow2 drive 32G`

### 加速器（accel）

支持的类型：`kvm, xen, hax, hvf, nvmm, whpx, tcg`

- `kvm` Linux 内核虚拟化加速
	- `-accel kvm`
- `hax`
	- [Intel® HAXM](https://github.com/intel/haxm)
- `whpx` Windows Hyper-V 虚拟化加速
	- `-accel whpx,kernel-irqchip=off`
- `hvf` macOS 虚拟化加速

### QEMU run Win7

- 驱动 [virtio-win-0.1.173.iso](https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/archive-virtio/virtio-win-0.1.173-9/)

```powershell
qemu-system-x86_64.exe `
-drive file=win7.qcow2,format=qcow2,if=virtio `
-drive file=virtio-win-0.1.173.iso,media=cdrom `
-machine q35 `
-m 2048M `
# -accel whpx,kernel-irqchip=off `
-cpu Nehalem \
-smp cores=2,threads=2,sockets=2 \
-smp 4 \
-accel tcg \
-device vmware-svga,vgamem_mb=128 `
-audiodev dsound,id=snd0  -device ac97,id=snd0 `
-usb -device usb-mouse -usb -device usb-tablet `
-net user -net nic,model=e1000 `
-no-fd-bootchk
```
## QEMU run WindowsXP

- 教程： https://www.youtube.com/watch?v=U5UDzgg5cHw
- qemu for windows 下载： https://qemu.weilnetz.de/w64/
- xp iso镜像下载： https://www.imsdn.cn/operating-systems/windows-xp/
- virtio驱动下载： https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/archive-virtio/virtio-win-0.1.141-1/
- 显卡驱动VBEMP.iso： https://archive.org/download/VBEMPNT

qemu 安装 xp 启动命令：
```powershell
qemu-system-i386.exe -nodefaults -rtc base=localtime -M pc,accel=whpx,kernel-irqchip=off -m 512 -display sdl -device VGA -device virtio-blk-pci,drive=boot0 -device lsi -device ac97 -netdev user,id=net0 -device virtio-net-pci,rombar=0,netdev=net0 -drive if=floppy,file=virtio-win-0.1.141_x86.vfd -drive id=boot0,if=none,file=wxp.qcw -device scsi-cd,drive=xpcd -drive id=xpcd,if=none,media=cdrom,file=zh-hans_windows_xp_professional_with_service_pack_3_x86_cd_vl_x14-74070.iso -boot d
```

安装注意：
- 初次进入安装界面，按 F5/F6 选择额外驱动
	- F5: Windows XP HAL
	- F6: VIOSTOR driver
- 进入 computer type 选择界面，选择 `Advanced Configuration and Power Interface (ACPI) PC`
- 进入 SCSI Adapter 选择界面，选择 `Red Hat VirtIO BLOCK Disk Device WinXP/32-bit`
- xp sp3序列号：`MRX3F-47B9T-2487J-KWKMF-RPWBY`

## 其他 · 参考

- [QEMU - QuickStart | Cyan's Notebook](https://cyan-io.github.io/posts/2023-07-30-qemu-quickstart/)
- [qemu已支持在Win端VirGL渲染加速/BlissOS启动效果_哔哩哔哩_bilibili](https://www.bilibili.com/video/BV1n2421Z7ZP)
- [ShaderGlass - 全局 CRT 显示器效果滤镜](https://github.com/mausimus/ShaderGlass)
	- 推荐滤镜：`crt-hyllian-3d`
	- 命令行全屏启动：`.\ShaderGlass.exe -f 1.sgp`
- [老游戏窗口化 _ 全屏的解决方法](https://sarakale.top/blog/posts/5dd1ddbf)