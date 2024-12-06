> 本地推流需要启动==推流服务器==。推流服务器是一个接收推流数据并流转给其他播放器的中间服务。推流服务器需要安装在具有公网 IP 的服务器上，同时被推流端和播放端访问到。在本地推流时，则需要将推流服务器搭建在本地 PC 上。在 OBS Studio 中进行推流时，需要将推流地址设置为==推流服务器==的相应地址。在推流服务器正确配置后，即可通过本地推流方式将视频数据传输到推流服务器上，并使用 VLC / PotPlayer 等播放器查看推流效果。

参考：

- https://www.jianshu.com/p/160c027bf482
- https://juejin.cn/post/7069593614795571214
- 推荐使用 https://github.com/gwuhaolin/livego/blob/master/README_cn.md

1. 启动 livego
2. 访问 http://localhost:8090/control/get?room=movie 获取推流码
3. 在 OBS Studio 设置-直播
	- 服务器 rtmp://127.0.0.1:1935/live
	- 填写推流码
4. 使用 VLC 播放（Ctrl+N），支持两种方式
	- rtmp://localhost:1935/live/movie
	- http://127.0.0.1:7001/live/movie.flv

flv 方式可以使用 flv.js 在网页端播放，HTML 代码如下

```html
<!DOCTYPE html>
<html>
<head>
   <meta charset="UTF-8">
   <title>直播</title>
</head>
<body>
   <script src="https://cdn.bootcss.com/flv.js/1.4.0/flv.min.js"></script>
   <video id="videoElement" width="100%" controls></video>
   <script>
       if (flvjs.isSupported()) {
           var videoElement = document.getElementById('videoElement');
           var flvPlayer = flvjs.createPlayer({
               type: 'flv',
               url: 'http://127.0.0.1:7001/live/movie.flv'
           });
           flvPlayer.attachMediaElement(videoElement);
           flvPlayer.load();
           flvPlayer.play();
       }
   </script>
</body>
</html>
```