## macOS Monterey 壁纸位置

- 下载壁纸位置：`/Users/你的用户名/Library/Application Support/com.apple.mobileAssetDesktop`
- 系统内置壁纸位置：`/System/Library/Desktop Pictures`

## 禁止雷蛇自动安装驱动：

- 进入文件夹 `C:\Windows\Installer\Razer`
- 把 Installer 删除
- 创建一个空文件，重命名为 Installer
- 完成！


## Syncthing 常见问题

- 设备长期离线后，再次连接，在其他设备删除的文件可能又会被同步回来，所以要尽量保持设备在线。
- SyncTrazor 遇到冲突文件后，点击会弹窗让你选择保留哪个文件，但是翻译非常反人类，总之就是让你看不懂，正确的翻译如下：
	- 上面的按钮：保留新版
	- 下面的按钮：保留旧版
- SyncTrazor 如何升级最新版本 syncthing：去[官网](https://syncthing.net/downloads/) 下载最新版主程序，解压 `syncthing.exe` 到 SyncTrazor 目录。

## 如何舒适的使用 61 键盘

61键盘最不爽的就是没有上下左右键，有一些方案可以使用组合键更方便地触发： 

- [lydell/spacefn-win: A Windows implementation of the SpaceFN keyboard layout. (github.com)](https://github.com/lydell/spacefn-win)
- [OhYee/SpaceFn: SpaceFn key mapping (github.com)](https://github.com/OhYee/SpaceFn)
- [jinweijie/vim-style-cursor-move: Replace arrow keys with Alt + hjkl binding using Autohotkey on Windows, Karabiner on Mac and Autokey on Linux. (github.com)](https://github.com/jinweijie/vim-style-cursor-move)

## 把 Steam 的游戏拷贝到另一台电脑

原文：https://www.zhihu.com/question/270062762/answer/351631966

1. steamapps文件夹内，保存所有appmanifest文件，可以放入网盘或U盘，
2. 然后把steamapps里的common文件夹压缩成分卷放入U盘，
3. 在新电脑上安装steam，别急着启动，在steamapps里解压复原appmanifest文件的位置和common文件夹后登录即可，
4. 出问题验证完整性。