##  Ubuntu 实用软件

- 浏览器
	- Chrome
		- `wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb`
		- `sudo dpkg -i ./google-chrome-stable_current_amd64.deb`
	- Firefox
		- https://www.mozilla.org/en-US/firefox/linux/
- Wine 模拟器
	- `sudo apt install wine`
	- wine32: `sudo dpkg --add-architecture i386 && sudo apt-get update && sudo apt-get install wine32`

## Wine 中文乱码解决

- [参考](https://juejin.cn/post/6844903917742981128)
1. 首先确保系统语言为中文 [[Ubuntu#Ubuntu 终端下修改语言]]
3. 复制 Windows 系统中的 **msyh.ttc** **simsun.ttc** （位于 `C:\Windows\Fonts\`）到 wine 的字体目录（位于 `~/.wine/drive_c/windows/Fonts/`） 
4. 创建一个 `font.reg`，填写以下内容：
```reg
REGEDIT4
 
[HKEY_LOCAL_MACHINE\Software\Microsoft\Windows NT\CurrentVersion\FontLink\SystemLink]
"Lucida Sans Unicode"="msyh.ttc"
"Microsoft Sans Serif"="msyh.ttc"
"MS Sans Serif"="msyh.ttc"
"Tahoma"="msyh.ttc"
"Tahoma Bold"="msyhbd.ttc"
"msyh"="msyh.ttc"
"Arial"="msyh.ttc"
"Arial Black"="msyh.ttc"
```
5. 在wine的cmd中执行命令才能生效：`regedit font.reg`
6. 修改对话框字体：编辑wine 的 system.reg配置文件 `~/.wine/system.reg`
7. 查找 `MS Shell Dlg`，把值改为 `msyh`，保存生效
## Ubuntu 终端下修改语言

- 修改为中文
	1. 安装语言包：`sudo apt-get install language-pack-zh-hans`
	2. 修改locale文件配置：`vim /etc/default/locale`
	3. 修改配置文件为：`LANG=zh_CN.UTF-8`
	4. 保存，重启：`sudo reboot`
- 修改为英文
	1. 安装语言包：`sudo apt-get install language-pack-en`
	2. 然后添加英文支持：`locale-gen en_US.UTF-8`
	3. 修改locale文件配置：`vim /etc/default/locale`
	4. 修改配置文件为：`LANG=en_US.UTF-8`
	5. 保存，重启：`sudo reboot`
