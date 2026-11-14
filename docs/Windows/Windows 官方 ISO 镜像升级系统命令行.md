
- .\setup.exe：运行当前目录的 Windows 安装程序
- /auto upgrade：自动执行就地升级，保留文件、设置和应用程序
- /dynamicupdate disable：升级过程中禁用动态更新，不联网下载更新或驱动
- /eula accept：自动接受许可协议
- /product server：以 Server 产品模式运行，常用于绕过 Windows 11 的 TPM/CPU 等硬件检查

```
.\setup.exe /auto upgrade /dynamicupdate disable /eula accept /product server
```


整体作用：保数据升级 Windows，跳过自动更新，自动接受协议，并绕过硬件兼容性检查。