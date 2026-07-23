# WoA (Windows on ARM) 学习指南

> 从零开始学习在手机上运行 Windows on ARM
> 设备: LG G8 ThinQ (mh2lm) / LG G8X (mh2lm)
> 芯片: Snapdragon 855 (SM8150)

---

## 一、项目生态全貌

Mindows/WoA 由多个开源项目组成，各自负责不同层面：

```
┌──────────────────────────────────────────────────────┐
│                      用户界面                         │
│  WOA Helper (Android APP)  /  Mindows 工具箱          │
├──────────────────────────────────────────────────────┤
│                    一键切换脚本                        │
│  Windows: .bat 脚本 (dd + blktool + shutdown)         │
│  Android: WOA Helper APP (blktool + magiskboot + dd)  │
├──────────────────────────────────────────────────────┤
│                  UEFI 固件 (核心)                      │
│  edk2-msm: 编译成 UEFI 固件，刷入 ABL 分区              │
├──────────────────────────────────────────────────────┤
│                  UEFI 应用程序                         │
│  SimpleInit: 启动菜单 (选择 Android/Windows)          │
│  BootShim:   Android 启动镜像 ↔ UEFI 的桥梁           │
├──────────────────────────────────────────────────────┤
│                  Windows 驱动                         │
│  WOA-Drivers: 高通平台 Windows ARM64 驱动集           │
├──────────────────────────────────────────────────────┤
│                  ACPI 表 (硬件描述)                    │
│  手工从原厂 Device Tree (DTS) 翻译为 ACPI (ASL)       │
└──────────────────────────────────────────────────────┘
```

### 核心仓库一览

| 仓库                        | 用途                         | 地址                                                 |
| ------------------------- | -------------------------- | -------------------------------------------------- |
| **edk2-msm**              | UEFI 固件源码，支持 80+ 高通设备      | `https://github.com/edk2-porting/edk2-msm`         |
| **SimpleInit**            | UEFI 启动菜单 (图形界面)           | `https://github.com/BigfootACA/simple-init`        |
| **WOA-Drivers**           | Windows ARM64 高通驱动         | `https://github.com/edk2-porting/WOA-Drivers`      |
| **SurfaceDuo-Guides**     | Wine 安装指南 (SD855 同架构，学习参考) | `https://github.com/WOA-Project/SurfaceDuo-Guides` |
| **woa-mh2lm**             | LG G8X 一键安装指南 + 成品         | `https://github.com/n00b69/woa-mh2lm`              |
| **woa-alphaplus**         | LG G8 指南 + 成品              | `https://github.com/n00b69/woa-alphaplus`          |
| **woa-betalm**            | LG G8S 指南 + 成品             | `https://github.com/n00b69/woa-betalm`             |
| **woa-helper**            | Android 侧切换 APP            | `https://github.com/n00b69/woa-helper`             |
| **Renegade Project Wiki** | 中文文档(可能需要翻墙)               | `https://wiki.renegade-project.cn`                 |

---

## 二、LG G8/G8X 当前状态

来自 `woa-mh2lm` 项目的状态记录：

### 已正常工作
| 硬件               | 状态        |
| ---------------- | --------- |
| 显示屏              | 正常        |
| GPU (Adreno 640) | 正常 (可能花屏) |
| 触摸屏              | 正常        |
| UFS 存储           | 正常        |
| USB              | 正常        |
| WiFi             | 正常        |
| 蓝牙               | 正常        |
| 扬声器              | 正常        |
| 麦克风              | 正常        |
| SD 卡             | 正常（不稳定）   |
| 电池百分比            | 正常        |
| USB 充电           | 正常 (非常慢)  |
| 无线充电             | 正常        |
| 加速度计             | 正常        |
| GPS              | 正常        |
| 陀螺仪              | 正常        |

### 尚未工作
| 硬件        | 状态        |
| --------- | --------- |
| 3.5mm 耳机孔 | 不支持（实测支持） |
| 摄像头       | 不支持       |
| LTE/SMS   | 不支持       |
| 指纹传感器     | 不支持       |
| 光线传感器     | 不支持       |
| 振动马达      | 不支持       |
| LG 双屏配件   | 不支持       |
| 手电筒       | 不支持       |

> 当前整体状态: **Beta**，日常使用基本可用(除了通话和拍照)。

---

## 三、UEFI 固件详解

### 3.1 什么是 EDK2

```
EDK2 (EFI Development Kit II) = TianoCore 项目
├── 开源的 UEFI 固件实现
├── BSD-2-Clause 许可证 (商业友好)
├── 支持 x86_64, ARM64, RISC-V 等架构
└── 被用于: VMware, QEMU, 各种主板, Surface Duo, LG G8 等
```

edk2-msm 是 EDK2 在**高通 Snapdragon 平台**上的移植版本。

### 3.2 源码目录结构

```
edk2-msm/
├── Silicon/Qualcomm/sm8150/          ← SD855 SoC 级别代码
│   ├── AcpiTables/                    ★ ACPI 表 (硬件描述的核心)
│   │   ├── Dsdt.asl                   ★ 主 DSDT 表
│   │   ├── Madt.asl                   ★ 中断控制器描述
│   │   ├── Gtdt.asl                   ★ 定时器
│   │   └── ...
│   ├── Sm8150.dec                     ← SoC 配置定义
│   └── Sm8150.dsc                     ← SoC 编译配置
│
├── Platform/LGE/sm8150/mh2lm/        ← LG G8 设备特定代码
│   ├── AcpiTables/                    ★ 设备专属 ACPI 表
│   │   └── Dsdt.asl                   ★ 设备的硬件描述
│   ├── Mh2lm.dec                      ← 设备配置
│   └── Mh2lm.dsc                      ← 设备编译配置
│
├── GPLDrivers/                        ← GPL 许可的驱动
│   └── Library/SimpleInit/            ← 启动菜单
│
├── configs/
│   ├── sm8150.conf                    ← SoC 基础配置
│   │   FD_BASE=0xCE000000             ← UEFI 加载基址
│   │   FD_SIZE=0x00700000             ← UEFI 固件大小 = 7MB
│   └── devices/
│       ├── mh2lm.conf                 ← LG G8 设备配置
│       ├── mh2lm5g.conf               ← LG V50 5G
│       ├── flashlmdd.conf             ← LG V50
│       ├── betalm.conf                ← LG G8S
│       └── ... (80+ 设备)
│
├── build.sh                           ★ 一键编译脚本
├── tools/
│   ├── BootShim/                      ← Linux↔UEFI 桥接
│   └── Installer/                     ← 刷机包生成器
│
└── Common/
    ├── edk2/                           ← TianoCore EDK2 上游
    └── edk2-platforms/                ← EDK2 平台支撑
```

### 3.3 编译流程

```bash
# 1. 克隆仓库 (包含子模块)
git clone --recursive https://github.com/edk2-porting/edk2-msm
cd edk2-msm

# 2. 安装依赖 (Ubuntu/Debian)
apt install build-essential python3 python3-distutils \
            gcc-aarch64-linux-gnu clang llvm device-tree-compiler \
            uuid-dev nasm acpica-tools libglib2.0-dev

# 3. 编译 LG G8 的 UEFI 固件
./build.sh --device mh2lm

# 输出文件: boot-mh2lm.img (可刷入的 UEFI 启动镜像)

# 其他编译选项:
./build.sh --device mh2lm --acpi         # 重新编译 ACPI 表
./build.sh --device mh2lm -z             # 生成刷机包 zip
./build.sh --device mh2lm -b             # fastboot 临时启动测试
./build.sh --device mh2lm -r DEBUG       # DEBUG 版本 (含调试信息)
./build.sh --device mh2lm -u             # 启用串口调试输出
./build.sh --device mh2lm --clean        # 清理编译产物
```

### 3.4 BootShim 原理

BootShim 是 Android 启动镜像与 UEFI 之间的**转接层**：

```
Android 启动镜像 (boot.img)
  ├── Linux Kernel (被替换为 BootShim)
  │     └── 启动时不做 Linux 初始化，而是加载 UEFI 固件
  ├── UEFI 固件 (FD 文件，追加在镜像末尾)
  └── 启动后: BootShim → UEFI → SimpleInit → 选择系统
```

---

## 四、ACPI 硬件描述详解

### 4.1 Android vs Windows 的硬件发现

```
Android:
  内核启动参数 → Linux Kernel → Device Tree (DTS/DTB)
  ├── 树状结构: soc { ufs { ... }; usb { ... }; }
  └── 原厂提供，从 DTS 编译为 DTB

Windows:
  UEFI → ACPI 表 → Windows ACPI 驱动
  ├── 表格结构: DSDT / SSDT / MADT / GTDT / DSD
  └── 需要手工编写 ACPI 代码 (ASL 语言)，编译为 AML 字节码
```

### 4.2 ACPI 表类型

| 表名 | 全称 | 描述内容 |
|------|------|---------|
| **DSDT** | Differentiated System Description Table | 主硬件描述表，几乎所有设备都在这里 |
| **SSDT** | Secondary System Description Table | 辅助描述表，补充 DSDT |
| **MADT** | Multiple APIC Description Table | 中断控制器 (GIC) 描述 |
| **GTDT** | Generic Timer Description Table | 系统定时器描述 |
| **DSD** | Device Specific Data | 设备专属属性 (类似 DTS 的 compatible 属性) |
| **FADT** | Fixed ACPI Description Table | 电源管理相关 |

### 4.3 ACPI 代码示例 (ASL)

```asl
// 描述 UFS 控制器
Device (UFS0) {
    Name (_HID, "QCOM0182")          // 硬件 ID (对应 Windows 驱动)
    Name (_UID, 0)                   // 实例编号
    Name (_CCA, 1)                   // DMA 一致性

    Method (_CRS, 0) {               // 硬件资源
        Name (RBUF, ResourceTemplate() {
            Memory32Fixed (ReadWrite, 0x01D84000, 0x1000)  // 寄存器基址
            Interrupt (ResourceConsumer, Level, ActiveHigh, Exclusive) {
                0x000001C8            // 中断号
            }
        })
        Return (RBUF)
    }
}

// 描述 GPIO
Device (GPIO) {
    Name (_HID, "QCOM01A1")
    // ...
}
```

### 4.4 关键：从 DTS 翻译到 ACPI

这是整个移植过程中**最耗时**的工作。需要对照原厂 Device Tree Source (从内核源码中提取) 和高通参考驱动，将每个硬件的信息翻译成 ACPI 格式：

```
DTS (原厂提供):                ACPI/ASL (需手工编写):
─────────────────────────      ─────────────────────
ufs@1d84000 {                  Device(UFS0) {
    compatible = "qcom,ufs";       Name(_HID, "QCOM0182")
    reg = <0x1d84000 0x1000>;      Memory32Fixed(0x01D84000, 0x1000)
    interrupts = <GIC_SPI 456>;    Interrupt(ResourceConsumer, ..., 0x1C8)
    clocks = <&gcc GCC_UFS_...>;   (在 ACPI 中由驱动自行管理时钟)
    resets = <&gcc GCC_UFS_...>;   (由 UEFI 初始化时处理)
    phys = <&ufsphy>;              (在 DSD 属性中描述)
};                              }
```

---

## 五、Windows 驱动

### 5.1 驱动来源分类

```
Windows on LG G8 的驱动来源:

1. 高通官方 Windows BSP
   ├── UFS 存储驱动
   ├── USB 控制器 (DWC3) 驱动
   ├── PCIe 控制器驱动
   └── 电源管理芯片 (PMIC) 驱动
   (高通为 Windows on ARM 笔记本提供过这些基础驱动)

2. 社区移植的驱动 (WOA-Drivers 仓库)
   ├── 显示驱动 (LG OLED 面板)
   ├── 触摸屏驱动
   ├── 音频驱动 (WCD9341)
   ├── 传感器驱动
   └── 电池驱动

3. 参考设备复用
   ├── Surface Pro X (SQ1/SQ2 = Snapdragon 8cx 变体)
   ├── Lenovo Flex 5G (Snapdragon 8cx)
   └── Samsung Galaxy Book S (Snapdragon 8cx)
   (这些也是高通 + ARM64，部分驱动可移植)
```

### 5.2 WOA-Drivers 仓库结构

```
WOA-Drivers/
├── Drivers/
│   ├── Audio/           ← 音频驱动
│   ├── Display/         ← 显示驱动
│   ├── Touch/           ← 触摸屏驱动
│   ├── Sensors/         ← 传感器驱动
│   └── ...
├── Installer/           ← 驱动安装脚本 (PowerShell)
└── Docs/                ← 文档
```

---

## 六、woa-mh2lm 安装指南 (LG G8X 参考)

来自 `https://github.com/n00b69/woa-mh2lm`，这是 LG G8X 的完整安装流程。

### 6.1 整体步骤

```
1. 解锁 Bootloader
2. 进入 EDL 模式 (Qualcomm 9008)
3. 备份关键分区 (Qfil 工具)
4. 刷入工程 ABL (elf 修改版 bootloader)
5. 进入 modded TWRP
6. 备份当前 boot 镜像
7. 用 parted 调整分区 → 创建 ESP + Windows 分区
8. 格式化为 FAT32 (ESP) + NTFS (Windows)
9. 刷入 UEFI + 安装 Windows
```

### 6.2 分区布局 (修改后)

```
原始 Android 分区:
┌────────────────────────────────────┐
│  ...  │ userdata (60GB+) │  grow  │
└────────────────────────────────────┘

WoA 分区 (修改后):
┌───────────────────────────────────────┐
│  ...   │ userdata │ ESP │ Windows  │
│        │  ~46GB   │300MB│ ~60GB    │
└───────────────────────────────────────┘
```

### 6.3 双启动 (Dualboot)

通过 **WOA Helper APP** 实现 Android ↔ Windows 一键切换：

```
Android 侧:
├── 安装 WOA Helper APK
├── 用 APP 备份当前 boot.img
├── 用 APP 生成 StA (Switch to Android) 文件
├── 点击 QUICKBOOT TO WINDOWS
└── 自动: dd 写入 UEFI → 设置槽位 → 重启 → Windows

Windows 侧:
├── 运行 C:\sta\sta.exe
├── 自动: 写入 Android boot.img → 设置槽位 → 重启 → Android
└── (也可固定到开始菜单/任务栏)
```

### 6.4 与 Mindows (你的设备) 的对应关系

| woa-mh2lm | Mindows (你的设备) |
|-----------|-------------------|
| 分区名 `esp` | 分区名 `mindowsesp` |
| 分区名 `win` | 分区名 `mindowswin` |
| ESP 卷标 `ESPMH2LM` | ESP 卷标同 FAT32 |
| Windows 卷标 `WINMH2LM` | Windows 卷标同 NTFS |
| WOA Helper APP | Mindows 工具箱 APP (`com.mindows.toolbox`) |
| 备份 boot.img | 备份 `mh2lm_boot_b.img` + `mh2lm_xbl_b.img` |
| sta.exe (Switch to Android) | `Mindows一键切换.bat` |

---

## 七、学习路线

### 第一阶段：基础理论 (自学，2-4 周)

| 主题 | 资源 |
|------|------|
| ARM64 启动链 (PBL→XBL→ABL→Kernel) | 阅读 SD855 技术参考手册 (公开章节) |
| UEFI 规范 (第 2-5 章) | `https://uefi.org/specs` |
| ACPI 规范 (DSDT/SSDT) | 同上 |
| Device Tree vs ACPI | Linux 内核 `Documentation/devicetree/` |
| 高通分区结构 (GPT) | 用你手上的 blktool 实际查看 |

### 第二阶段：搭建编译环境 (1-2 周)

```bash
# 1. 安装 Ubuntu 22.04 (虚拟机或 WSL2)
# 2. 安装交叉编译工具链
sudo apt install gcc-aarch64-linux-gnu clang llvm device-tree-compiler \
                 build-essential python3 python3-distutils uuid-dev nasm \
                 acpica-tools libglib2.0-dev img2simg

# 3. 克隆源码
git clone --recursive https://github.com/edk2-porting/edk2-msm
cd edk2-msm

# 4. 尝试编译
./build.sh --device mh2lm

# 预期输出: 编译完成的 boot-mh2lm.img
```

### 第三阶段：阅读源码 (4-8 周)

推荐阅读顺序：

1. **入口点**: `Platform/LGE/sm8150/mh2lm/Mh2lm.dsc` — 了解编译哪些模块
2. **ACPI 表**: `Silicon/Qualcomm/sm8150/AcpiTables/` — 理解硬件描述
3. **设备 DSDT**: `Platform/LGE/sm8150/mh2lm/AcpiTables/Dsdt.asl` — 看你的手机硬件怎么写的
4. **启动钩子**: `Platform/LGE/sm8150/mh2lm/*.sh.inc` — 了解编译后处理流程
5. **GPL 驱动**: `GPLDrivers/` — 看 Linux 驱动如何适配到 UEFI

### 第四阶段：动手实践 (持续)

推荐从小修改开始，逐步深入：

```
级别 1：修改启动配置
  └── 改 simpleinit.uefi.cfg 的启动超时时间、默认选项

级别 2：用 fastboot 安全测试
  └── 编译后不刷入，用 fastboot boot 临时启动测试
      如果失败，重启自动恢复原固件

级别 3：修改 UEFI Logo/界面
  └── 替换 SimpleInit 的启动画面

级别 4：添加/修改 ACPI 表
  └── 修改 Dsdt.asl → 重新编译 ACPI → fastboot boot 测试

级别 5：移植 Linux 驱动到 UEFI
  └── 如添加缺失的传感器支持

级别 6：编写 Windows 驱动
  └── 基于 Linux 驱动逆向 → 编写 KMDF 驱动 → 提交到 WOA-Drivers
```

### 第五阶段：参与社区

| 社区 | 地址 |
|------|------|
| **LG 设备 WoA Telegram** | `https://t.me/lgedevices` |
| **Duo WoA Telegram** | `https://t.me/duowoa` |
| **Renegade Project 中文** | `https://wiki.renegade-project.cn` |
| **Discord** | `https://discord.gg/XXBWfag` |
| **赞助 (Patreon)** | `https://patreon.com/renegade_proj` |

---

## 八、你手上可以直接做的

### 8.1 用现有工具探索

```bash
# 查看你手机上运行着的 UEFI 固件
xxd /dev/block/by-name/abl_a | head -5
# → 7f45 4c46 = ELF 可执行文件

# 查看 UEFI 固件大小 (7MB)
blktool -N uefivarstore --print-size -n

# 用 magiskboot 深入分析启动镜像
dd if=/dev/block/by-name/boot_a of=/tmp/boot_a.img bs=32M
magiskboot unpack /tmp/boot_a.img
cat header  # 查看内核 cmdline, OS 版本等

# 查看 Windows EFI 分区内容
ntfs-3g -o ro /dev/block/sda32 /mnt/esp
ls /mnt/esp/EFI/
```

### 8.2 理解你当前的 Mindows 环境

```
你当前 Mindows 环境的核心文件来源:

uefi.img (7MB)          → edk2-msm 编译产物 (boot-mh2lm.img)
simpleinit.uefi.cfg      → SimpleInit 配置文件
mh2lm_boot_b.img (100MB) → 编译的 Android 启动镜像 = BootShim + UEFI 固件
mh2lm_xbl_b.img (3.5MB)  → 修改过的 XBL (eXtensible Boot Loader)
dtb / mh2lm_fdt           → 设备树 (用于编译 ACPI 表时的参考)
recovery_dtbo             → 设备树叠加层
boot.img (96MB)           → 标准 Android 启动镜像 (切回 Android 用)
```

### 8.3 编译你自己的 UEFI

如果在电脑上成功编译 edk2-msm，输出 `boot-mh2lm.img` 理论上和 `uefi.img` 是同一份产物，你可以通过 adb push 到手机后用 fastboot 测试：

```bash
# 在电脑上:
./build.sh --device mh2lm
adb push boot-mh2lm.img /sdcard/
adb shell "dd if=/sdcard/boot-mh2lm.img of=/dev/block/by-name/abl_a bs=32M"
adb reboot
```

---

## 九、关键术语对照

| 术语 | 全称 | 解释 |
|------|------|------|
| **WoA** | Windows on ARM | ARM 处理器运行的 Windows |
| **EDK2** | EFI Development Kit II | TianoCore 开源 UEFI 实现 |
| **UEFI** | Unified Extensible Firmware Interface | 统一可扩展固件接口 (替代 BIOS) |
| **ACPI** | Advanced Configuration and Power Interface | 硬件描述表，Windows 发现硬件的依据 |
| **DSDT** | Differentiated System Description Table | ACPI 主表 |
| **ASL** | ACPI Source Language | 编写 ACPI 表的源代码语言 |
| **AML** | ACPI Machine Language | ASL 编译后的字节码 |
| **DTS** | Device Tree Source | Linux/Android 使用的硬件描述 |
| **ABL** | Application Boot Loader | 高通 Boot 链的第三阶段 (被 UEFI 替换) |
| **XBL** | eXtensible Boot Loader | 高通 Boot 链的第二阶段 |
| **BootShim** | Boot Shim | Linux/UEFI 启动桥接器 |
| **SimpleInit** | Simple Initialization | UEFI 启动菜单程序 |
| **StA** | Switch to Android | 从 Windows 切回 Android 的工具 |
| **WoA Helper** | Windows on ARM Helper | Android 侧的切换辅助 APP |
