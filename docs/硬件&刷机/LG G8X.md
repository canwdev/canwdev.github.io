2023/09/23
## LG G8X 如何进入9008

1. 开机状态下，连接usb线到电脑，长按电源键和音量下键关机
2. 在关机黑屏的一瞬间（不要松开电源键和音量下键），疯狂快速按音量加键！
3. 如果出现开机 Logo，则失败！请重复1、2步骤！
4. 如果黑屏，设备管理器中端口（COM）出现9008设备，则成功！

> [!WARNING] 9008 刷机会救砖操作会破坏基带，如果要进行救砖，请提前备份基带所在的几个分区！
### 教学视频，G8X 同样适用：

如何进入9008： https://www.bilibili.com/video/BV1rB4y1N7BM/
如何进入fastboot： https://www.bilibili.com/video/BV193411s74D
## LG G8X 如何进入fastboot

- 请插入数据线长按电源键和音量减，黑屏时松开电源键和音量减，按住音量加，进 入Fastboot模式。
- 也可以在插入数据线并且重启状态下按住音量加键进入fastboot

## LG G8X 如何进入 recovery

- 请插入数据线长按电源键和音量减，黑屏时松开电源键和音量减，按住音量加，进 入Fastboot后按音量键直到屏幕左上方显示“Press_volume_key_to_select...”，然后按电源键确认，将设备进入Recovery。
- adb reboot recovery
- https://forum.xda-developers.com/t/unofficial-twrp-recovery-twrp-3-3-1-0.4201783/
## TWRP 触摸屏不可用

- 请外接 USB 鼠标进行操作。
- 提示：你可以把刷机包放在sd卡中（/external_sd）刷机。

## LG G8X Win 11 arm 专区

## LG G8X 刷入 Windows 11 ARM

- 使用 [Mindows](https://mindows.cn/) 工具箱可自动化完成绝大部分操作
	- win11 镜像使用 22H2(22621.1485) 成功进入系统 [uupdump](https://uupdump.net/)
- 手动教程 [Icesito68/Port-Windows-11-Lg-G8x: Based on POCO X3 Pro tutorial.](https://github.com/Icesito68/Port-Windows-11-Lg-G8x)

### LG G8X 刷入 WoA 后无法进入 Recovery

请使用【MindowsWOA工具包】中的【Mindows一键切换】切换回Android系统（记得放置Android系统的boot.img在工具目录），切回Android后，再尝试进入recovery模式。

### Android 切回 Windows

- 安装 [Mindows助手APP](https://www.123pan.com/s/8eP9-KDTGA)，根据软件内教程操作（放入设备的uefi.img到指定位置）
- 进入 TWRP，切换到ab分区的另一个分区，比如你在a分区，则切换到b分区重启

