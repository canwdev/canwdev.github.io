> 已验证所有命令，放心使用。

新建 vhdx

```shell
New-Item -ItemType Directory -Path "D:\Projects\wsl" -Force

# New-VHD -Path "D:\Projects\wsl\dev_drive.vhdx" -SizeBytes 128GB -Dynamic
# 当 New-VHD 不可用时，改用 diskpart 交互式命令
diskpart

DISKPART> create vdisk file="D:\Projects\wsl\dev_drive.vhdx" maximum=131072 type=expandable

DISKPART> exit

```

挂载虚拟磁盘到 wsl

```shell
wsl --mount --vhd "D:\Projects\wsl\dev_drive.vhdx" --name dev-drive --bare
```

初次使用，在 wsl 中格式化并挂载

```shell
# 查看分区（每次重启分区名可能会变，这里是 sdd）
lsblk

# NAME MAJ:MIN RM   SIZE RO TYPE MOUNTPOINTS
# sda    8:0    0 356.9M  1 disk
# sdb    8:16   0 159.4M  1 disk
# sdc    8:32   0     4G  0 disk [SWAP]
# sdd    8:48   0   128G  0 disk


# 注意！确保是正确的分区名，格式化为 ext4
sudo mkfs.ext4 /dev/sdd

sudo mkdir -p /mnt/dev-drive
sudo mount /dev/sdd /mnt/dev-drive/
sudo chown -R $USER:$USER /mnt/dev-drive/

# 验证
echo ok > /mnt/dev-drive/test.txt
ls -la /mnt/dev-drive
```

wsl 开机自动挂载

```shell
# 查看UUID
sudo blkid /dev/sdd
# /dev/sde: UUID="bda008e8-d550-4647-9fc5-6c9742883c7b" BLOCK_SIZE="4096" TYPE="ext4"

# 修改 `/etc/fstab` 文件
sudo vim /etc/fstab

# 在文件最下方追加一行（替换你实际获取到的 UUID）：
UUID=bda008e8-d550-4647-9fc5-6c9742883c7b  /mnt/dev-drive  ext4  defaults,nofail  0  2

# 回到 Windows 下验证：
wsl --shutdown
# 每次关机后必须手动挂载
wsl --mount --vhd "D:\Projects\wsl\dev_drive.vhdx" --name dev-drive --bare

# 回到 wsl 验证
ls /mnt/dev-drive/
```

Windows 自动挂载脚本

`mount.ps1`

```powershell
$vhdxPath = "D:\Projects\wsl\dev_drive.vhdx"

if (Test-Path $vhdxPath) {
    $res = wsl --mount --vhd $vhdxPath --name dev-drive --bare 2>&1
    Write-Host "Mount result: $res"
} else {
    Write-Host "Error: file not found $vhdxPath"
}

```

执行方法：`powershell mount.ps1`

开机自动执行挂载（计划任务）以管理员权限执行：

```powershell
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -WindowStyle Hidden -File `"D:\Projects\wsl\mount.ps1`""
$trigger = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME" -Delay (New-TimeSpan -Seconds 6)
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Highest
Register-ScheduledTask -TaskName "WSL Mount dev-drive" -Action $action -Trigger $trigger -Principal $principal -Description "Auto mount WSL dev-drive when startup"

# 验证任务已创建
Get-ScheduledTask -TaskName "WSL Mount dev-drive"

# 手动触发
Start-ScheduledTask -TaskName "WSL Mount dev-drive"

# 打开计划任务程序验证
taskschd.msc

# 如需删除
# Unregister-ScheduledTask -TaskName "WSL Mount dev-drive" -Confirm:$false

```

可能还需要：[[WSL 2 开机自启以及常驻后台]]

卸载分区（非必要）

```shell
# 卸载分区（在 wsl 中）
sudo umount /mnt/dev-drive/
# 手动删除 `/etc/fstab` 配置

# 卸载分区（在 Windows 中）
wsl --unmount "D:\Projects\wsl\dev_drive.vhdx"
```
