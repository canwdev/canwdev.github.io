## QEMU run WindowsXP

- 教程： https://www.youtube.com/watch?v=U5UDzgg5cHw
- qemu for windows 下载： https://qemu.weilnetz.de/w64/
- xp iso镜像下载： https://www.imsdn.cn/operating-systems/windows-xp/
- virtio驱动下载： https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/archive-virtio/virtio-win-0.1.141-1/
- 显卡驱动VBEMP.iso： https://archive.org/download/VBEMPNT

qemu 安装 xp 启动命令：
```sh
qemu-system-i386.exe -nodefaults -rtc base=localtime -M pc,accel=whpx,kernel-irqchip=off -m 512 -display sdl -device VGA -device virtio-blk-pci,drive=boot0 -device lsi -device ac97 -netdev user,id=net0 -device virtio-net-pci,rombar=0,netdev=net0 -drive if=floppy,file=virtio-win-0.1.141_x86.vfd -drive id=boot0,if=none,file=wxp.qcw -device scsi-cd,drive=xpcd -drive id=xpcd,if=none,media=cdrom,file=zh-hans_windows_xp_professional_with_service_pack_3_x86_cd_vl_x14-74070.iso -boot d
```

安装注意：
- 初次进入安装界面，按 F5/F6 选择额外驱动
	- F5: Windows XP HAL
	- F6: VIOSTOR driver
- 进入 computer type 选择界面，选择 `Advanced Configuration and Power Interface (ACPI) PC`
- 进入 SCSI Adapter 选择界面，选择 `Red Hat VirtIO BLOCK Disk Device WinXP/32-bit`
- xp sp3序列号：`MRX3F-47B9T-2487J-KWKMF-RPWBY`

## Retro Games

- [ShaderGlass - 全局 CRT 显示器效果滤镜](https://github.com/mausimus/ShaderGlass)
	- 推荐滤镜：`crt-hyllian-3d`
	- 命令行全屏启动：`.\ShaderGlass.exe -f 1.sgp`
- [老游戏窗口化 _ 全屏的解决方法](https://sarakale.top/blog/posts/5dd1ddbf)