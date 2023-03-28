# 使用 LUKS 加密 home 目录并在开机时自动解密

参考：

- [用luks方式对磁盘进行加密以及加密磁盘的自动挂载](https://www.cnblogs.com/guarderming/p/11957780.html)
- [[使用cryptsetup创建加密磁盘]]
- [[how-to-encrypt-your-home-directory-in-arch-linux]]

## 创建 LUKS 加密分区

首先你需要创建一个 luks 加密分区，具体操作参阅上述链接。

## 手动挂载并测试

使用 `CTRL + ALT + F2` 打开一个新的 tty2，并使用 root 登录

```
# 查看目标 luks 分区
lsblk

# 假设目标分区为 /dev/sda3，使用 cryptsetup 解密，名字为 home
cryptsetup open /dev/sda3 home
# 此时会要求输入密码，解密成功后会出现在 /dev/mapper/home

# 重命名旧的 home 目录
mv /home /home.old

# 挂载新的 home 目录（此时应该为空）
mkdir /home
mount /dev/mapper/home /home

# 复制原来的文件到新的 home 目录，并保留用户权限
cp -ax /home.old/* /home/
```

此时重新登录普通用户，如果登录成功并且 home 目录可以读写，则实验成功。

## 加密设备的开机自动挂载

创建密钥文件，这个文件在开机时会自动读取并解密目标分区：

```sh
# 生成随机字符串，熵越大越好
dd if=/dev/urandom bs=1 count=1024 2>/dev/null | base64 -w 0 | rev | cut -b 2- | rev
# 将随机内容写入到一个文件，比如这个
vim /root/luks_pass

# 设置文件权限，只允许 root 读写
chmod 600 /root/luks_pass
```

设置开机自动解密 luks 分区：`vim /etc/crypttab`

```
# <name>  <device>      <password> <options>
home    /dev/sda3       /root/luks_pass
```

把密码添加到luks加密中，这一步必须执行才能使密码生效：

```sh
cryptsetup luksAddKey /dev/sda3 /root/luks_pass
# 会提示 `Enter any passphrase`，此时请输入分区的加密密码
```

设置 /home 目录的自动挂载点：`vim /etc/fstab`

```
/dev/mapper/home        /home   ext4    defaults        0       2
```

重启即可完成。

---

如果要修改加密卷密码，或是删除密钥认证，请参考 [[保护数据，用 LUKS 给磁盘全盘加密]]