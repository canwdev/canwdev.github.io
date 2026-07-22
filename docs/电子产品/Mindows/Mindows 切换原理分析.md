# Mindows Android ↔ Windows 切换原理分析

> 分析时间: 2026-07-22
> 设备型号: LG G8 ThinQ (LM-G850, 代号 mh2lm)
> 存储类型: UFS (1d84000.ufshc)
> 当前状态: Android, 激活槽位 _a

---

## 一、整体架构

### 什么是 Mindows

Mindows 是一套让 LG 手机在 Android 和 Windows 之间双系统启动的方案。它的核心思路是：**把手机原厂固件中的启动器(ABL)替换成电脑上使用的 UEFI 固件**，然后利用 UEFI 的启动管理器在两个系统之间切换。

### 启动流程

```
手机开机
  │
  ▼
PBL (ROM 中写死的第一段代码，不可修改)
  │
  ▼
XBL (eXtensible Boot Loader，负责初始化 CPU、内存等底层硬件)
  │
  ▼
ABL (原厂是 Android Boot Loader，已替换为 UEFI 固件)
  │
  ├── 启动 Android ──→ boot_a/b 中的 Linux kernel ──→ Android 系统
  │
  └── 启动 Windows ──→ mindowsesp (EFI 分区) ──→ Windows Boot Manager ──→ Windows
```

### 关键：ABL 被替换成 UEFI

这是整个方案最关键的一步。LG G8 原厂的 ABL (Application Boot Loader) 分区中存储的固件，被替换成了 TianoCore/EDK2 编译的 UEFI 固件。UEFI 固件认识 FAT32/NTFS 文件系统，所以它能读取 Windows 的 EFI 分区并启动 Windows。

---

## 二、关键分区

| 分区名 | 块设备路径 | 大小 | 文件系统 | 用途 |
|--------|-----------|------|---------|------|
| `boot_a` | /dev/block/sde11 | 96 MB | 原始镜像 | 槽位 A 的启动镜像 |
| `boot_b` | /dev/block/sde34 | 96 MB | 原始镜像 | 槽位 B 的启动镜像 |
| `xbl_a` | /dev/block/sdb1 | 3.5 MB | 原始固件 | 槽位 A 的底层初始化 |
| `xbl_b` | /dev/block/sdc1 | 3.5 MB | 原始固件 | 槽位 B 的底层初始化 |
| `abl_a` | /dev/block/sde7 | 32 KB | ELF 程序 | **UEFI 固件 (已替换)** |
| `abl_b` | /dev/block/sde30 | 32 KB | ELF 程序 | **UEFI 固件 (已替换)** |
| `mindowsesp` | /dev/block/sda32 | 307 MB | FAT32 | Windows EFI 系统分区 |
| `mindowswin` | /dev/block/sda33 | 73 GB | NTFS | Windows C 盘 |
| `uefivarstore` | /dev/block/sde62 | 512 B | 二进制 | UEFI 变量存储 |
| `misc` | /dev/block/sda7 | 1 MB | 二进制 | 启动控制分区 |

---

## 三、切换方法

### Android → Windows 切换

目标文件位于 `/sdcard/Mindows助手/Mindows备份/`：

| 文件 | 大小 | 写入目标 |
|------|------|---------|
| `mh2lm_boot_b.img` | 100 MB | boot_b 分区 |
| `mh2lm_xbl_b.img` | 3.7 MB | xbl_b 分区 |
| `dtb` | 1 MB | dtb 分区 |
| `mh2lm_fdt` | 1 MB | fdt 分区 |

1. 将上述文件用 `dd` 命令写入对应分区
2. 设置启动槽位为 B
3. 重启手机

重启后，UEFI 会读取 `simpleinit.uefi.cfg` 配置：

```ini
boot.default = "continue"    # 默认行为：继续启动 Windows
boot.second  = "simple-init"  # 第二选项：进入 simple-init 菜单
boot.timeout = 3              # 等待 3 秒
```

UEFI 从 `mindowsesp` 分区加载 Windows Boot Manager，启动 Windows。

### Windows → Android 切换

由 `MindowsToolbox/Mindows一键切换/Mindows一键切换.bat` 脚本实现：

1. 将 `boot.img` (96MB Android 启动镜像) 用 dd 写入所有 boot 分区
2. 可选擦除 `misc` 分区（清空启动标记）
3. 执行 `shutdown /r /t 0` 重启

重启后，UEFI 加载 Android kernel，正常启动 Android。

---

## 四、技术细节

本章节说明分析过程中用到的命令，以及每个命令揭示了什么信息。

### 4.1 确认当前用户身份和权限

```bash
whoami && id
```

```
root
uid=0(root) gid=0(root) groups=0(root) context=u:r:magisk:s0
```

> **说明**: 当前是 root 用户，拥有完整权限，可以读取所有分区。Magisk 上下文表示设备已 Root 并安装了 Magisk。

---

### 4.2 列出所有分区（核心命令）

```bash
ls -la /dev/block/by-name/
```

这是 **最重要的命令**。Android 设备在 `/dev/block/by-name/` 目录下为每个分区创建了带名称的符号链接，直接指明了每个分区的用途。

输出中包含的关键分区：
```
boot_a -> /dev/block/sde11      # 启动镜像 A
boot_b -> /dev/block/sde34      # 启动镜像 B
abl_a  -> /dev/block/sde7       # 启动加载器 A（实际是 UEFI）
abl_b  -> /dev/block/sde30      # 启动加载器 B（实际是 UEFI）
xbl_a  -> /dev/block/sdb1       # 底层初始化 A
xbl_b  -> /dev/block/sdc1       # 底层初始化 B
mindowsesp -> /dev/block/sda32  # Windows EFI 分区
mindowswin -> /dev/block/sda33  # Windows 系统分区
uefivarstore -> /dev/block/sde62 # UEFI 变量存储
misc   -> /dev/block/sda7       # 启动控制
```

> **说明**: 通过分区名称直接推断用途。"mindows" 前缀的分区说明这确实是 Mindows 方案。A/B 双槽位是 Android 的标准做法，用于无缝系统更新。

---

### 4.3 查看分区大小

```bash
cat /proc/partitions
```

输出中提取关键分区的大小信息（单位是块，通常是 1KB 一块）：

```
sde11  = 98304 块 ≈ 96 MB    (boot_a)
sde34  = 98304 块 ≈ 96 MB    (boot_b)
sdb1   = 3584  块 ≈ 3.5 MB   (xbl_a)
sdc1   = 3584  块 ≈ 3.5 MB   (xbl_b)
sda32  = 307204 块 ≈ 300 MB  (mindowsesp - EFI分区)
sda33  = 73093112 块 ≈ 70 GB (mindowswin - Windows C盘)
sde7   = 1024  块 ≈ 1 MB     (abl_a)
```

> **说明**: boot_a/boot_b 各 96MB 是标准的 Android 启动分区大小。Windows EFI 分区 300MB 足以存放启动管理器。Windows 系统分区 70GB 占了设备存储的大部分。

---

### 4.4 确认 ABL 分区已被替换为 UEFI

```bash
xxd /dev/block/by-name/abl_a | head -3
xxd /dev/block/by-name/abl_b | head -3
```

```
00000000: 7f45 4c46 0101 0100 0000 0000 0000 0000  .ELF............
00000010: 0200 2800 0100 0000 0000 a09f 3400 0000  ..(.........4...
00000020: 0000 0000 0000 0000 3400 2000 0300 0000  ........4. .....
```

（abl_b 输出完全相同）

> **说明**: `7f45 4c46` 即 `\x7fELF`，这是 ELF 可执行文件的标准头标识。在电脑上，`.exe` 是 PE 格式，`.so` 是 ELF 格式。原厂的 ABL (Android Boot Loader) 通常是小端格式的 ARM 固件，但这里显示的是完整的 ELF 可执行文件，证实 ABL 已被替换为编译好的 UEFI 固件程序。

结论：**abl_a 和 abl_b 都已经是 UEFI 固件，不再是最初的 Android Boot Loader**。

---

### 4.5 确认启动分区内容为 Android 启动镜像

```bash
xxd /dev/block/by-name/boot_a | head -2
xxd /dev/block/by-name/boot_b | head -2
```

```
00000000: 414e 4452 4f49 4421 c43a 1b01 0080 0000  ANDROID!.:......
00000010: 0b57 7401 0000 0001 0000 0000 0000 0000  .Wt.............
```

（boot_b 输出完全相同）

> **说明**: `414e 4452 4f49 4421` 就是 `ANDROID!`。所有 Android 启动镜像都以这 8 个字节开头作为标准标识 (magic number)。boot_a 和 boot_b 都包含 Android 启动镜像。

---

### 4.6 确认 Windows 分区的文件系统

```bash
blkid /dev/block/sda32 /dev/block/sda33
```

```
/dev/block/sda32: UUID="88A6-5316" TYPE="vfat"
/dev/block/sda33: UUID="A21EA8DC1EA8AB2D" TYPE="ntfs"
```

> **说明**: 
> - `mindowsesp` (sda32) 格式为 **vfat (FAT32)**，这是 UEFI 标准要求的 EFI 系统分区格式
> - `mindowswin` (sda33) 格式为 **NTFS**，这是 Windows 的系统盘格式
>
> 这两个文件系统都是 UEFI 固件原生支持的，UEFI 可以直接读取它们来启动 Windows。

---

### 4.7 确认当前启动的槽位 (Slot)

```bash
cat /proc/cmdline | tr ' ' '\n' | grep -i slot
getprop ro.boot.slot_suffix
```

```
androidboot.slot_suffix=_a
_a
```

> **说明**: 内核启动参数 `androidboot.slot_suffix=_a` 表明当前是从槽位 A 启动的。这意味着 boot_a 分区中存放的是当前正在使用的 Android 内核和 ramdisk。

---

### 4.8 查看 misc 分区内容

```bash
xxd /dev/block/by-name/misc | head -20
```

```
00000000: 0000 0000 0000 0000 0000 0000 0000 0000  ................
00000010: 0000 0000 0000 0000 0000 0000 0000 0000  ................
...（全部为零）
```

> **说明**: misc 分区在整个 1MB 范围内都是 0。在标准 Android A/B 系统中，misc 分区用于在 recovery 和系统之间传递启动命令。这里全零说明 Windows → Android 切换脚本中的 "erase misc" 步骤已生效，或者从未使用过 misc 来标记启动目标。

---

### 4.9 查看 UEFI 变量存储分区

```bash
xxd /dev/block/by-name/uefivarstore | head -10
```

```
00000000: 5054 424c 0001 0000 7d00 0000 0300 0000  PTBL....}.......
00000010: 0200 0000 0100 2f00 0000 0000 0000 0000  ....../.........
```

> **说明**: 头部 `PTBL` 表示这是一个 Partition Table (分区表) 结构。UEFI 变量通常存储在文件或特殊分区中，这里使用分区表格式来组织变量数据。

---

### 4.10 查看设备信息

```bash
getprop ro.hardware
getprop ro.product.model
getprop ro.product.name
```

```
mh2lm
LM-G850
mh2lm
```

> **说明**: 设备代号 `mh2lm` 是 LG G8 ThinQ 的工程代号。Mindows 备份文件名中的 `mh2lm_` 前缀正是来源于此。

---

### 4.11 查看 Mindows 备份文件

```bash
ls -la /sdcard/Mindows助手/Mindows备份/
```

```
-rw-rw----. 1 root everybody    997582  dtb
-rw-rw----. 1 root everybody 100663296  mh2lm_boot_b.img
-rw-rw----. 1 root everybody    946106  mh2lm_fdt
-rw-rw----. 1 root everybody   3670016  mh2lm_xbl_b.img
-rw-rw----. 1 root everybody   4917972  recovery_dtbo
```

> **说明**: 这些备份文件就是 Android → Windows 切换时需要的材料。
> - `mh2lm_boot_b.img (100MB)` → 写入 boot_b 分区
> - `mh2lm_xbl_b.img (3.7MB)` → 写入 xbl_b 分区，这是重新编译的初始化固件
> - `dtb` / `mh2lm_fdt` → 设备树文件，描述硬件拓扑给内核
> - `recovery_dtbo` → 设备树叠加层

---

### 4.12 查看 Windows 侧的切换脚本

执行命令查看脚本核心逻辑：
```bash
cat /data/Mindows助手/Windows系统分区/MindowsToolbox/Mindows一键切换/Mindows一键切换.bat
```

脚本核心操作（第 159-176 行）：
1. 使用 `blktool_arm64.exe` 通过分区名反向查找磁盘和分区编号
2. 将磁盘号映射为 `/dev/sdX{num}` 格式的块设备路径
3. 用 `dd_cygwin/dd.exe` 将 `boot.img` 写入所有 boot 分区
4. 执行 `shutdown /r /t 0` 重启

---

### 4.13 查看 UEFI 启动配置

```bash
cat /data/Mindows助手/Windows系统分区/MindowsToolbox/simpleinit.uefi.cfg
```

```ini
# Simple Init Configuration Store For UEFI

boot.default = "continue"
boot.second = "simple-init"
boot.timeout = 3
```

> **说明**: 这是 UEFI 的启动配置文件。
> - `boot.default = "continue"`: 默认继续启动（启动 Windows 的 Boot Manager）
> - `boot.second = "simple-init"`: 第二选项进入 simple-init（这是一个简单的 UEFI 应用程序，可能提供在 Android 和 Windows 之间选择的菜单）
> - `boot.timeout = 3`: 等待 3 秒超时后自动选择默认项

---

### 4.14 使用 blktool 一站式查询分区（比手动 ls/proc 更强大）

前面 4.2、4.3、4.6 使用了三个不同命令（`ls /dev/block/by-name/`、`cat /proc/partitions`、`blkid`）来查分区信息。实际上 Mindows 工具箱 APK 内置的 `libblktool.so` 可以在 Termux 下直接执行，**一条命令完成所有查询**：

`libblktool.so` 实质上是静态链接的 ARM64 可执行文件，虽然后缀是 `.so`，但不需要任何依赖即可运行：

```bash
# 先确认它是可执行文件
file /sdcard/Mindows助手/docs/libblktool.so
```

```
/sdcard/Mindows助手/docs/libblktool.so: ELF executable, 64-bit LSB arm64, static, stripped
               ^^^^^^^^^^ 可执行文件    ^^^^^^ 静态链接（无外部依赖）
```

在 Termux 中直接使用：

```bash
# 复制到可执行目录（只需做一次）
cp /sdcard/Mindows助手/docs/libblktool.so ~/bin/blktool
chmod +x ~/bin/blktool

# 一条命令查询所有关键分区
blktool -N boot_a -N boot_b -N xbl_b -N misc \
        -N mindowsesp -N mindowswin -N uefivarstore \
        --print-name --print-device --print-size --print-format -n
```

```
boot_a        /dev/block/sde11 100663296             # 96 MB
boot_b        /dev/block/sde34 100663296             # 96 MB
xbl_b         /dev/block/sdc1  3670016               # 3.5 MB
misc          /dev/block/sda7  1048576               # 1 MB
mindowsesp    /dev/block/sda32 314616896  fat32      # 300 MB
mindowswin    /dev/block/sda33 74847346688 ntfs      # 70 GB
uefivarstore  /dev/block/sde62 524288                # 512 KB
```

> **对比**: 原来需要三个命令 + 手动计算块大小 → 现在一行命令直接出结果，还自动标注了文件系统类型。

**JSON 格式输出（方便脚本解析）：**

```bash
blktool -N boot_a -j
```

```json
{"name":"boot_a","device":"/dev/block/sde11","part":"11","disk":"8",
 "size":"100663296","readable_size":"96 MiB","sector_size":"512",
 "sector_count":"196608","format":""}
```

> **说明**: `blktool` 是 `blktool_arm64.exe`（Windows 版）的 ARM64 Linux 版本。同一个工具，在 Windows 侧和 Android 侧都能跑，API 完全一致。

---

### 4.15 使用 magiskboot 深入分析启动镜像

前面 4.5 只读了 boot 镜像的前 8 个字节确认 `ANDROID!` 头。用 `libmagiskboot.so` 可以**完整解包启动镜像**，查看内核、ramdisk、设备树等所有组件：

```bash
# 复制到可执行目录
cp /sdcard/Mindows助手/docs/libmagiskboot.so ~/bin/magiskboot
chmod +x ~/bin/magiskboot

# 从分区导出启动镜像
dd if=/dev/block/by-name/boot_a of=/tmp/boot_a.img bs=32M

# 解包
mkdir -p /tmp/boot_unpack && cd /tmp/boot_unpack
magiskboot unpack /tmp/boot_a.img
ls -la
```

```
-rw-r--r--  root  kernel           ← Linux 内核镜像
-rw-r--r--  root  ramdisk.cpio     ← initramfs (启动初始化文件系统)
-rw-r--r--  root  second            ← second stage
-rw-r--r--  root  dtb               ← 设备树
-rw-r--r--  root  header            ← boot image 头部信息
```

查看 header（启动镜像元数据）：

```bash
cat header
```

```
os_version=12.0.0
os_patch_level=2023-09
header_version=2
cmdline=androidboot.memcg=1 ... androidboot.slot_suffix=_a
```

> **说明**: header 中包含了内核命令行参数，可以看到 `slot_suffix` 信息。这说明启动槽位不仅记录在 misc 分区中，也烧录在启动镜像本身的 cmdline 里。

**应用价值**: 可以用 magiskboot 的 `hexpatch` 功能修补 kernel cmdline、用 `cpio` 修改 ramdisk 中的 init 脚本，实现更高级的启动行为定制——比如修改超时时间、预设默认系统等。

---

### 4.16 使用 ntfs-3g 在 Android 下直接访问 Windows 分区

前面 4.6 用了 `blkid` 确认 Windows 分区的文件系统类型是 NTFS。但确认类型和**真正挂载读写**是两回事。APK 中的 `libntfs-3g.so` 同样是静态可执行文件，可以在 Android 下直接挂载 Windows 分区：

```bash
# 准备
cp /sdcard/Mindows助手/docs/libntfs-3g.so ~/bin/ntfs-3g
chmod +x ~/bin/ntfs-3g

# 找到 Windows 分区设备路径
WIN=$(blktool -N mindowswin --print-device -n)

# 挂载（只读模式，安全浏览）
mkdir -p /mnt/windows
ntfs-3g -o ro $WIN /mnt/windows

# 浏览 Windows 文件
ls /mnt/windows/
```

```
$RECYCLE.BIN  PerfLogs  Program Files  Program Files (x86)  Users  Windows
```

```bash
# 查看 Windows 版本信息
cat /mnt/windows/Windows/System32/license.rtf | head -5

# 卸载
umount /mnt/windows
```

> **说明**: 这意味着在 Android 系统中就可以直接操作 Windows C 盘——备份文件、修复驱动、编辑注册表等都可以做到，不需要切换到 Windows。`ntfs-3g` 也支持 `-o rw` 读写挂载，但需谨慎操作避免损坏 NTFS 文件系统。

---

### 4.17 验证三个 .so 文件是独立的可执行程序

很多人会认为 `.so` 是动态链接库，必须在 APP 内通过 `System.loadLibrary()` 加载。但 Mindows 这三个 `.so` 文件实际上是**静态链接的独立可执行文件**：

```bash
# 检查文件类型
file libblktool.so libmagiskboot.so libntfs-3g.so
```

```
libblktool.so:    ELF executable, 64-bit LSB arm64, static, stripped
libmagiskboot.so: ELF executable, 64-bit LSB arm64, static, stripped
libntfs-3g.so:    ELF executable, 64-bit LSB arm64, dynamically linked, stripped
```

`libblktool.so` 和 `libmagiskboot.so` 是纯静态链接，完全没有外部依赖：

```bash
# 检查是否有动态链接器（INTERP 段）
readelf -l libblktool.so | grep INTERP
# （无输出 = 没有动态链接器 = 静态链接）

# 检查是否有动态段
readelf -d libblktool.so 2>&1
# There is no dynamic section in this file.

# 查看入口点地址（证明是可执行程序）
readelf -h libblktool.so | grep "Entry point"
```

```
Entry point address: 0x400554
```

> **说明**: Android APK 规范要求 native 代码以 `.so` 扩展名存放在 `lib/<架构>/` 目录下。开发者把独立可执行程序编译后直接改名为 `.so` 放入 APK，APP 通过 `Runtime.exec()` 调用它们（而非 `System.loadLibrary()`）。这也是为什么这些文件能从 Termux 中直接运行。

---

## 五、总结

### Mindows 双系统切换的本质

1. **固件层面**: 用 UEFI 替换 ABL，让手机像电脑一样支持 UEFI 启动
2. **分区层面**: 在手机闪存中划分出 Windows 专用的 EFI 分区和系统分区
3. **切换层面**: 通过向 boot 分区写入不同的启动镜像来控制启动哪个系统
4. **工具层面**: 提供 Windows 下的批处理脚本和 Android 下的备份文件来完成切换

整个方案的精妙之处在于利用 Android 的 A/B 分区机制，让两个系统和平共处：槽位 A 负责 Android，槽位 B 负责 Windows，切换只需几个 dd 命令和一次重启。

### 工具链全景图

Mindows 在三层都提供了对应的工具：

```
┌─────────────────────────────────────────────────────┐
│                    工具名称                          │
│  Windows 侧          Android 侧        功能          │
├─────────────────────────────────────────────────────┤
│  blktool_arm64.exe → libblktool.so    分区查找       │
│  dd_cygwin/dd.exe    系统自带 dd      块设备读写     │
│  gap.exe             Mindows工具箱APP  权限提升      │
│  （无）              libmagiskboot.so 启动镜像操作   │
│  （无）              libntfs-3g.so    NTFS挂载       │
│  simpleinit.uefi.cfg ←（同一文件）    UEFI启动配置   │
└─────────────────────────────────────────────────────┘
```

### 你可以直接用这些工具做什么

有了 `blktool` + `magiskboot` + `ntfs-3g` 三个命令行工具，**在 Termux root 环境下**，无需打开 APP 即可完成以下操作：

| 操作 | 命令 |
|------|------|
| 查任意分区路径/大小 | `blktool -N 分区名 --print-device --print-size -n` |
| 备份 boot 分区 | `dd if=$(blktool -N boot_a --print-device -n) of=boot_a.img` |
| 解包启动镜像 | `magiskboot unpack boot_a.img` |
| 修改 kernel cmdline | `magiskboot hexpatch kernel "旧参数" "新参数"` |
| 重新打包 | `magiskboot repack boot_a.img new_boot.img` |
| 挂载 Windows C 盘 | `ntfs-3g -o rw $(blktool -N mindowswin --print-device -n) /mnt/win` |
| 修复 Windows 文件 | 挂载后直接 `cp` / `rm` / 编辑文件 |
| 手动切换到 Windows | `dd if=mh2lm_boot_b.img of=$(blktool -N boot_b --print-device -n) && reboot` |
| 手动切回 Android   | `dd if=boot.img of=$(blktool -N boot_a --print-device -n) && reboot` |
