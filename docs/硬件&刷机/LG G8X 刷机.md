更新于 2024/06/28

## LG G8X 通用教程
### LG G8X 如何进入9008

1. 开机状态下，连接usb线到电脑，长按电源键和音量下键关机
2. 在关机黑屏的一瞬间（不要松开电源键和音量下键），疯狂快速按音量加键！
3. 如果出现开机 Logo，则失败！请重复1、2步骤！
4. 如果黑屏，设备管理器中端口（COM）出现9008设备，则成功！

> [!WARNING] 9008 刷机会救砖操作会破坏基带，如果要进行救砖，请提前备份基带所在的几个分区！
#### 教学视频，G8X 同样适用：

如何进入9008： https://www.bilibili.com/video/BV1rB4y1N7BM/
如何进入fastboot： https://www.bilibili.com/video/BV193411s74D
### LG G8X 如何进入 fastboot

- 请插入数据线长按电源键和音量减，黑屏时松开电源键和音量减，按住音量加，进 入Fastboot模式。
- 也可以在插入数据线并且重启状态下按住音量加键进入fastboot

### LG G8X 如何进入 recovery

- 请插入数据线长按电源键和音量减，黑屏时松开电源键和音量减，按住音量加，进 入Fastboot后按音量键直到屏幕左上方显示“Press_volume_key_to_select...”，然后按电源键确认，将设备进入Recovery。
- adb reboot recovery
- https://forum.xda-developers.com/t/unofficial-twrp-recovery-twrp-3-3-1-0.4201783/
### TWRP 触摸屏不可用

- 请外接 USB 鼠标进行操作。
- 提示：你可以把刷机包放在sd卡中（/external_sd）刷机。

## LG G8X WoA (Windows on ARM) 教程

### LG G8X 刷入 Windows 11 ARM

- 使用 [Mindows](https://mindows.cn/) 工具箱可自动化完成绝大部分操作
	- win11 镜像使用 22H2(22621.1485) 成功进入系统 [uupdump](https://uupdump.net/)
- 手动教程 [Icesito68/Port-Windows-11-Lge-devices: Based on POCO X3 Pro tutorial.](https://github.com/Icesito68/Port-Windows-11-Lge-devices/tree/Lg-G8x)

### LG G8X 刷入 WoA 后无法进入 Recovery

请使用【MindowsWOA工具包】中的【Mindows一键切换】切换回Android系统（记得放置Android系统的boot.img在工具目录），切回Android后，再尝试进入recovery模式。

### Android 切回 Windows

- 安装 [Mindows助手APP](https://www.123pan.com/s/8eP9-KDTGA)，根据软件内教程操作（放入设备的uefi.img到指定位置）
- 进入 TWRP，切换到ab分区的另一个分区，比如你在a分区，则切换到b分区重启

### G8X 如何进入 Mindows工具箱 的大容量存储模式

1. 首先进入 `fastboot`，参考上面的教程
2. 使用 Mindows工具箱V8 的【`进入大容量模式`】功能
3. 选择【`3.刷入 (会覆盖当前Boot. ab分区设备将刷入当前槽位)`】，目前（2024.1.21）还不支持 `UEFI` 菜单进入和 `fastboot` 临时启动
4. 刷入成功后重启设备，此时会卡在卡机 logo，连接电脑会显示很多硬盘，说明进入了大容量模式
5. 此时你可以备份 Windows 系统，或重刷 Windows
6. 完成上面的操作后，重启仍然会进入大容量模式，因为我们已经替换了 `boot`，此时需要进入 `fastboot` 模式重新刷入 `UEFI`
7. 同时长按电源键、音量加、音量减，直到设备重启，然后按住音量加进入 `fastboot`
8. 选择 Mindows 工具箱的【`刷入或临时启动UEFI`】功能，选择【`1.刷入UEFI到boot分区(ab分区设备则刷入当前槽位)`】，然后重启即可

### ~~刷入最新 UEFI 镜像~~（不推荐）

> [!WARNING]
> 以下镜像实测不如 Mindows 工具箱的内置 UEFI 镜像，仅供实验使用

| File Name              | Target Device | Description                                                                                                                                                                              |
| ---------------------- | ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| lg-mh2lm.img           | Lg G8x        | It's the usual uefi                                                                                                                                                                      |
| lg-mh2lmGPUOC.img      | Lg G8x        | The GPU frequency has been increased to 800MHz, voltages have not been modified so it is safe, still use it at your own risk                                                             |
| lg-mh2lmCPUPATCHED.img | Lg G8x        | It has a patch that runs the main core at 2.7GHz **(Warning, the power consumption is huge using this uefi, it is safe, but the battery consumes much faster, use it at your own risk)** |

到 [Releases · woa-lge/msmnilePkg](https://github.com/woa-lge/msmnilePkg/releases) 项目，下载 `lg-mh2lm.img` 或 `lg-mh2lmGPUOC.img`(超频) 镜像，放置在工具箱的以下位置（记得备份原文件！）
```
Mindows工具箱V8_lgg8x\bin\res\mh2lm\usr\uefi.img
```
然后通过上述【`刷入或临时启动UEFI`】功能刷入即可。

### 更新最新驱动

参考 [Updating drivers](https://github.com/Icesito68/Port-Windows-11-Lge-devices/blob/Lg-G8x/guide/English/update.md) 步骤：

1. 将手机启动到 Windows
2. 下载并解压 g8x 的驱动：[Release Drivers · Icesito68/Port-Windows-11-Lge-devices](https://github.com/Icesito68/Port-Windows-11-Lge-devices/releases/tag/Drivers)
3. 在手机上运行 `OnlineUpdater.cmd` 脚本
4. 根据提示授权完成驱动安装
5. 如果看到任何 **App Packages** 的安装报错，请忽略
6. 安装完成后重启手机即可完成


