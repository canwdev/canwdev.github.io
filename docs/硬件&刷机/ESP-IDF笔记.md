- [ESP-IDF 编程指南](https://docs.espressif.com/projects/esp-idf/zh_CN/latest/esp32/)推荐使用最新稳定版本，目前稳定版本为 [4.4.3](https://docs.espressif.com/projects/esp-idf/zh_CN/v4.4.3/esp32/index.html)

## v4.4.x 环境搭建

> [!INFO]
> 官方文档写的非常详细：[快速入门 - ESP32 - — ESP-IDF 编程指南 v4.4.3 文档 (espressif.com)](https://docs.espressif.com/projects/esp-idf/zh_CN/v4.4.3/esp32/get-started/index.html#get-started-get-prerequisites)
> 建议阅读官方文档来入门。

- Windows 用户
	- 推荐使用离线安装器：[ESP-IDF 工具安装器](https://dl.espressif.com/dl/esp-idf/?idf=4.4)，里面集成了大部分环境，无需再配置环境。
- Linux 用户
	- 安装环境
		- Ubunt `sudo apt-get install git wget flex bison gperf python3 python3-pip python3-setuptools cmake ninja-build ccache libffi-dev libssl-dev dfu-util libusb-1.0-0`
		- ArchLinux `sudo pacman -S --needed gcc git make flex bison gperf python-pip cmake ninja ccache dfu-util libusb`
		- ESP-IDF 支持 Python 3.6 及以上版本
	- 下载 [esp-idf-v4.4.3.zip](https://dl.espressif.com/github_assets/espressif/esp-idf/releases/download/v4.4.3/esp-idf-v4.4.3.zip) 并解压至 `~/esp` 目录。
	- 设置工具，执行以下命令：`cd ~/esp/esp-idf && ./install.sh esp32`
	- 设置环境变量，将 `alias get_idf='. $HOME/esp/esp-idf/export.sh'` 添加到 `.bashrc` 中，执行 `get_idf` 即可在当前终端添加环境变量

> [!INFO] 
> 安装完环境后，推荐使用 VSCode ESP-IDF 插件优化开发体验

## v3.3.x

### 环境变量设置
~/.zshrc
```sh
alias get_idf='. $HOME/esp/esp-idf/export.sh'
```
~/esp/esp-idf/export.sh
```sh
export IDF_PATH="$HOME/esp/esp-idf/"
export PATH="$HOME/esp/xtensa-esp32-elf/bin:$PATH"
export PATH="$HOME/esp/esp-idf/tools:$PATH"
```

## [idf.py](https://docs.espressif.com/projects/esp-idf/zh_CN/v4.4.3/esp32/api-guides/build-system.html#idf-py) 常用命令

- `idf.py set-target <target>` 会设置构建项目的目标（芯片）
- `idf.py menuconfig` 会运行 `menuconfig` 工具来配置项目
- `idf.py build` 会构建在当前目录下找到的项目
- `idf.py clean` 会把构建输出的文件从 `build` 目录中删除，不会删除 CMake 配置输出及其他文件
- `idf.py fullclean` 会将整个 `build` 目录下的内容全部删除
- `idf.py flash` 刷机命令
- `idf.py monitor` 用于显示目标 ESP32 设备的串口输出

## Linux 权限问题 /dev/ttyUSB0

刷入命令：`idf.py -p /dev/ttyUSB0 -b 921600 flash ` 会遇到没有权限的问题，此时可以用 `sudo` 来提权，或者输入以下命令，重启解决（[与 ESP32 创建串口连接](https://docs.espressif.com/projects/esp-idf/zh_CN/latest/esp32/get-started/establish-serial-connection.html#linux-dialout-group) ）
- Ubuntu:  `sudo usermod -a -G dialout $USER`
- ArchLinux: `sudo usermod -a -G uucp $USER`

## VSCode ESP-IDF 安装失败解决方案

在执行这个步骤之后报错：
```
Installing ESP-IDF Debug Adapter python packages in D:/Espressif/python_env/idf4.4_py3.8_env/Scripts/python.exe

...开始报错...
```

> [!WARNING]
> 错误原因：没有关闭 Clash 代理导致 pip 下载失败

一定要关闭 Clash 代理工具，否则一直会报这个错误：
```
(Caused by SSLError(SSLEOFError(8, 'EOF occurred in violation of protocol
```

编辑 Python pip 镜像源 `C:\Users\<username>\AppData\Roaming\pip\pip.ini`，加速下载
```
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
[install]
trusted-host=pypi.tuna.tsinghua.edu.cn
```
或使用命令：
```
D:\Espressif\python_env\idf4.4_py3.8_env\Scripts\python.exe -m pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

成功安装！VSCode 配置文件会多出以下配置：
```json
{
    "idf.espIdfPathWin": "D:/Espressif/frameworks/esp-idf-v4.4.3/",
    "idf.pythonBinPathWin": "D:/Espressif/python_env/idf4.4_py3.8_env/Scripts/python.exe",
    "idf.toolsPathWin": "D:\\Espressif",
    "idf.customExtraPaths": "D:\\Espressif\\tools\\xtensa-esp32-elf\\esp-2021r2-patch5-8.4.0\\xtensa-esp32-elf\\bin;D:\\Espressif\\tools\\xtensa-esp32s2-elf\\esp-2021r2-patch5-8.4.0\\xtensa-esp32s2-elf\\bin;D:\\Espressif\\tools\\xtensa-esp32s3-elf\\esp-2021r2-patch5-8.4.0\\xtensa-esp32s3-elf\\bin;D:\\Espressif\\tools\\riscv32-esp-elf\\esp-2021r2-patch5-8.4.0\\riscv32-esp-elf\\bin;D:\\Espressif\\tools\\esp32ulp-elf\\2.35_20220830\\esp32ulp-elf\\bin;D:\\Espressif\\tools\\cmake\\3.23.1\\bin;D:\\Espressif\\tools\\openocd-esp32\\v0.11.0-esp32-20220706\\openocd-esp32\\bin;D:\\Espressif\\tools\\ninja\\1.10.2;D:\\Espressif\\tools\\idf-exe\\1.0.3;D:\\Espressif\\tools\\ccache\\4.3\\ccache-4.3-windows-64;D:\\Espressif\\tools\\dfu-util\\0.9\\dfu-util-0.9-win64",
    "idf.customExtraVars": "{\"OPENOCD_SCRIPTS\":\"D:\\\\Espressif\\\\tools\\\\openocd-esp32\\\\v0.11.0-esp32-20220706/openocd-esp32/share/openocd/scripts\",\"IDF_CCACHE_ENABLE\":\"1\"}"
}
```

## ESP32 各版本区别

- ESP32 WROVER IE / ESP32 WROVER E 的区别是：IE是外置天线，E是内置天线。通过观察 [2201121630_Espressif-Systems-ESP32-WROVER-IE-8MB_C2934565.pdf (lcsc.com)](https://datasheet.lcsc.com/lcsc/2201121630_Espressif-Systems-ESP32-WROVER-IE-8MB_C2934565.pdf) 可以得知。
- [ESP32选型一文就够，ESP32-WROOM-32、ESP32-WROVER、ESP32-S衍生模组、ESP32-PICO差异 - 哔哩哔哩 (bilibili.com)](https://www.bilibili.com/read/cv15539489)
- 官方产品对比：[ESP Product Selector (espressif.com)](https://products.espressif.com/#/product-comparison)