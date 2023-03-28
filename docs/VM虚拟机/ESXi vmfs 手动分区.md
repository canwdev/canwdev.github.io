使用 web 控制台分区的时候出现：无法创建VMFS数据存储，无法更改主机配置。为了不删除所有硬盘分区，我们需要手动进行分区。


- 参考：https://blog.csdn.net/weixin_42293131/article/details/118420356


## 1. 查看分区表

```sh
[root@localhost:/dev/disks] partedUtil getptbl /dev/disks/t10.NVMe____WDC_WDS100T2B0C2D00PXH0__________________64FD30464A441B00
gpt
121601 255 63 1953525168
1 2048 616447 C12A7328F81F11D2BA4B00A0C93EC93B systemPartition 128
2 616448 878591 E3C9E3160B5C4DB8817DF92DF00215AE microsoftRsvd 0
3 878592 269316095 0FC63DAF848347728E793D69D8477DE4 unknown 0
4 269316096 286095359 0657FD6DA4AB43C484E50933C84B4F4F linuxSwap 0
5 286095360 554530815 0FC63DAF848347728E793D69D8477DE4 unknown 0
6 554530816 822966271 EBD0A0A2B9E5443387C068B6B72699C7 linuxNative 0
7 822966272 1953523711 0FC63DAF848347728E793D69D8477DE4 unknown 0
```

其中，6 号是我们需要的分区。

## 2. 重写分区表

> 记得备份！

```sh
partedUtil setptbl /dev/disks/t10.NVMe____WDC_WDS100T2B0C2D00PXH0__________________64FD30464A441B00 gpt \
"1 2048 616447 C12A7328F81F11D2BA4B00A0C93EC93B 128" \
"2 616448 878591 E3C9E3160B5C4DB8817DF92DF00215AE 0" \
"3 878592 269316095 0FC63DAF848347728E793D69D8477DE4 0" \
"4 269316096 286095359 0657FD6DA4AB43C484E50933C84B4F4F 0" \
"5 286095360 554530815 0FC63DAF848347728E793D69D8477DE4 0" \
"6 554530816 822966271 AA31E02A400F11DB9590000C2911D1B8 0" \
"7 822966272 1953523711 0FC63DAF848347728E793D69D8477DE4 0"
```

## 3. 格式化新分区

```sh
vmkfstools -C vmfs6 -S nvme_datastore t10.NVMe____WDC_WDS100T2B0C2D00PXH0__________________64FD30464A441B00:6
```

输出：

```
create fs deviceName:'t10.NVMe____WDC_WDS100T2B0C2D00PXH0__________________64FD30464A441B00:6', fsShortName:'vmfs6', fsName:'nvme_datastore'
deviceFullPath:/dev/disks/t10.NVMe____WDC_WDS100T2B0C2D00PXH0__________________64FD30464A441B00:6 deviceFile:t10.NVMe____WDC_WDS100T2B0C2D00PXH0__________________64FD30464A441B00:6
ATS on device /dev/disks/t10.NVMe____WDC_WDS100T2B0C2D00PXH0__________________64FD30464A441B00:6: not supported
.
Checking if remote hosts are using this device as a valid file system. This may take a few seconds...
Creating vmfs6 file system on "t10.NVMe____WDC_WDS100T2B0C2D00PXH0__________________64FD30464A441B00:6" with blockSize 1048576, unmapGranularity 1048576, unmapPriority default and volume label "nvme_datastore".
Successfully created new volume: 614fe1e0-e3c5bc6e-d842-1c697aa767ec
```

---

## 附：ESXi/ESX 常用分区类型参考

| 分区           | GUID                             | 类型（十六进制） | 类型（十进制） |
| -------------- | -------------------------------- | ---------------- | -------------- |
| VMFS 数据存储  | AA31E02A400F11DB9590000C2911D1B8 | 0xFB             | 251            |
| VMKCore 诊断   | 9D27538040AD11DBBF97000C2911D1B8 | 0xFC             | 252            |
| VMware 预留    | 9198EFFC31C011DB8F78000C2911D1B8 |                  |                |
| 基本数据       | EBD0A0A2B9E5443387C068B6B72699C7 | 0x83             | 131            |
| Linux Swap     | 0657FD6DA4AB43C484E50933C84B4F4F | 0x82             | 130            |
| Linux LVM      | E6D6D379F50744C2A23C238F2A3DF928 | 0x8E             | 142            |
| Linux RAID     | A19D880F05FC4D3BA006743F0F84911E | 0xFD             | 253            |
| EFi 系统       | C12A7328F81F11D2BA4B00A0C93EC93B | 0xEF             | 239            |
| Microsoft 预留 | E3C9E3160B5C4DB8817DF92DF00215AE |                  |                |
| 未使用条目     | 00000000000000000000000000000000 |                  |                |
| Fat16          |                                  | 0x6              | 6              |
| 扩展           |                                  | 0x5              | 5              |
| SFS            |                                  | 0x42             | 66             |
| NTFS           |                                  | 0x7              | 7              |
