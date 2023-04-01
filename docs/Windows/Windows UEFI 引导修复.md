参考：[UEFI引导修复 - 知乎 (zhihu.com)](https://zhuanlan.zhihu.com/p/455985072)

## 挂载EFI分区

推荐使用 DiskGenius 挂载ESP分区，更方便。

参考： https://cloud.tencent.com/developer/article/2138700

以管理员身份启动 cmd，输入 `diskpart`，进入 dispart 之后的操作如下：
```javascript
$ list disk        #列出磁盘
$ select disk 0    #选择第0个磁盘
$ list partition   #列出分区
$ select partition 1   #选择第一个分区类型为系统 默认大小为550MB 的那个系统分区
$ assign letter=b   #挂载到 卷号B
```

## 用 bcbboot 自动修复

### 不指定 esp 分区修复

进入Win10 PE环境（必须UEFI启动），打开cmd命令行，输入以下命令

`bcdboot C:\Windows /l zh-cn`

-  `C:\Windows` 硬盘系统目录，根据实际情况修改
- `/l zh-cn` 指定uefi启动界面语言为简体中文

### 指定 esp 分区修复

进入Win10 PE环境（UEFI或Legacy都可），打开cmd命令行，输入以下命令

`bcdboot C:\Windows /s o: /f uefi /l zh-cn`

其中：

- `C:\Windows` 硬盘系统目录
- `/s o:` 指定esp分区所在磁盘，如果不存在请先挂载
- `/f uefi` 指定启动方式为uefi
- `/l zh-cn` 指定uefi启动界面语言为简体中文
