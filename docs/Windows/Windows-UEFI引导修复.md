# UEFI引导修复
[UEFI引导修复 - 知乎 (zhihu.com)](https://zhuanlan.zhihu.com/p/455985072)

## 一、用bcbboot自动修复

我们建议大家启动64位8PE，用它带的bcdboot来修复。

### (一)指定esp分区修复

环境为64位8PE，bios/uefi启动进入下都可以

启动64位8PE，并用esp分区挂载器或diskgenuis挂载esp分区

打开cmd命令行，输入以下命令并运行

`bcdboot C:\Windows /s o: /f uefi /l zh-cn`

其中：`C:\Windows` 硬盘系统目录，根据实际情况修改

/s o: 指定esp分区所在磁盘，根据实际情况修改

/f uefi 指定启动方式为uefi

/l zh-cn 指定uefi启动界面语言为简体中文

注：64位7PE不带/s参数，故7PE不支持bios启动下修复

### (二)不指定esp分区修复

环境为64位Win7或Win8PE，只有uefi启动进入Win PE才可以

不用挂载esp分区，直接在cmd命令行下执行：

`bcdboot C:\Windows /l zh-cn`

其中 C:\Windows 硬盘系统目录，根据实际情况修改

/l zh-cn 指定uefi启动界面语言为简体中文

注：在Win8 PE中，我们也可以在uefi启动进入Win pe后，挂载esp分区用方法(一)修复

---

## 二、用bootice手动修复

从efi引导启动过程来看，虽然它的文件很多，但主要用到的就是两文件，我们完全可以在各Winpe下挂载esp分区，从硬盘系统中复制bootx64.efi文件，然后用用bootice制作好bcd，就完成efi引导修复。

1、启动任一Win pe，用esp分区挂载器或diskgenuis挂载esp分区

2、查看esp分区是否可正常读写，如不正常可重新格式化为fat16分区格式。

3.在esp分区中建立如下空文件夹结构

``\efi\boot\`` (bootx64.efi等复制)

`\efi\microsoft\boot\` (bcd等建立)

4、复制硬盘系统中的bootmgfw.efi(一般在 `C:\Windows\boot\efi` 下)到esp分区的 `\efi\boot\` 下，并重命名为bootx64.efi

5、打开bootice软件，有esp分区的 `\efi\microsoft\boot\` 下新建立一bcd文件，

打开并编辑bcd文件，添加“windows vista/7/8启动项，指定磁盘为硬盘系统盘在的盘，指定启动分区为硬盘系统分区(一般为c:)

指定启动文件为：`\Windows\system32\winload.efi` ， 是*.efi，不是*.exe，要手工改过来

最后保存当前系统设置并退出。

注：Winxp PE不能识别gpt格式的硬盘分区，用2003PE中的disk.sys替换xpPE内核中的相应文件，就可以让xpPE也能识别gpt磁盘格式分区

指定启动分区不是esp分区所在分区，就是硬盘64位Win7、Win8 系统所在分区

指定启动文件为：`\Windows\system32\winload.efi` ，是*.efi，不是*.exe，要手工改过来。