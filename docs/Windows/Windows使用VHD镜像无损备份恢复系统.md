有了这项技术，迁移系统再也不用重新安装环境了，并且备份/恢复的过程相当快（SSD）。  
  
## 1. 使用 disk2vhd 备份系统  
  
[disk2vhd](https://docs.microsoft.com/en-us/sysinternals/downloads/disk2vhd) 是微软官方工具集 [Sysinternals](https://docs.microsoft.com/en-us/sysinternals/) 中的一个小工具，下载地址：https://download.sysinternals.com/files/Disk2vhd.zip  
  
使用这个工具，可以在系统开机运行的状态下，完美的备份出一个 vhdx 文件。  
记得仅勾选 EFI 分区和系统分区，如有需要也可勾选 Prepar for use in Virtual PC，这样此镜像就可以直接再 Hyper-V 运行。  
  
![截图说明](disk2vhd.png)  
  
## 2. 系统还原  
  
备份出 vhdx 后，镜像还原主要有以下几个步骤：  
  
1. 启动至PE环境（略）  
2. 装载镜像  
3. 使用 DiskGenius 进行系统还原  
4. [[Windows-UEFI引导修复]]
  
### 装载镜像：  
  
现代的 Win10 PE（如：FirPE、WePE、飞扬时空PE），都支持右键挂载 vhdx 镜像为虚拟硬盘。  
  
![截图说明](mount-vhd.png)  
  
装载后的磁盘可以使用 DiskGenius 或系统的磁盘管理工具查看。  
  
![dg](dg.png)  
  
### 使用 DiskGenius 进行系统还原：  
  
选择虚拟磁盘的系统分区，右键 > 克隆分区  
  
![dg](dg1.png)  
  
选择目标硬盘分区（新系统分区），并确认  
  
![dg](dg2.png)  
![dg](dg3.png)  
  
  
### 修复引导  
  
PE 一般会自带引导修复工具，选择系统安装盘和EFI分区即可一键修复。推荐使用飞扬时空PE的内置工具，或手动修复：[[Windows-UEFI引导修复]]  
  
---  
  
## 备注：  
  
- 备份出来的vhdx镜像可直接用于 Hyper-V 虚拟机  
- 如果硬件差异过大，可能需要用 Dism++ 删除新系统的驱动才能正常进入系统  
- 使用 Dism++ 备份/添加/删除驱动可以省去手动安装驱动的步骤  
- 备份还原后的系统激活信息会丢失，需要重新激活
5. [[Windows迁移系统后黑屏只有鼠标的解决方案]]