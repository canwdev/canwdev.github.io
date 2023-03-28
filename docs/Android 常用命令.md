## 禁用 Android P 中的旋转建议
Android9中加入了[旋转建议](https://source.android.google.cn/devices/tech/display/rotate-suggestions?hl=zh-cn)这个东西，这个我个人不太喜欢，一般会给关了。关闭也很简单，按照aosp给出的调试命令：
```sh
adb shell settings put secure show_rotation_suggestions 0
```

## 解決 Android 狀態欄的感嘆號問題
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

### Android 5.0 - 6.0

```sh
# 删除地址就可以恢复默认的谷歌服务器  
adb shell settings delete global captive_portal_server  
# 设置一个可用地址  
adb shell settings put global captive_portal_server http://developers.google.cn/generate_204  
# 查询当前地址  
adb shell settings get global captive_portal_server
```
其他操作系統自行手動安裝對應平台 Google 的 [SDK Platform Tools](https://developer.android.com/studio/releases/platform-tools.html)
**注意**：执行完后请打开飞行模式后再关闭

## 修改NTP服务器以同步时间
```sh
adb shell "settings put global ntp_server ntp.ntsc.ac.cn"
```
这是中科院提供的NTP服务，如果对速度不满意可以改成阿里的ntp：ntp.aliyun.com，ntp后加数字一共可以到：ntp7.aliyun.com，总共8个域名。


## 网络 ADB 调试 

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


## 通过 adb 启动 shizuku

- [Shizuku 让你的应用直接使用系统 API](https://shizuku.rikka.app/zh-hans/)

```sh
adb shell sh /data/user_de/0/moe.shizuku.privileged.api/start.sh
```

## 炼妖壶

```
adb shell

# 开启 File Shuttle
pm grant com.oasisfeng.island android.permission.INTERACT_ACROSS_USERS
```

## 常用 ADB 命令


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

## 使用 fastboot 刷入 Recovery

```sh
# 查看设备列表
fastboot.exe devices
# 刷入 recovery 到 recovery 分区
fastboot.exe flash recovery recovery.img
# 立即引导 recovery
fastboot.exe boot recovery.img
```

## 刷机常见问题

- [Android ROM 在 Ubuntu 下的 system.new.dat 的解包、修改和打包](./android-rom-modify/README.md)

- 如果无法刷入，请检查
  - 设备型号与脚本判定是否一致，如果要强刷，请修改刷机包 `\META-INF\com\google\android\updater-script` 里的判定机制
  - 底包（firmware）是否达到要求，如果底包版本过低则无法刷入
  - TWRP 是否支持刷入该版本的Android
- 如果刷入后卡第一屏（无开机动画）
  - 可能是 /data 分区出了问题，先备份数据，然后完全格式化 /data 分区，再重新刷入
  - 可能是 ROM 本身的问题
- 如果重启后总是进入 recovery
  - 可能是把 recovery.img 刷入了 boot 分区导致的
  - 可能是 boot 损坏了导致自动启动 recovery 分区
  - 线刷官方包或者卡刷上一次能用的包应该可以解决问题
