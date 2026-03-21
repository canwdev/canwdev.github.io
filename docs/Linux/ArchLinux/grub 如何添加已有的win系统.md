如果在安装 Arch Linux 后，GRUB 菜单里没有出现 Windows 的选项，通常是因为 **os-prober**（系统探测工具）没有启用或未安装。

以下是修复步骤：
## 1. 安装必要工具

你需要 `os-prober` 来自动识别硬盘上的其他操作系统，以及 `ntfs-3g` 来确保 Linux 能读取 Windows 的 NTFS 分区。

Bash

```
sudo pacman -S os-prober ntfs-3g
```

---

## 2. 启用 os-prober

出于安全考虑，新版本的 GRUB 默认禁用了自动探测。你需要手动开启它。

1. 编辑 GRUB 配置文件：
    
    Bash
    
    ```
    sudo nano /etc/default/grub
    ```
    
2. 在文件末尾添加（或取消注释）这一行：
    
    Plaintext
    
    ```
    GRUB_DISABLE_OS_PROBER=false
    ```
    
3. 保存并退出（Nano 中按 `Ctrl+O` 然后回车保存，`Ctrl+X` 退出）。
    

---

## 3. 挂载 Windows 分区 (关键步骤)

如果 Windows 分区没有被挂载，`os-prober` 有时会跳过它。

- 你可以先通过 `lsblk` 确认 Windows 所在的 EFI 分区或系统分区。
    
- 手动挂载一下（或者直接重启，通常启用上述设置后即可识别）。
    

---

## 4. 重新生成 GRUB 配置

这是最关键的一步，它会扫描所有驱动器并重新创建菜单。

Bash

```
sudo grub-mkconfig -o /boot/grub/grub.cfg
```

**检查输出：**

如果你在命令输出中看到类似 `Found Windows Boot Manager on /dev/nvme0n1p1@/EFI/Microsoft/Boot/bootmgfw.efi` 的字样，说明成功了！
