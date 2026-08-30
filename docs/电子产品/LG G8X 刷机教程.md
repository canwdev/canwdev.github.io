# LG G8X ThinQ（型号 LMG850UM）刷机步骤

1. 寻找资源
2. 备份数据
3. 刷入

## 1. 寻找资源

- 下载破解版 LGUP： https://xdaforums.com/t/lgup-1-16-3-patched-setup-installer-w-lgmobile-drivers-and-common_dll.4304181
- 或者 LGROMUP 工具： https://lgrom.com/blog/lgromup
- 下载固件
  - https://lgrom.com/firmware/LMG850UM
  - https://lg-firmwares.com/downloads-file/27581/G850UM40c_00_1129


## 2. 备份数据

检查清单

- [ ] 备份内置存储
- [ ] 备份 Termux
- [ ] 备份应用程序和数据（钛备份或用 X-plore 导出 apk）
- [ ] 备份必要分区

备份内置存储

```shell
tar -czf ~/storage/ext_sd/backup_$(date +%Y%m%d_%H%M%S).tar.gz -C /sdcard Download Documents Pictures Music Movies DCIM "Mindows助手"
```

备份 Termux

```shell
# 备份
termux-backup ~/storage/ext_sd/termux_backup_$(date +%Y%m%d_%H%M%S).tar.gz
# 还原
termux-restore ~/storage/ext_sd/termux_backup_YYYYMMDD_HHMMSS.tar.gz
```

备份必要分区

```shell
su
ls -l /dev/block/by-name/
cat /proc/partitions
df -h
```

```shell
su
BACKUP_DIR="/mnt/media_rw/6C44-9EF1/essential_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo "备份目录：$BACKUP_DIR"

# ----- 必须备份（硬件校准/基带/安全） -----
dd if=/dev/block/by-name/persist    of="$BACKUP_DIR/persist.img"    bs=4M
dd if=/dev/block/by-name/persdata   of="$BACKUP_DIR/persdata.img"   bs=4M
dd if=/dev/block/by-name/modemst1   of="$BACKUP_DIR/modemst1.img"   bs=4M
dd if=/dev/block/by-name/modemst2   of="$BACKUP_DIR/modemst2.img"   bs=4M
dd if=/dev/block/by-name/fsg        of="$BACKUP_DIR/fsg.img"        bs=4M
dd if=/dev/block/by-name/frp        of="$BACKUP_DIR/frp.img"        bs=4M

# ----- 建议备份（内核/设备树/引导/验证） -----
# 当前活动槽位（默认为 _a，如需确认可运行 getprop ro.boot.slot_suffix）
dd if=/dev/block/by-name/boot_a     of="$BACKUP_DIR/boot_a.img"     bs=4M
dd if=/dev/block/by-name/dtbo_a     of="$BACKUP_DIR/dtbo_a.img"     bs=4M
dd if=/dev/block/by-name/abl_a      of="$BACKUP_DIR/abl_a.img"      bs=4M
dd if=/dev/block/by-name/vbmeta_a   of="$BACKUP_DIR/vbmeta_a.img"   bs=4M

# 备份备用槽位 _b（以防万一）
dd if=/dev/block/by-name/boot_b     of="$BACKUP_DIR/boot_b.img"     bs=4M
dd if=/dev/block/by-name/dtbo_b     of="$BACKUP_DIR/dtbo_b.img"     bs=4M
dd if=/dev/block/by-name/abl_b      of="$BACKUP_DIR/abl_b.img"      bs=4M
dd if=/dev/block/by-name/vbmeta_b   of="$BACKUP_DIR/vbmeta_b.img"   bs=4M

# ----- 备份分区布局信息（恢复参考） -----
cat /proc/partitions                > "$BACKUP_DIR/partitions.txt"
ls -l /dev/block/by-name/           > "$BACKUP_DIR/by-name.txt"
df -h                               > "$BACKUP_DIR/df.txt"
mount                               > "$BACKUP_DIR/mount.txt"
getprop ro.boot.slot_suffix         > "$BACKUP_DIR/active_slot.txt" 2>/dev/null

# ----- 生成校验文件 -----
cd "$BACKUP_DIR"
md5sum *.img > checksums.md5

echo "✅ 备份完成！"
echo "备份文件夹：$BACKUP_DIR"
ls -lh "$BACKUP_DIR"

```

## 3. 刷机

### 9008（进入不了Download Mode可尝试）

进入 9008 模式

1. 开机状态下，用 USB 线连接电脑，长按电源键和音量下键关机
2. 在关机黑屏的一瞬间（不要松开电源键和音量下键），快速连续按音量加键
3. 如果出现开机 Logo，则失败，重复第 1、2 步，多试几次一定能成功
4. 如果黑屏，且设备管理器中端口（COM）出现 9008 设备，则成功

安装 QPST_2.7.496 和 Qualcomm USB Driver V1.0.exe

网上搜索并下载9008救砖包如 `LGG8X_9008救砖包不刷基带_G850UM20j_00_OPEN_CA_OP_0416`

- 打开 QFIL
- 选择设备
- 在 Configuration -> FireHose Configuration 中确保 Device Type 设为 UFS。
- 选择 Flat Build
- Programmer Path：选择该文件夹下的 `firehose_ddr.elf` 。
- 点击右下角 Load XML...：
- 在弹出的第一个窗口，将 rawprogram0.xml 到 rawprogram6.xml 全选，点击打开。
- 在弹出的第二个窗口，选择 patch0.xml（如果文件夹里有）或取消。
- 点击 Download 按钮（没有二次确认），QFIL 会立即把所有分卷切片依次写入手机。
- 刷完后同时按下按 `音量减和电源键` 重启。

### LGUP（升级底包）并解决 OPID mismatch

如果出现 0x5319, OPID mismatch. TMO_US to OPEN_CA. ID Unlock first. [ERR : 0x2]，参考 https://xdaforums.com/t/tutorial-crossflash-bypass-opid-mismatched-error.4345963/

```
Steps
A)
1. Open QFIL.
2. Change "Storage Type" to UFS.
3. Select "Flat Build".
4. Browse for "LGE SM8150 Firehose" and pick it.
5. Now, connect the phone to PC and boot into EDL mode.
6. Open "Select Port" and select the phone, press OK.
7. In "Tools" open the "Partition Manager".

B)
!!!BE CAREFUL TO DO EXACTLY AS THE INSTRUCTIONS SAY OR YOU WILL BRICK THE PHONE!!!
1. Make a backup of and erase these 7 partitions: FTM, Modem_A, Modem_B, SID_A, SID_B, OP_A, OP_B.
1.1. You have to left-click on a partition then right-click on it and select "Manage Partition Data".
1.2. In the pop-up window, you have 4 choices: I. Erase (to erase data on the partition), II. Read Data (to dump or back up the partition), III. Load Image (to restore the partition), IV. Close (to close the window).
1.3. First dump/back up the partition by choosing "Read Data" then Erase it.
2. Close the "Partition Manager" window.
3. Wait for 5 seconds then press Vol- and Power until it restarts.
3.1. Immediately after rebooting, Release the Vol- and Power buttons and press Vol+ to get into Download Mode.
Note: Do not let the phone to begin to boot! If it begins to boot, it may regenerate the SID and FTM partitions data and so you need to redo the whole step B.

C)
1. Open LGUP.
2. Pick your favorite KDZ.
3. Select "PARTITION DL".
4. Press Start. And a pop-up window will appear. In this window you can select which partitions to be flashed.
5. Here, uncheck these partitions: SID_A and SID_B. It will make it able to bypass the OPID Mismatched Error.
6. If you are in Sprint or other platforms you will get the message whether to change the model or not. Of course you know what to do =)

after completing the process it will boot up in some minutes and before starting the customization it will do one restart. just be patient.

--- 译文： ---

步骤
A)
1. 打开QFIL。
2. 将“存储类型”更改为UFS。
3. 选择“Flat Build”。
4. 浏览并选择“LGE SM8150 Firehose”。
5. 现在，将手机连接到电脑并启动进入EDL模式。
6. 打开“选择端口”并选择手机，按“确定”。
7. 在“工具”中打开“分区管理器”。

B)
!!!务必严格按照说明操作，否则手机将变砖!!!
1. 备份并擦除以下7个分区：FTM、Modem_A、Modem_B、SID_A、SID_B、OP_A、OP_B。
1.1. 左键单击一个分区，然后右键单击并选择“管理分区数据”。
1.2. 在弹出窗口中有4个选项：I. 擦除（擦除分区数据），II. 读取数据（转储或备份分区），III. 加载镜像（恢复分区），IV. 关闭（关闭窗口）。
1.3. 首先选择“读取数据”转储/备份分区，然后将其擦除。
2. 关闭“分区管理器”窗口。
3. 等待5秒，然后同时按音量减和电源键，直到重启。
3.1. 重启后立即松开音量减和电源键，然后按音量加进入下载模式。
注意：不要让手机开始启动！如果开始启动，可能会重新生成SID和FTM分区数据，因此您需要重做整个B步骤。

C)
1. 打开LGUP。
2. 选择您喜欢的KDZ文件。
3. 选择“PARTITION DL”。
4. 按“开始”。将出现一个弹出窗口，在此窗口中您可以选择要刷写的分区。
5. 在此处取消勾选SID_A和SID_B分区。这将使其能够绕过OPID不匹配错误。
6. 如果您使用的是Sprint或其他平台，将会收到是否更改型号的提示。当然您知道该怎么做 =)

完成该过程后，手机将在几分钟内启动，并且在开始自定义之前会重启一次。请耐心等待。
```

### 刷入 abl，启用 fastboot

LG Android 12 原厂系统只有 Download Mode，下面方法可以刷入 fastboot。下载帖子中的 abl 附件。

https://xdaforums.com/t/guide-lg-g8-g8x-v50-bootloader-unlock-and-magisk-root-using-firehose.4221793/

- 进入 9008，QFIL，Partition Manager，备份 abl_a/abl_b 并刷入上述 abl_a 到 abl_a/abl_b 
	- 备份 Read Data，会自动备份到`C:\Users\user\AppData\Roaming\Qualcomm\QFIL\COMPORT_6`
	- 还原 Load Image
- 同时按下按 `音量减和电源键` 重启，然后按住 `音量加` 进入 fastboot，进设备管理器查看

此外，切换 ab 分区命令：`fastboot set_active b`

### 利用 9008 修补 boot 获取 root 权限

- 进入 9008，QFIL，Partition Manager，备份 boot_a，找到备份文件，复制并重命名为 img
- 用[柚坛工具箱](https://github.com/Uotan-Dev/UotanToolboxNT/releases)-基本刷入-修补 Boot 修补备份的 boot_a
- Partition Manager 刷入刚刚修补的 boot 文件到 boot_a/boot_b
- 重启进入系统，安装 Magisk app-debug.apk https://github.com/topjohnwu/Magisk/releases 

### 利用 magiskboot 修补 boot.img 生成 recovery.img

下载 `twrp-installer-v3.6.0-G8X_ab.zip`： https://xdaforums.com/t/unofficial-twrp-recovery-twrp-3-3-1-0.4201783/page-5 

root 后，可安装 https://github.com/capntrips/KernelFlasher 方便的备份还原 boot

首先，备份 boot.img，复制到电脑
```shell
PS D:\Programs\Android\UotanToolbox_Windows_x64_3.7.0\Bin> .\magiskboot.exe unpack "D:\Downloads\2022-09-29--20-52\boot.img"
``` 


解包后会生成 `ramdisk.cpio`、`kernel` 等文件。**替换 Ramdisk**： 将 `twrp-installer-v3.6.0-G8X_ab.zip`  解压出的 ` ramdisk-twrp.cpio ` 重命名为 `ramdisk.cpio `，覆盖替换掉解包出来的 ` ramdisk.cpio `。
```shell 
PS D:\Programs\Android\UotanToolbox_Windows_x64_3.7.0\Bin> .\magiskboot.exe repack "D:\Downloads\2022-09-29--20-52\boot.img"
``` 

会生成新的 boot.img 拷贝到手机里刷入。重启即可直接进入 recovery。

后续可使用[柚坛工具箱](https://github.com/Uotan-Dev/UotanToolboxNT/releases)-基本刷入-刷入 Recovery-临时启动 来方便的启动 recovery。

### 刷入三方ROM

完成底包升级并刷入第三方 Recovery（如 TWRP）后，可直接下载并刷入以下基于新底包开发的最新 ROM：

https://xdaforums.com/f/lg-g8x-thinq-roms-kernels-recoveries-other-de.9267/

* **[LineageOS 21.0](https://xdaforums.com/t/rom-official-14-lineageos-21-0-for-lg-g8x-v50s-mh2lm.4658472/)**（Android 14）：追求**稳定续航、零冗余**的主力系统，无多余功能，代码质量与兼容性最高，适合当日常主力机使用。
* **[crDroid 12.11](https://xdaforums.com/t/rom-16-unofficial-crdroid-12-11-for-lg-g8x-v50s-mh2lm-mh2lm_5g.4798433/)**（Android 16）/ **[crDroid 11.6](https://xdaforums.com/t/rom-unofficial-15-crdroid-11-6-for-lg-g8x-mh2lm.4751045/)**（Android 15）：兼顾**系统稳定性与高度自定义**，继承 LineageOS 底盘，内置丰富的美化控制与游戏性能调度，适合喜欢折腾和玩游戏的用户。
* **[Evolution X 11.10](https://xdaforums.com/t/rom-16-unofficial-evolution-x-11-10-for-lg-g8x-v50s-mh2lm-mh2lm_5g.4798519/)**（Android 16）/ **[AxionOS 2.8](https://xdaforums.com/t/rom-16-unofficial-axionos-2-8-oneira-for-lg-g8x-v50s-mh2lm-mh2lm_5g.4798522/)**（Android 16）：主打 **Google Pixel 视觉体验与极端个性化**，拥有最酷炫的 UI 动画、锁屏样式和深度的自定义选项，适合追求最新 Android 特性与视觉美化的玩家。

如果刷入后循环重启，记得在 recovery 中清空 data 分区。

#### 获取 zip 刷机包中的 boot.img

下载 [payload-dumper-go](https://github.com/ssut/payload-dumper-go) 解压 zip 获取 payload.bin

```shell
payload-dumper-go -p boot payload.bin
```

