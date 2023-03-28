# [使用cryptsetup创建加密磁盘](http://blog.lujun9972.win/blog/2018/04/12/%E4%BD%BF%E7%94%A8cryptsetup%E5%88%9B%E5%BB%BA%E5%8A%A0%E5%AF%86%E7%A3%81%E7%9B%98/index.html)

## 目录

cryptsetup是linux下的一个分区加密工具，它通过调用内核中的"dm-crypt"来实现磁盘加密的功能。

## dm-crypt的特点

dm-crypt具有如下几个特点:

1. 支持多种加密格式

   - LUKS（Linux Unified Key Setup）
   - Plain
   - loop-AES
   - TCRYPT

   一般我们比较常用的是LUKS格式

2. 安装简单

   dm-crypt是整合到linux内核中的，而它的命令行前端cryptsetup,在大多数主流的linux发行版中都会自带

3. 可以与LVM无缝结合

## 使用cryptsetup创建加密磁盘



### 创建虚拟磁盘分区

为了方便，我这里用 `dd` 命令创建一个文件来代替真实的磁盘分区(因为操作过程会清空整个磁盘分区的内容:()。

```
dd if=/dev/zero of=/tmp/USB.img bs=1M count=100

ls -l /tmp/USB.img
-rw-r--r-- 1 lujun9972 lujun9972 104857600 4月  12 18:13 /tmp/USB.img
```

这就创建了一个100M的文件作为虚拟磁盘分区来用。

在实际使用中，你可以用cryptsetup来对实际的磁盘分区来进行操作。

### 创建加密磁盘分区

虽然说dm-crypt支持多种加密格式，但最常用的还是LUKS。

创建LUKS加密盘的命令为:

```
cryptsetup [其他参数] luksFormat 设备名
```

这里常用的参数有下面几个:

- --cipher

  加密方式

- --key-size

  密钥长度

- --hash

  散列算法

- --iter-time

  迭代时间，单位为毫秒。值越大，暴力破解越难，但打开加密盘的时间也越久

这里我们直接使用默认值

```
[lujun9972@X61 ~]$ cryptsetup luksFormat /tmp/USB.img 

WARNING!
========
这将覆盖 /tmp/USB.img 上的数据，该动作不可取消。

Are you sure? (Type uppercase yes): YES
输入 /tmp/USB.img 的密码：
确认密码：
[lujun9972@X61 ~]$ 
```

执行的过程中，命令会警告你将会清除磁盘上的所有数据，并要求你输入两次密码

### 打开密码盘

cryptsetup可以打开前面提到的各种加密盘。

打开加密盘的命令为

```
cryptsetup open --type 加密类型 加密磁盘 映射名称
```

或者也可以写成

```
cryptsetup 加密类型Open 加密磁盘 映射名称
```

比如，我们这个案例中可以执行:

```
[lujun9972@X61 ~]$ sudo cryptsetup luksOpen /tmp/USB.img USB
[sudo] lujun9972 的密码：
输入 /tmp/USB.img 的密码：
[lujun9972@X61 ~]$ 
```

注意这里需要用到root权限。

执行该命令后就会将 `/tmp/USB.img` 解密，并映射成 `/dev/mapper/USB`

### 像普通磁盘分区一样操作 `/dev/mapper/USB`

你可以像普通磁盘一样来操作 `/dev/mapper/USB`.

```
sudo mkfs.ext4 /dev/mapper/USB
sudo mount /dev/mapper/USB /mnt
sudo touch /mnt/secret
ls -l /mnt/secret
```

结果为

```
Creating filesystem with 100352 1k blocks and 25168 inodes
Filesystem UUID: b1557874-a538-4ffa-9ce0-c17e8feb4b1c
Superblock backups stored on blocks: 
        8193, 24577, 40961, 57345, 73729

Allocating group tables:  0/13     done                            
Writing inode tables:  0/13     done                            
Creating journal (4096 blocks): done
Writing superblocks and filesystem accounting information:  0/13     done

-rw------- 1 root root 0 Apr 12 18:39 /mnt/secret
```

### 查看加密盘状态

在打开加密盘后，可以查看该加密盘的状态，语法为

```
cryptsetup status 映射名
```

同样的，由于需要初始化device mapper,因此需要root权限：

```
sudo cryptsetup status USB
```

结果为

```
/dev/mapper/USB is active and is in use.
  type:    LUKS1
  cipher:  aes-xts-plain64
  keysize: 256 bits
  key location: dm-crypt
  device:  /dev/loop0
  loop:    /tmp/USB.img
  sector size:  512
  offset:  4096 sectors
  size:    200704 sectors
  mode:    read/write
```

### 关闭加密盘

操作完磁盘后，使用下面命令关闭加密盘

```
cryptsetup close 映射名
```

像这样：

```
sudo umount /mnt
sudo cryptsetup close USB
```

## 让加密盘使用keyfile认证



### 创建随机文件作为keyfile

```
dd if=/dev/urandom of=/tmp/keyfile bs=1K count=64
```

### 查看key slot

LUKS格式的加密盘默认能够提供8个"key slot",每个"key slot"就是一个解密的钥匙，使用任何一把钥匙都能打开这个LUKS加密盘。

相当于是能有多种解密方式。

要查看LUKS密码盘的"Key Slot",可以用下面命令：

```
cryptsetup luksDump 加密盘
```

比如

```
cryptsetup luksDump /tmp/USB.img
LUKS header information for /tmp/USB.img

Version:        1
Cipher name:    aes
Cipher mode:    xts-plain64
Hash spec:      sha256
Payload offset: 4096
MK bits:        256
MK digest:      0b 6b f3 5d fb 94 1a 8f aa c6 7e 86 d8 64 b0 0b c7 bf 7b 7d 
MK salt:        02 9b dc c3 0e 34 79 0b ab a9 44 e6 e4 ad 67 30 
                35 f1 dd cf e0 33 0c 36 bf bc 55 f1 d5 ce fb ad 
MK iterations:  70167
UUID:           e4e7cfc4-f9ae-4ed1-b65b-1b0e7b84ca7f

Key Slot 0: ENABLED
        Iterations:             1122672
        Salt:                   d2 04 39 66 d7 cb 64 6d e3 ef d9 88 c7 1c 07 b2 
                                25 00 8f bf e3 6d f1 9e 3f 31 91 c6 f0 ff 6d 75 
        Key material offset:    8
        AF stripes:             4000
Key Slot 1: DISABLED
Key Slot 2: DISABLED
Key Slot 3: DISABLED
Key Slot 4: DISABLED
Key Slot 5: DISABLED
Key Slot 6: DISABLED
Key Slot 7: DISABLED
```

你会发现，这个LUKS加密盘目前只使用了一个Key Slot，也就是创建盘时设置的密码

### 添加keyfile认证

使用下面命令为LUKS加密盘添加keyfile认证

```
cryptsetup luksAddKey 加密盘 keyfile
```

比如

```
[lujun9972@X61 ~]$ cryptsetup luksAddKey /tmp/USB.img /tmp/keyfile
输入任意已存在的密码：
[lujun9972@X61 ~]$ 
```

再查一下Key Slot:

```
cryptsetup luksDump /tmp/USB.img
LUKS header information for /tmp/USB.img

Version:        1
Cipher name:    aes
Cipher mode:    xts-plain64
Hash spec:      sha256
Payload offset: 4096
MK bits:        256
MK digest:      0b 6b f3 5d fb 94 1a 8f aa c6 7e 86 d8 64 b0 0b c7 bf 7b 7d 
MK salt:        02 9b dc c3 0e 34 79 0b ab a9 44 e6 e4 ad 67 30 
                35 f1 dd cf e0 33 0c 36 bf bc 55 f1 d5 ce fb ad 
MK iterations:  70167
UUID:           e4e7cfc4-f9ae-4ed1-b65b-1b0e7b84ca7f

Key Slot 0: ENABLED
        Iterations:             1122672
        Salt:                   d2 04 39 66 d7 cb 64 6d e3 ef d9 88 c7 1c 07 b2 
                                25 00 8f bf e3 6d f1 9e 3f 31 91 c6 f0 ff 6d 75 
        Key material offset:    8
        AF stripes:             4000
Key Slot 1: ENABLED
        Iterations:             1109604
        Salt:                   38 3a 6a 76 c3 10 7c a3 1f fd e8 7c 1a 7f 4b 4f 
                                2a bf 99 6c 1c 06 11 00 59 5e ce e4 99 79 79 f7 
        Key material offset:    264
        AF stripes:             4000
Key Slot 2: DISABLED
Key Slot 3: DISABLED
Key Slot 4: DISABLED
Key Slot 5: DISABLED
Key Slot 6: DISABLED
Key Slot 7: DISABLED
```

会发现启用了新的key slot

### 使用keyfile打开加密盘

使用keyfile打开加密盘的方式跟普通打开加密盘的方式类似，只是要多用一个 `--keyfile` 来指定keyfile的路径

```
sudo cryptsetup --key-file /tmp/keyfile open --type luks /tmp/USB.img USB
```

### 删除keyslot

使用下面命令可以删除加密盘的其中一个key slot

```
cryptsetup luksKillSlot /tmp/USB.img 0
```

再查一下Key Slot:

```
cryptsetup luksDump /tmp/USB.img
LUKS header information for /tmp/USB.img

Version:        1
Cipher name:    aes
Cipher mode:    xts-plain64
Hash spec:      sha256
Payload offset: 4096
MK bits:        256
MK digest:      0b 6b f3 5d fb 94 1a 8f aa c6 7e 86 d8 64 b0 0b c7 bf 7b 7d 
MK salt:        02 9b dc c3 0e 34 79 0b ab a9 44 e6 e4 ad 67 30 
                35 f1 dd cf e0 33 0c 36 bf bc 55 f1 d5 ce fb ad 
MK iterations:  70167
UUID:           e4e7cfc4-f9ae-4ed1-b65b-1b0e7b84ca7f

Key Slot 0: DISABLED
Key Slot 1: ENABLED
        Iterations:             1109604
        Salt:                   38 3a 6a 76 c3 10 7c a3 1f fd e8 7c 1a 7f 4b 4f 
                                2a bf 99 6c 1c 06 11 00 59 5e ce e4 99 79 79 f7 
        Key material offset:    264
        AF stripes:             4000
Key Slot 2: DISABLED
Key Slot 3: DISABLED
Key Slot 4: DISABLED
Key Slot 5: DISABLED
Key Slot 6: DISABLED
Key Slot 7: DISABLED
```

会发现key slot0已经被禁用了