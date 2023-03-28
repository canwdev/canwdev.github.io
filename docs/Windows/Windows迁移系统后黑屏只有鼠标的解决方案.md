出现这个问题的原因是系统盘挂载到了错误的盘符，我们需要进入PE系统，使用注册表编辑器将盘符改回C盘，或直接删除所有盘符分配（让系统重启后自动分配）。

1. 进入PE系统然后运行 `regedit` 调出注册表
2. 选中 `HKEY_LOCAL_MACHINE`，打开菜单操作：文件-加载配置单元，然后找到系统目录 `C:\Windows\System32\config\`，选择 `SYSTEM` 文件
3. 在弹出对话框中输入【任意名称】，然后进入注册表 `HKEY_LOCAL_MACHINE\【任意名称】`
4. 把 `mountedevices` 里面的内容全部删除，卸载配置单元
5. 重启系统就会自动恢复

参考：
- [1分钟解决系统迁移克隆分区后的启动问题 蓝屏 黑屏 只剩鼠标指针_哔哩哔哩_bilibili](https://www.bilibili.com/video/BV1Jh411279E)
- [迁移系统后黑屏 只有鼠标可以动【解决方法】_hkzdcc的博客-CSDN博客_系统迁移后黑屏](https://blog.csdn.net/hkzdcc/article/details/116452275)