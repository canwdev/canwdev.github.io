> sudo vim /etc/fstab

## fstab 文件内容及释义

参考：

- [fstab - ArchWiki](https://wiki.archlinux.org/index.php/Fstab_(%E7%AE%80%E4%BD%93%E4%B8%AD%E6%96%87))
- [ubuntu 重新挂载home](https://www.cnblogs.com/huapox/p/3509637.html)

fstab文件可用于定义磁盘分区，各种其他块设备或远程文件系统应如何装入文件系统。

一个 `/etc/fstab` 示例，使用内核名称标识磁盘:

```
# /etc/fstab: static file system information.
#
# Use 'blkid' to print the universally unique identifier for a device; this may
# be used with UUID= as a more robust way to name devices that works even if
# disks are added and removed. See fstab(5).
#
# <file system>        <dir>         <type>    <options>             <dump> <pass>
tmpfs                  /tmp          tmpfs     nodev,nosuid          0      0
/dev/sda1              /             ext4      defaults,noatime      0      1
/dev/sda2              none          swap      defaults              0      0
/dev/sda3              /home         ext4      defaults,noatime      0      2
```

字段解释：

- `<file systems>`：要挂载的分区或存储设备。最初，该字段只包含待挂载分区的设备名（如/dev/sda1）。现在，除设备名外，还可以包含LABEL或UUID。
- `<dir>`：`<file systems>` 的文件系统挂载点。
- `<type>`：文件系统类型，支持许多种不同的文件系统：如`ext4`, `vfat`, `ntfs`, `swap`, `auto`等。 设置成`auto`类型，mount 命令会猜测使用的文件系统类型，对 CDROM 和 DVD 等移动设备是非常有用的。
- `<options>`：挂载时使用的参数，注意有些参数是特定文件系统才有的。
- `<dump>`：dump 工具通过它决定何时作备份。dump 会检查其内容，并用数字来决定是否对这个文件系统进行备份。 允许的数字是 0 和 1 。0 表示忽略， 1 则进行备份。大部分的用户是没有安装 dump 的 ，对他们而言 `<dump>` 应设为 0。
- `<pass>`：fsck 读取 `<pass>` 的数值来决定需要检查的文件系统的检查顺序。允许的数字是0, 1, 和2。 0表示不必检查该文件系统，数字1示意该文件系统需要先行检查（用于根文件系统）。数字2则表示完成根文件系统检查后，再检查该文件系统。

## 更改 /home 挂载点

1. 复制原有 home 内容到新分区

   ```sh
   sudo cp -ax /home/* /mnt/test/
   ```

2. 找到目标分区 UUID：`sudo blkid`

3. 重命名旧 `/home`目录，并且创建一个新的空目录（必要）

   ```sh
   sudo mv /home /home.old
   sudo mkdir /home
   ```

4. 将挂载点保，`sudo vim /etc/fstab`，按照如下格式修改：

   ```
   UUID=45a8f854-55c1-435b-b37e-8cfce8f8a6b2 /              ext4    defaults,noatime 0 1
   UUID=ba6bab0d-ecc4-48f8-b0f8-fc999bd67491 /home          ext4    defaults 0 2
   ```

   第一个 UUID 是系统根目录的分区，第二个则是新 home 的分区。

5. 重启，如果成功进入系统就可以删除旧的 `home.old`

参考：[ubuntu18.04 更改/home挂载点](https://blog.csdn.net/u012796629/article/details/100841549)
