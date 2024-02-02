# OnePlus 6T 刷 Windows 11 on ARM 

## 0. 一些常识

- 一加官方ROM 氢氧OS的区别
	- 氢OS（H2OS）是国内版本
	- 氧OS（OxygenOS）是海外版，有Google服务。
- 如何进入Fastboot：关机状态，拔掉数据线，按住【音量加、音量减、电源键】三个按键几秒钟后即可进入 Fastboot
- 一加 6T 是拥有 A/B 分区的设备，当前启动分区在哪个 slot 就启动那个 slot 的 boot 镜像
- 如何进入9008救砖模式：关机状态下，按住音量加和音量减，插入数据线，可以在设备管理器的端口（COM）看到：Qualcomm HS-USB QDLoader 9008

```
另注：使用了A/B分区的系统，有以下特点：
1.boot分区就是recovery，进入系统和进入rec需要用到同一个boot分区，对于刷机来说不是一件好事
2.一般刷入twrp后不会被官方rec覆盖（但要区分A/B分区）
3.A/B分区可以自由切换，一般刷入官方卡刷包时，会自动切换到另一分区启动
4.A/B分区手机的system分区，包含非A/B分区手机的boot分区和system分区的内容，即/system目录的文件实际上存放在system分区下的system目录，即system_root
5.很多工具和app可能对A/B分区手机兼容的不是很好
6.A/B分区手机刷入twrp比一般手机要麻烦
7.为什么需要提供手机内系统相同版本的boot镜像文件，因为如果twrp不和系统版本匹配可能会导致：进入系统后无法使用WiFi等功能，或者系统崩溃。
8.如果刷入twrp有问题，请用fastboot flash boot boot.img命令刷入官方boot.img（与手机内系统版本相同）即可，恢复官方boot和recovery。

(来源于网络)
```

## 1. 必须先解锁 & 抹掉所有数据

> [!WARNING] 解锁手机会抹除所有数据，因此进行此操作前请先备份！

- 开启开发者模式：设置 - 关于手机 - 狂点版本号（开启开发者模式）- 返回 - 系统 - 开发者选项 - 打开【OEM 解锁】开关 - 打开【USB调试】开关
- 电脑终端输入 `adb shell` 然后 `reboot fastboot` 重启到刷机模式
- 手机重启进入刷机模式后，电脑终端输入 `fastboot unlock bootloader`(或 `fastboot flashing unlock`) 解锁手机，按照手机提示操作
- 解锁成功后会重启，手机数据会抹除，再次设置进入开发者选项后，可以看到【OEM解锁】选项为灰色，则表明解锁成功！

## 1.1 刷入 TWRP Recovery（可选）

> [!INFO] 刷入第三方Recovery、Root 或固件等操作，需要在解锁成功之后方可执行。

- 安装 [Mindows](https://mindows.cn/) 工具箱，刷入Win11的同时也可以刷入 TWRP！
- 到官网 https://dl.twrp.me/fajita/ 下载最新版本的 twrp img 镜像。
- 安装驱动
- 重启进入刷机模式 `reboot fastboot`，或者关机后，同时按下【电源键、音量加、音量减】三个按钮

## 2. 开始安装 Windows 11 ARM

- 推荐使用 [Mindows](https://mindows.cn/) 工具箱自动刷入
- 或到 [Renegade Project](https://download.renegade-project.cn/) 网站选择对应型号下载（手动刷入）

## ❓常见问题 · FAQ

### win11 oobe 阶段提示：`计算机意外的重新启动或遇到错误。Windows安装无法继续。若要安装Windows，请单击“确定”重新启动计算机，然后安装系统。`

- 按shift+F10出命令行窗口，输入 regedit 回车
- 找到注册表`HKEY_LOCAL_MACHINE\SYSTEM\SETUP\STATUS\ChildCompletion`
- 下面有SETUP.EXE,找到后双击它，将1修改为3，然后点击确定，关机注册表编辑器
- 重新点击错误消息框的确定。电脑就会自动 重启，重新解析安装包再次进入安装系统
- [参考](https://blog.csdn.net/qq_21583077/article/details/106146157)

### 如何跳过 Win11 oobe 强制联网：

- 在首次启动出现联网界面时按下 Shift+F10 打开 cmd 窗口
- 输入`OOBE\BypassNRO.cmd`并回车，此时系统会自动重启
- 重启后就可以和以前一样离线配置。[参考视频教程](https://www.bilibili.com/video/BV1LF411578a)

### 刷入Windows 之后，Wi-Fi 在 Windows 系统下不可用

进入 PE 后，删除所有驱动再安装，[fajita.tar.gz](https://github.com/edk2-porting/WOA-Drivers/releases/download/v2.0rc2/fajita.tar.gz)
- 最新驱动：https://github.com/edk2-porting/WOA-Drivers/releases
- 参考：https://forum.renegade-project.cn/t/6t-woa-wifi/1725/2
- 可能与系统版本有关，如果不行建议更换系统版本

### 如何切换 A/B 分区

在 TWRP 下：Reboot -> Slot A/B
在 Renegade Project UEFI 下，UEFI Boot Menu -> Reboot to anther slot
在 fastboot 模式下执行： `fastboot set_active b`
[[Android 常用命令#a/b 分区的设备，如何切换 ab 分区]]

### 如何进入大容量存储模式

- 重启手机进入 Renegade Project UEFI 
- 选择 Enter Simple Init -> Mass Storage 并且连接电脑
- 稍等片刻，成功后可在资源管理器中直接访问手机的磁盘
- 此时可以配合 Mindows工具箱刷入 Windows 镜像，Dism++ 备份分区，或导入驱动

### 在 Win 系统中容易死机并进入 Qualcomm Crash Dump

禁用蜂窝网络功能，具体操作如下：
- 下载一个 Devcon.exe (64位) [Devcon 下载](https://www.lab-z.com/dddevcon/)
- 放在 `C:\Windows\System32\` 下
- 用管理员权限在cmd行执行以下命令：
```
devcon disable *DEV_02F1*`
```
- [参考视频教程](https://www.bilibili.com/video/BV1iT4y1Q7yh)

> [!WARNING] 提示
> 即便是禁用了蜂窝网络，在开启 WiFi 的情况下也容易出现 Qualcomm Crash Dump，最好还是关闭 WiFi，使用另一台Android 设备 USB 共享网络上网，以保证系统稳定性

### 如何关闭休眠

管理员权限终端执行：`powercfg -h off`

### 一加 6T 在 Win11 系统里如何充电？

使用 5V3A 充电头可以直接充电，我使用绿联 USB hub 再接一根数据线连接电脑也可进行缓慢充电。

### 如何激活 Win11 系统

使用 `HEU_KMS_Activator_v24.1.0.exe`，内置了激活和切换系统版本。

### 如何双系统

> 已经刷入 Win11，如何在不影响 Win 系统的前提下重刷 Android 系统

重启到 TWRP，格式化 data，刷入新系统，参考 [这个教程](https://renegade-project.cn/#/zh/devices/sdm845/fajita/status) 复制 Android 系统的 ab 分区，然后用 Mindows 工具箱重新刷入 UEFI 即可。

### 一加 6T 怎么备份 boot.img

> 由 ChatGPT 回答

1.  首先，需要在计算机上安装 ADB 工具和 Oneplus 6T 的 USB 驱动程序。
	- 下载 ADB 工具：[link](https://developer.android.com/studio/releases/platform-tools) 
1.  在 Oneplus 6T 上启用 USB 调试模式。要启用 USB 调试模式，请打开设置应用，然后转到“开发者选项”并启用“USB 调试”选项。
2.  将 Oneplus 6T 连接到计算机上，并通过以下命令确认设备是否成功连接：adb devices
3.  接下来，通过以下命令备份 boot.img 文件：adb shell su -c "dd if=/dev/block/bootdevice/by-name/boot of=/sdcard/boot.img"
4.  备份完成后，将 boot.img 文件从设备复制到计算机上。通过以下命令可以实现：adb pull /sdcard/boot.img <local_directory>

## 参考链接

- [Mindows工具箱](https://mindows.cn/)
- [设备支持状态](https://www.kdocs.cn/l/cjI6xbkJFxs2?f=201)
- [Windows设备支持状态](https://renegade-project.cn/#/zh/windows/state-frame.html)
- [一加6T刷postmarketOS](https://www.cnblogs.com/hupo376787/p/16461892.html)

## 2024.01.20 更新

最近我又重装了一加6T 的 WoA，以下是一些经验。

- 推荐使用 `[Luo]22635.2915.231204_A64FRE_ZH-CN.wim` 的精简版镜像
- ⚠️⚠️⚠️警告：不要更新可选更新中的高通System驱动，否则会立即 Qualcomm Crash Dump，并且重启也会无限进入，只能重刷系统
- 由于高通无线驱动不稳定，尽量不要开启 WLAN 上网，否则极其容易 Crash，建议初次进入系统立即关闭 WLAN
- [[Windows 设备如何在使用 Android 手机 USB 共享上网的情况下，在局域网进行远程桌面连接(RDP)]]
- [[RDP 使用空密码登录]]