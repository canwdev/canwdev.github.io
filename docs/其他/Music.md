## 音乐格式

- FLAC 无损压缩格式，能最大程度保留音频原始质量，但其占用存储空间较多。
- mp3 格式中，320kbps 码率为常用推荐选项。若希望减小文件体积，同时又保证在多数普通设备上听觉体验无明显差异，也可选用 192kbps 码率 。
- 极限压缩场景下，可采用 opus 格式（96kbps，ogg 封装）。不过此格式并不适用于音乐存储，更推荐用于播客节目或其他纯语音类内容。

## 音乐播放器

- Foobar 2000: PC 端近乎完美的音乐播放器，移动端也有，但不支持歌词
- AIMP: 可用于转换 mp3 为 opus，并保留全部元数据（包括封面）
- One Player: iOS 端的本地音乐播放器，对歌词支持程度一般
- Folder Music Player: Android 端的本地音乐播放器

## 同步

### 本地文件同步推荐使用 rclone

```bat
rclone sync D:\MusicCenter\ J:\MusicCenter\ --track-renames --progress -v --transfers 8 --checkers 8
```

### Sync to iPhone

iOS 推荐使用 Mobius Sync 进行同步，iOS 端唯一的基于 Syncthing 的同步软件。

或使用数据线在Linux下同步：
```shell
ifuse --documents com.foobar2000.mobile ~/iPhone/documents/com.foobar2000.mobile

rsync -vrP --ignore-existing --delete /home/can/Music/MusicCenter/ACG/ /home/can/iPhone/documents/com.foobar2000.mobile/ACG000/
```

## 在Foobar 2000 ABX Comparator 中，p值越小说明了什么

在 Foobar 2000 的 ABX Comparator 中，p 值表示你通过随机猜测正确区分两个音频样本的概率。p 值越小，说明你区分两个音频样本的结果越不可能是靠猜的，也就是说，你越有可能确实听出了它们之间的差异。

具体来说：

- **p 值很小**（通常小于 0.05，比如 5%）：表示你的测试结果具有统计显著性，说明你很可能真的能分辨出两个音频样本的差异，而不是偶然猜对。
- **p 值较大**（比如大于 0.05）：表示你的测试结果可能只是随机猜测，缺乏足够证据证明你能可靠区分两个样本。

简单总结：p 值越小，你的测试结果越可信，说明你听出的差异越真实。