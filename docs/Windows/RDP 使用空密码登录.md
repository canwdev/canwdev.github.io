在RDP主机上设置：

1. 按下“Win+R”打开“运行”输入 gpedit.msc
2. 点击“计算机配置”，“Windows设置”—>“安全设置”—>“本地策略”
	- 也可以在开始菜单 -> 管理工具 -> 本地安全策略
3. 点击右侧的“安全选项”
4. 双击“账户：使用空密码的本地账户只允许进行控制台登陆”
	- 英文版为：Account: Limit local account use of blank passwords to console login only
5. 选择“已禁用”点击“确定”即可
6. 参考： https://www.jb51.net/os/win10/746086.html