# Mindows 工具箱 APK 原理

> 分析时间: 2026-07-22
> 包名: com.mindows.toolbox
> 设备: LG G8 ThinQ (mh2lm)

---

## 一、APK 总体结构

APK 采用 **Java/Kotlin + 原生 C/C++** 混合架构：

```
base.apk
├── classes.dex              ← Java/Kotlin 业务逻辑 + UI
├── lib/arm64-v8a/
│   ├── libblktool.so        ← 分区查找引擎（666KB）
│   ├── libmagiskboot.so     ← 启动镜像操作工具（616KB）
│   └── libntfs-3g.so        ← NTFS 文件系统驱动（1052KB）
└── 资源文件 (布局、图片、字符串等)
```

### UI 模块（从反编译的类名推断）

| 类 | 对应页面 | 功能 |
|----|---------|------|
| `MainActivity` | 主容器 | 四页底部导航，管理生命周期 |
| `HomeFragment` | 主页 | 当前系统状态显示、一键切换按钮、进度条 |
| `BackupFragment` | 备份 | 备份/还原当前 boot 分区镜像 |
| `DashboardFragment` | 工具面板 | 分区管理、USB 模式切换等高级功能 |
| `NotificationsFragment` | 日志 | 操作日志和通知记录 |
| `ImageActivity` | 图片 | 放大查看截图或日志截图 |

---

## 二、三个原生库详解

### 2.1 libblktool.so — 分区查找引擎

这是整个切换流程的**眼睛**，负责在复杂的 Android 分区表中精确找到目标分区。

```
Usage: blktool [FILTERS...] [FIELDS...]

Filters (查找条件):
  -N, --name NAME         按 GPT 分区名查找  ★ 最常用
  -D, --disk DISK         按磁盘号查找
  -P, --part PART         按分区号查找
  -M, --mount MOUNT       按挂载点查找
  -U, --uuid UUID         按文件系统 UUID 查找
  -L, --label LABEL       按文件系统卷标查找
  -F, --format FORMAT     按文件系统格式查找
  -B, --boot              按可启动标志查找
  -T, --type TYPE         按 GPT 类型查找
  -G, --guid GUID         按 GPT GUID 查找
  -E, --device DEVICE     按设备路径查找

Operations (操作):
  -l, --list              列出匹配的块设备
  -p, --list-part         列出匹配的分区
  -d, --list-disk         列出匹配的磁盘
  -a, --print-all         打印全部可用字段
  --print-device          打印设备路径    ★
  --print-disk            打印磁盘编号    ★
  --print-part            打印分区编号    ★
  --print-size            打印总大小
  --print-read-size       打印可读大小
  --print-sector-size     打印扇区大小
  --print-sector-count    打印扇区数
  --print-format          打印文件系统格式
  --print-uuid            打印文件系统 UUID
  --print-label           打印文件系统卷标
  --print-name            打印 GPT 名称
  --print-type            打印 GPT 类型
  --print-guid            打印 GPT GUID
  --print-mount           打印挂载点
  --print-layout          打印磁盘布局
  --print-is-bootable     打印是否可启动
  --print-is-partition    打印是否为分区
  --print-media           打印磁盘介质类型

Options (输出选项):
  -n, --no-head           不打印表头
  -j, --json              JSON 格式输出（Java 解析用）★
  -r, --raw               RAW 格式输出
  -e, --export            Shell export 格式输出
  -h, --help              显示帮助
```

**典型用法示例：**

```bash
# 查找 boot_a 分区的设备路径
blktool -N boot_a --print-device -n
# 输出: /dev/block/sde11

# 查找 boot_a 的磁盘号和分区号
blktool -N boot_a --print-disk --print-part -n
# 输出: 8 11

# JSON 格式输出所有信息
blktool -N boot_a -j
# 输出: {"name":"boot_a","device":"/dev/block/sde11","disk":"8","part":"11",...}
```

### 2.2 libmagiskboot.so — 启动镜像操作工具

这是 Magisk 项目的核心工具，负责**解包、修改、重打包** Android 启动镜像。

| 命令 | 功能 | 用途 |
|------|------|------|
| `unpack [-n] [-h] boot.img` | 解包启动镜像为 kernel, ramdisk.cpio, second, dtb 等 | 查看/修改镜像内容 |
| `repack [-n] orig.img [new.img]` | 用当前目录下的组件重打包 | 修改后重新生成 |
| `cpio ramdisk.cpio [命令]` | 对 ramdisk 执行操作（添加/提取/修补文件） | 修改 init 脚本 |
| `hexpatch file 旧hex 新hex` | 二进制模式替换 | 修补特定字节 |
| `dtb input [action]` | 操作设备树 (Device Tree Blob) | 修改硬件配置 |
| `split input` | 分离 kernel 和 kernel_dtb | 分析内核结构 |
| `sha1 file` | 计算 SHA1 校验和 | 完整性验证 |
| `compress/decompress` | 压缩/解压（支持 gzip, lz4, xz 等） | 处理压缩镜像 |
| `cleanup` | 清理临时文件 | 操作后清理 |
| `decompress infile [outfile]` | 自动检测格式并解压 | 通用解压 |
| `compress[=format] infile [outfile]` | 指定格式压缩 | 通用压缩 |

**典型用法：**

```bash
# 解包启动镜像
magiskboot unpack boot.img
# 生成: kernel, ramdisk.cpio, second, dtb, kernel_dtb, extra

# 修补 ramdisk 中的某个文件
magiskboot cpio ramdisk.cpio "add 0755 /init.rc new_init.rc"

# 十六进制修补
magiskboot hexpatch boot.img "DEADBEEF" "CAFEBABE"

# 重新打包
magiskboot repack boot.img new-boot.img
```

### 2.3 libntfs-3g.so — NTFS 文件系统驱动

ntfs-3g 是 Linux 下**唯一稳定可靠的 NTFS 读写驱动**，这里嵌入为原生库。

**从字符串中提取的挂载命令：**

```bash
# 挂载 Windows 系统分区 (C盘)
ntfs-3g -o rw /dev/block/sda33 /mnt/mindowswin

# 挂载 Windows 数据分区
ntfs-3g -o rw /dev/block/sdaXX /mnt/mindowsdat
```

**能力：**
- 完整的 NTFS 读写支持
- 创建/删除/修改 Windows 文件
- 支持 NTFS 压缩、加密属性
- 可以修复 Windows 系统文件、替换驱动等

### 2.4 在 Termux 中直接调用原生库

**三个 `.so` 文件不是动态链接库，而是静态链接的 ARM64 可执行文件。**

Android APK 规范要求 native 代码必须使用 `.so` 扩展名放在 `lib/<架构>/` 目录下，但这三个文件实际上是**自包含可执行程序**——无动态链接器 (`INTERP`)、无动态段 (`DYNAMIC`)、无外部依赖：

```bash
file libblktool.so
# → ELF executable, 64-bit LSB arm64, static, stripped

readelf -h libblktool.so | grep Type
# → Type: EXEC (Executable file)

readelf -h libblktool.so | grep Entry
# → Entry point address: 0x400554
```

**在 Termux (root) 中使用的步骤：**

```bash
# 1. 复制到可执行目录
cp /sdcard/Mindows助手/docs/libblktool.so   ~/bin/blktool
cp /sdcard/Mindows助手/docs/libmagiskboot.so ~/bin/magiskboot
cp /sdcard/Mindows助手/docs/libntfs-3g.so    ~/bin/ntfs-3g

# 2. 赋予执行权限
chmod +x ~/bin/blktool ~/bin/magiskboot ~/bin/ntfs-3g
```

#### 2.4.1 blktool — 分区查询实战

```bash
# 查看帮助
blktool -h

# 查 boot_a 设备路径、大小
blktool -N boot_a --print-device --print-size -n
# 输出: /dev/block/sde11 100663296

# 查 misc 分区
blktool -N misc --print-device -n
# 输出: /dev/block/sda7

# 查 Windows 分区文件系统类型
blktool -N mindowsesp -N mindowswin --print-name --print-device --print-format -n
# 输出:
#   mindowsesp /dev/block/sda32 fat32
#   mindowswin /dev/block/sda33 ntfs

# 一次性查所有关键分区
blktool -N boot_a -N boot_b -N xbl_a -N xbl_b -N misc -N mindowsesp -N mindowswin \
    -N uefivarstore --print-name --print-device --print-size --print-format -n
# 输出:
#   boot_a        /dev/block/sde11 100663296
#   boot_b        /dev/block/sde34 100663296
#   xbl_a         /dev/block/sdb1  3670016
#   xbl_b         /dev/block/sdc1  3670016
#   misc          /dev/block/sda7  1048576
#   mindowsesp    /dev/block/sda32 314616896 fat32
#   mindowswin    /dev/block/sda33 74847346688 ntfs
#   uefivarstore  /dev/block/sde62 524288

# JSON 格式（便于脚本解析）
blktool -N boot_a -j
# 输出: {"name":"boot_a","device":"/dev/block/sde11","part":"11","disk":"8","size":"100663296",...}
```

#### 2.4.2 magiskboot — 启动镜像操作实战

```bash
# 查看帮助
magiskboot 2>&1

# 解包当前 boot_a 镜像
mkdir -p /tmp/boot_dump && cd /tmp/boot_dump
dd if=/dev/block/by-name/boot_a of=boot_a.img bs=32M
magiskboot unpack boot_a.img
ls -la
# 生成: kernel, ramdisk.cpio, second, dtb, header

# 十六进制修补（例：替换 kernel cmdline 中的一个参数）
magiskboot hexpatch boot_a.img "deadbeef" "cafebabe"

# 查看 ramdisk 内容
magiskboot cpio ramdisk.cpio "extract init.rc /tmp/init.rc"
cat /tmp/init.rc

# 重新打包
magiskboot repack boot_a.img boot_a_new.img
```

#### 2.4.3 ntfs-3g — 挂载 Windows 分区实战

```bash
# 先找到 Windows 分区路径
WINESP=$(blktool -N mindowsesp --print-device -n)
WINWIN=$(blktool -N mindowswin --print-device -n)

# 挂载 Windows C 盘（读写模式）
mkdir -p /mnt/windows
ntfs-3g -o rw $WINWIN /mnt/windows

# 浏览 Windows 文件
ls /mnt/windows/Windows/System32/

# 卸载
umount /mnt/windows
```

#### 2.4.4 组合使用：一键查看双系统状态

将三个工具组合，写一个脚本全面检查设备状态：

```bash
#!/bin/bash
echo "=== 当前启动槽位 ==="
getprop ro.boot.slot_suffix

echo ""
echo "=== 关键分区信息 ==="
blktool -N boot_a -N boot_b -N xbl_b -N misc -N mindowsesp -N mindowswin \
    --print-name --print-device --print-size --print-format -n

echo ""
echo "=== Windows 分区状态 ==="
WIN=$(blktool -N mindowswin --print-device -n)
ESP=$(blktool -N mindowsesp --print-device -n)
echo "Windows 系统分区: $WIN"
echo "Windows EFI 分区:  $ESP"
ntfs-3g -o ro $WIN /mnt/wincheck 2>/dev/null && \
    echo "Windows 系统分区可读" && umount /mnt/wincheck || \
    echo "Windows 系统分区不可访问"

echo ""
echo "=== boot_b 镜像校验 ==="
# 用 dd 导出并与备份比对
dd if=/dev/block/by-name/boot_b bs=32M 2>/dev/null | head -c 8 | xxd
# 输出 ANDROID! = 当前是 Android 镜像
```

> **注意：** 所有读写块设备的操作（blktool 读分区表、dd 读写分区、ntfs-3g 挂载）都需要 **root 权限**。在 Termux suroot 环境下已有 root 权限，可直接使用。

---

## 三、切换完整流程

### 3.1 关键字符串证据（从 dex 和 so 中提取）

```
of=/sdcard/Mindows                              ← dd 输出目标
/sdcard/Mindows                                 ← 工作目录
mindowswinAddr                                  ← Windows 系统分区路径变量
mindowsdatAddr                                  ← Windows 数据分区路径变量
getSlotId                                       ← 获取当前槽位
Landroid/os/PowerManager$WakeLock               ← 保持屏幕唤醒
shutdown$kotlinx_coroutines_core                ← Kotlin 协程 + 关机
Progress:                                       ← 进度条更新
```

### 3.2 Android → Windows 完整流程

```
用户在 HomeFragment 点击"切换到 Windows"
  │
  ├── 1. HomeFragment$MyHandler 启动后台 Kotlin 协程
  │      保持屏幕唤醒 (PowerManager.WakeLock)
  │      显示进度条 (Progress:)
  │
  ├── 2. libblktool.so 查找目标分区:
  │      blktool -N boot_b --print-device -n -j
  │        → {"device":"/dev/block/sde34","disk":"8","part":"11"}
  │      blktool -N xbl_b  --print-device -n -j
  │        → {"device":"/dev/block/sdc1","disk":"8","part":"33"}
  │
  ├── 3. Shell 执行 dd 写入镜像:
  │      dd if=/sdcard/Mindows助手/Mindows备份/mh2lm_boot_b.img \
  │         of=/dev/block/sde34 bs=32M
  │      dd if=/sdcard/Mindows助手/Mindows备份/mh2lm_xbl_b.img \
  │         of=/dev/block/sdc1 bs=4M
  │
  ├── 4. 切换启动槽位为 B (通过 getSlotId 相关逻辑):
  │      # 可能通过写入 misc 分区实现
  │      # 或直接操作 UEFI 变量存储
  │
  ├── 5. (可选) libntfs-3g.so 挂载 Windows 分区:
  │      ntfs-3g -o rw "$mindowswinAddr" /mnt/windows
  │      # 后续可对 Windows 文件操作
  │
  └── 6. 触发重启:
         通过 PowerManager.reboot() 或
         Runtime.exec("svc power reboot") 或
         Runtime.exec("reboot")
         ↓
       手机重启 → XBL_b → ABL_b(UEFI) → boot_b → simple-init → Windows
```

### 3.3 Windows → Android 流程

```
用户在 Windows 下运行 Mindows一键切换.bat
  │
  ├── 1. gap.exe 提权获取管理员权限
  ├── 2. blktool_arm64.exe 查找分区
  ├── 3. dd_cygwin/dd.exe 将 boot.img 写入所有 boot 分区
  ├── 4. (可选) 擦除 misc 分区
  └── 5. shutdown /r /t 0 重启
        ↓
      手机重启 → XBL → ABL(UEFI) → boot_a → Android kernel → Android
```

也可以直接在 Android 下完成同样操作：

```bash
# 找到 boot 分区设备路径
BOOT_A=$(blktool -N boot_a --print-device -n 2>/dev/null)
BOOT_B=$(blktool -N boot_b --print-device -n 2>/dev/null)

# 写入 Android 启动镜像
dd if=/sdcard/Mindows助手/.../boot.img of=$BOOT_A bs=32M
dd if=/sdcard/Mindows助手/.../boot.img of=$BOOT_B bs=32M

# 擦除 misc
dd if=/dev/zero of=/dev/block/by-name/misc bs=32K count=32

# 重启
reboot
```

---

## 四、判断当前 A/B 槽位

### 方法 1：内核启动参数（最权威）

直接从 bootloader 传给内核的参数中读取：

```bash
cat /proc/cmdline | tr ' ' '\n' | grep slot
```

```
androidboot.slot_suffix=_a
androidboot.slot=0
```

### 方法 2：Android 系统属性（最常用）

```bash
getprop ro.boot.slot_suffix
```

```
_a
```

```bash
getprop ro.boot.slot
```

```
0
```

> `_a` = A 槽，`_b` = B 槽；`0` = A 槽，`1` = B 槽。

### 方法 3：列出所有 slot 相关属性

```bash
getprop | grep slot
```

```
[ro.boot.slot_suffix]: [_a]
[ro.boot.slot]:        [0]
[ro.bootimage.build.fingerprint]: [LGE/mh2lm_lao_com/mh2lm:12/SKQ1.../release-keys:a]
```

### 方法 4：使用 blktool 判断

```bash
# 查看哪个 boot 分区为当前使用的
blktool -N boot_a -N boot_b --print-name --print-mount --print-is-bootable
```

---

## 五、手动切换 A/B 槽位

### 方法一：fastboot（推荐，最标准）

需要将手机重启到 Bootloader 模式，并用 USB 线连接电脑。

```
1. 关机
2. 同时按住 音量减 + 电源键 进入 Bootloader
3. 电脑端执行:
```

```bash
# 查看当前槽位
fastboot getvar current-slot

# 切换到 B 槽
fastboot --set-active=b

# 切换到 A 槽
fastboot --set-active=a

# 重启
fastboot reboot
```

> 注：部分 LG 机型的 fastboot 功能受限，请先验证是否支持 set_active 命令。

### 方法二：直接修改 misc 分区（底层，慎用）

Android A/B 系统的槽位信息存储在 **misc 分区开头** 的 `bootloader_control` 结构体中，共 32 字节：

```
偏移  大小   含义
0x00   4     Magic: "Boot" (0x42 0x6f 0x6f 0x74)
0x04   4     Magic: "Boot" (0x42 0x6f 0x6f 0x74)
0x08   4     Magic: "Boot" (0x42 0x6f 0x6f 0x74)
0x0C   4     Magic: "Boot" (0x42 0x6f 0x6f 0x74)
0x10   4     槽位编号: 0=A, 1=B
0x14   4     重试次数
0x18   4     是否成功启动标志
0x1C   4     是否可恢复标志
```

**切换到 B 槽（谨慎操作！）：**

```bash
# 切换到 B 槽 (将偏移 0x10 设为 0x01)
printf '\x42\x6f\x6f\x74\x42\x6f\x6f\x74\x42\x6f\x6f\x74\x42\x6f\x6f\x74\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
  | dd of=/dev/block/by-name/misc bs=1 count=32
```

**验证写入：**

```bash
xxd /dev/block/by-name/misc | head -2
```

```
00000000: 426f 6f74 426f 6f74 426f 6f74 426f 6f74  BootBootBootBoot
00000010: 0100 0000 0000 0000 0000 0000 0000 0000  ................
        ^^^^── 0x01 表示 B 槽
```

> **⚠ 警告：你当前设备使用的是 UEFI 固件（而非原厂 ABL），UEFI 可能不读取 misc 分区来决定槽位，而是使用 uefivarstore 分区。此方法不一定有效，建议先用 APP 切换。**

### 方法三：通过 Mindows 工具箱 APP（最安全）

这是**官方推荐**的方式，APP 内部自动处理所有复杂逻辑：

1. 打开"**Mindows 工具箱**"APP
2. 在主页 (HomeFragment) 查看当前系统状态
3. 点击"**切换到 Windows**"或"**切换到 Android**"
4. 确认 → 等待进度条完成 → 手机自动重启

APP 的 HomeFragment$MyHandler 会：
- 用 `getSlotId()` 判断当前槽位
- 用 libblktool 找到正确的分区路径
- 用 dd 写入对应镜像
- 设置槽位后调用 `shutdown` 重启

---

## 六、补充：你当前环境的状态

```
当前系统: Android
当前槽位: _a (A 槽)
boot_a:   Android 启动镜像 (ANDROID! 头)
boot_b:   Android 启动镜像 (ANDROID! 头)
misc:     全零 (没有 BootControl 数据)
UEFI:     正常运行 (abl_a/b 都是 ELF 格式)
```

这意味着：如果单纯切换槽位到 B（不先刷入 Windows 的 mh2lm_boot_b.img），你只会从另一个槽位启动**完全相同的 Android 系统**，不会进入 Windows。

要进入 Windows，必须先：
1. 把 `mh2lm_boot_b.img` 写入 boot_b
2. 把 `mh2lm_xbl_b.img` 写入 xbl_b  
3. 然后才能切换槽位到 B 并重启
