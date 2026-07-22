## Windows 沙盒配置示例

[参考](https://sspai.com/post/70356) [官方文档](https://learn.microsoft.com/zh-cn/windows/security/threat-protection/windows-sandbox/windows-sandbox-configure-using-wsb-file)

保存以下内容至 `test.wsb` 文件，双击打开此文件即可启动，配置解释如下：
- VGpu：是否启用显卡（如果改为 `Disable` 则表示禁用）
- Networking：是否启用网络
- ClipboardRedirection：剪贴板重定向
- ProtectedClient：开启会导致用户无法在主机和沙盒间复制粘贴文件
- PrinterRedirection：打印机重定向
- MemoryInMB：沙盒内存大小（MB）
- MappedFolders：文件夹映射
- LogonCommand：沙盒启动后执行的命令
```xml
<Configuration>
    <VGpu>Enable</VGpu>
    <Networking>Enable</Networking>
    <AudioInput>Enable</AudioInput>
    <VideoInput>Enable</VideoInput>
    <ClipboardRedirection>Enable</ClipboardRedirection>
    <ProtectedClient>Enable</ProtectedClient>
    <PrinterRedirection>Enable</PrinterRedirection>
    <MemoryInMB>4096</MemoryInMB>
    <MappedFolders>
        <MappedFolder>
          <HostFolder>D:\Download</HostFolder>
          <SandboxFolder>C:\Users\WDAGUtilityAccount\Downloads</SandboxFolder>
          <ReadOnly>false</ReadOnly>
        </MappedFolder>
        <MappedFolder>
          <HostFolder>D:\Sandbox</HostFolder>
          <ReadOnly>false</ReadOnly>
        </MappedFolder>
    </MappedFolders>
    <LogonCommand>
        <Command>winver</Command>
    </LogonCommand>
</Configuration>
```


