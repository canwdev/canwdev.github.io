## Hyper-V 装 Win7 驱动问题

参考： https://foxi.buduanwang.vip/virtualization/pve/1551.html/

去微软官网下载对应系统的更新包： https://support.microsoft.com/en-us/topic/hyper-v-integration-components-update-for-windows-virtual-machines-8a74ffad-576e-d5a0-5a2f-d6fb2594f990

并且`使用管理员身份运行cmd` 加载补丁，注意替换路径。

`Dism /online /Add-Package /PackagePath:C:\Users\Administrator\Desktop\windows6.x-hypervintegrationservices-x64.cab`


XP系统参考：
- https://docs.microsoft.com/en-us/archive/blogs/manageabilityguys/deploying-hyper-v-integration-services-to-vms-using-config-manager-and-dism
- https://kinakomochi-tank.hatenablog.com/entry/2020/11/23/104948
