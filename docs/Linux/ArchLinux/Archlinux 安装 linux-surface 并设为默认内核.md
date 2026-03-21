在 Surface 设备上安装 Arch Linux 后，使用专用的 `linux-surface` 内核可以显著提升触控、手写笔、电源管理及各类传感器的支持。

以下是安装该内核并将其设为默认启动项的步骤：

## 1. 添加 linux-surface 仓库

为了方便后续更新，建议直接使用官方维护的二进制仓库，而不是从 AUR 手动编译（那会耗费极长时间）。

### 导入密钥

首先，需要信任该仓库的开发者密钥：

Bash

```
curl -s https://raw.githubusercontent.com/linux-surface/linux-surface/master/pkg/keys/surface.asc \
    | sudo pacman-key --add -
sudo pacman-key --lsign-key 56C372A9DA4211C51DB8466A895F09CD43CB3A40
```

### 修改 pacman 配置

编辑 `/etc/pacman.conf` 文件：

Bash

```
sudo nano /etc/pacman.conf
```

在文件末尾添加以下内容：

Ini, TOML

```
[linux-surface]
Server = https://pkg.surfacelinux.com/arch/
```

---

## 2. 安装内核及相关组件

同步仓库并安装内核及其配套固件：

Bash

```
sudo pacman -Syu
sudo pacman -S linux-surface linux-surface-headers surface-ipts-firmware
```

- **linux-surface**: 核心内核。
    
- **surface-ipts-firmware**: 用于触控支持（适用于 Surface Pro 4 及更新机型）。
    
- **iptsd**: 如果你需要触控多点手势，建议也安装此守护进程：`sudo pacman -S iptsd` 并启用服务 `sudo systemctl enable iptsd`。
    

---

## 3. 设置为默认内核

安装完成后，系统内会有两个内核：原生 `linux` 和 `linux-surface`。你需要调整引导程序（通常是 **GRUB**）来默认启动后者。

### 方案 A：自动记忆最后一次选择（推荐）

编辑 `/etc/default/grub`：

Bash

```
sudo nano /etc/default/grub
```

修改或确认以下两行：

Plaintext

```
GRUB_DEFAULT=saved
GRUB_SAVEDEFAULT=true
```

这样，只要你手动选一次 Surface 内核，下次它就会自动进入。

### 方案 B：强制指定顺序

如果你想直接固定它，可以查看 `/boot/grub/grub.cfg` 中的菜单顺序，或者简单地在 `/etc/default/grub` 中设置：

Plaintext

```
GRUB_DEFAULT="Advanced options for Arch Linux>Arch Linux, with Linux linux-surface"
```

_(注意：具体名称可能因语言设置有所不同)_

### 更新 GRUB 配置

**这一步至关重要，否则修改不会生效：**

Bash

```
sudo grub-mkconfig -o /boot/grub/grub.cfg
```

---

## 4. 安装安全启动（Secure Boot）密钥 (可选)

如果你的 Surface 开启了 Secure Boot，内核可能无法加载。

1. 安装 `surface-control`：`sudo pacman -S surface-control`。
    
2. 按照 [Linux-Surface Wiki](https://www.google.com/search?q=https://github.com/linux-surface/linux-surface/wiki/Secure-Boot) 的说明导入 MOK 证书。
    

> **建议：** 初学者可以先在 UEFI 设置中关闭 Secure Boot 以确保能正常进入系统，待内核跑通后再研究签名。

---

## 5. 重启并验证

重启设备，并在 GRUB 菜单中选择 `Arch Linux, with Linux linux-surface`。进入系统后运行：

Bash

```
uname -a
```

如果输出中包含 `-surface` 字样，恭喜你，安装成功了！

