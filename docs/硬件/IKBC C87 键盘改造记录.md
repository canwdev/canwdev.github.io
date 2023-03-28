## 1. 键线分离

参考：
- [大泡泡的DIY 篇二十六：键线分离 DIY，只需十块钱，让传统 ikbc 机械键盘用上 Type-C_键盘_什么值得买 (smzdm.com)](https://post.smzdm.com/p/a5o876wx/)
- [IKBC C87 usb线序_euzen的博客-CSDN博客_ikbc线序](https://blog.csdn.net/euzen/article/details/107925001)
- [简单几步，自己就能给键盘加灯、改键线分离，IKBC C87樱桃茶轴改造全程实录_哔哩哔哩_bilibili](https://www.bilibili.com/video/BV1Xb411S7Pd/?vd_source=82220a88e46ac49340dd39f2a953dee6)
---

- 红 - V  
- 黄 - SG（屏蔽线，可不接，看到网上图片也有是黑色的，即两条黑线，但屏蔽线比其他线要粗些）  
- 黑 - G  
- 绿 - D-  
- 白 - D+

到 [ikbc 键线分离模块 - 嘉立创EDA开源硬件平台 (oshwhub.com)](https://oshwhub.com/BigBubble/jian-xian-fen-li) 使用下单助手免费打了5片板子，除了 Type-C 母座比较难焊以外都很顺利，这块板子的 D+/D- 是相反的，使用时要交换原来绿色和白色的线序，否则无法识别。

## 2. 加灯

参考：
- [简单几步，自己就能给键盘加灯、改键线分离，IKBC C87樱桃茶轴改造全程实录_哔哩哔哩_bilibili](https://www.bilibili.com/video/BV1Xb411S7Pd)
- [2020年IKBC C87 加灯成功_键盘_什么值得买 (smzdm.com)](https://post.smzdm.com/p/a2597v62/)
- [Ikbc C87无灯键盘加灯实现全部灯效_键盘_什么值得买 (smzdm.com)](https://post.smzdm.com/p/a5k6kqpx/)

经测试，我手上这把C87（买于2018年）加灯并不能亮，并且主板与网上所有的主板都不同，多了几个芯片焊接位，猜测是这个版本没有装灯控芯片。另一把2019年的可以用。

LED 正负极顺序：长脚为正极，短脚为负极；轴体上显示A的那边是正极。注意：LED反装仍然能亮，但是不会响应灯效，请勿装反！

键盘装灯后居然出现了段落感，原因是键帽碰到了LED的顶部，可以把装好的LED往轴体中心掰。