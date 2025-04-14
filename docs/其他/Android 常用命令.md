
- 下载 [SDK 平台工具(adb/fastboot等工具)](https://developer.android.com/studio/releases/platform-tools)

## adb 常用命令

```sh
# 重置 adb 服务
adb kill-server

# 参考：https://github.com/jaredrummler/android-shell-scripts
# 快速重启
setprop ctl.restart zygote

# 重启至 bootloader
reboot bootloader

# 重启至 recovery
setprop ctl.start pre-recovery
sleep 3
reboot recovery # fallback

# 重启
setprop sys.powerctl reboot
sleep 3
reboot # fallback

# 重启 SystemUI
service call activity 42 s16 com.android.systemui
am startservice -n com.android.systemui/.SystemUIService

# 关机
setprop sys.powerctl shutdown
sleep 3
reboot -p # fallback
```

### 开启网络 adb 调试 

```sh
# 用 USB 线将设备连接到电脑
# 为了确保设备已连接，可以先在 adb shell 中查看设备 ip 地址
adb shell
$ ifconfig
$ exit

# 开启网络调试，监听在 5555 端口
adb tcpip 5555

# 连接网络adb
# 如 adb connect 192.168.1.103:5555
adb connect IP地址[:端口号]
```



## fastboot 常用命令

### 使用 fastboot 刷入 Recovery

```sh
# 查看设备列表
fastboot.exe devices
# 刷入 recovery 到 recovery 分区
fastboot.exe flash recovery recovery.img
# 立即引导 recovery
fastboot.exe boot recovery.img
```

### a/b 分区的设备，获取当前所在分区 slot

```sh
# 该命令将返回当前活动的分区，例如 "current-slot: a" 或 "current-slot: b"。其中，“a”或“b”表示设备当前活动的分区，而备用分区是未激活的另一个分区。
fastboot getvar current-slot
```

### a/b 分区的设备，如何切换 ab 分区

```sh
# 该命令将返回当前活动的分区，例如 "current-slot: a" 或 "current-slot: b"。其中，“a”或“b”表示设备当前活动的分区，而备用分区是未激活的另一个分区。
fastboot getvar current-slot

# 输入以下命令来切换到备用分区
fastboot --set-active=b

# 输入以下命令来重启设备
fastboot reboot
# 设备将重启并进入新的活动分区
```

## 禁用 Android 9 (P) 中的[旋转建议](https://source.android.google.cn/devices/tech/display/rotate-suggestions?hl=zh-cn)

```sh
adb shell settings put secure show_rotation_suggestions 0
```

## 去除 Android Wi-Fi 图标的感叹号

此命令支持 Android 11.x 及以上版本

```
adb shell settings put global captive_portal_mode 0
adb shell settings put global captive_portal_https_url https://via.moe/generate_204
```

此命令支持 Android 10.x/9.x/8.x/7.x

```sh
# 删除（删除默认用 HTTPS ）  
adb shell settings delete global captive_portal_https_url  
adb shell settings delete global captive_portal_http_url  
# 设置一个可用地址  
adb shell settings put global captive_portal_http_url http://developers.google.cn/generate_204  
adb shell settings put global captive_portal_https_url https://developers.google.cn/generate_204
```

Android 5.0 - 6.0

```sh
# 删除地址就可以恢复默认的谷歌服务器  
adb shell settings delete global captive_portal_server  
# 设置一个可用地址  
adb shell settings put global captive_portal_server http://developers.google.cn/generate_204  
# 查询当前地址  
adb shell settings get global captive_portal_server
```

**注意**：执行完后请打开飞行模式后再关闭即可生效

## 修改 NTP 服务器以同步时间

```sh
adb shell "settings put global ntp_server ntp.ntsc.ac.cn"
```
这是中科院提供的NTP服务，如果对速度不满意可以改成阿里的ntp：`ntp.aliyun.com`，ntp后加数字一共可以到：`ntp7.aliyun.com`，总共8个域名。

## Nokia N1 开启 OTG 命令

> 注：开启后在重启之前都不能充电。

```shell script
echo A > /sys/kernel/debug/usb/dwc3_debugfs_root/otg_id
```

## build.prop 优化代码

```sh
# Disables logcat
logcat.live=disable

# Disable Automatic Error Reporting
profiler.force_disable_err_rpt=1
profiler.force_disable_ulog=1
ro.kernel.checkjni=0
ro.kernel.android.checkjni=0
persist.android.strictmode=0

# Faster boot.
ro.config.hw_quickpoweron=true

# 关闭开机动画
debug.sf.nobootanimation=1

# 低内存模式
# https://source.android.com/devices/tech/perf/low-ram
ro.config.low_ram=true
```

## 如何关闭 SELinux

```sh
# 查看当前 Selinux 功能是 **permissive**(关闭)还是 **enforce**(打开)的
adb shell getenforce

# 开Selinux：设置成模式permissive
adb shell setenforce 0

# 关Selinux：设置成模式enforce
adb shell setenforce 1

# 说明：setenforce 修改的状态在`设备重启后会失效`，需要重新执行命令重新设置。
```

## 刷机常见问题

- 如果无法刷入，请检查
  - 设备型号与脚本判定是否一致，如果要强刷，请修改刷机包 `\META-INF\com\google\android\updater-script` 里的判定机制
  - 底包（firmware）是否达到要求，如果底包版本过低则无法刷入，建议刷入最新官方ROM以更新底包
  - TWRP 是否支持刷入该版本的Android，若不支持需刷入对应版本的 TWRP
- 如果刷入后卡第一屏（无开机动画）
  - 可能是 /data 分区出了问题，先备份数据，然后完全格式化 /data 分区，再重新刷入
  - 可能是 ROM 本身的问题
- 如果重启后总是进入 recovery
  - 可能是把 recovery.img 刷入了 boot 分区导致的
  - 可能是 boot 损坏了导致自动启动 recovery 分区
  - 线刷官方包或者卡刷上一次能用的包应该可以解决问题
