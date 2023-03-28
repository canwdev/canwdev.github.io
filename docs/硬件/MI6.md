# MI 6 刷机日志

## Win10 问题

时间：20220801

刷入 Win10 ARM 后，切换至 Android 可能会导致的问题：

- 系统时钟可能不准，即使在 Android 中重新设置，重启后不会保存
- ? 重启进入 Android，蓝牙可能无法打开

解决方案：

1. 恢复原始分区
2. 线刷原厂包

> [!Info]
> 造成时间重启不保存的原因，可能是主板时钟电池电量耗尽，与 Windows 系统无关。

---

为了应对 Android 默认开启的加密，你需要一个 OTG HUB 和 U 盘

---

关于 MI6 蓝牙停止的问题，目前刷 MIUI 不会出现，可能是刷 10.0 以的类原生会出现（第一次启动可以用蓝牙，但是重启之后打开蓝牙就会停止）。

> [!Warning] 找到原因
> 刷入系统重启之后，如果再刷入任意一个包（如magisk或官方root），必然会导致蓝牙闪退！ 
> 原因：系统开启了 SELinux，再次刷包破坏了系统的稳定性
> 解决方案：在开发者模式中启用 root 授权：仅限于 ADB 后，关闭 SELinux。
> 或者，在刷入系统之后立即刷入root包，并且在以后的日常使用中不再刷入其他包。




如何关闭 SELinux

**adb shell getenforce**

查看当前 Selinux 功能是 **permissive**(关闭)还是 **enforce**(打开)的

**adb shell setenforce 0**

开Selinux：设置成模式permissive

**adb shell setenforce 1**

关Selinux：设置成模式enforce

说明：setenforce 修改的状态在`设备重启后会失效`，需要重新执行命令重新设置。

---

TWRP -> Advanced -> Fix Contexts 没用