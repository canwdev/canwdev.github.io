# media-compress — 图像 / 视频批量压缩

## 功能

- 图像走 **caesiumclt**，视频走 **HandBrakeCLI**，按扩展名自动分流，互不干扰
- 工具路径**自动查找**，无需配置
- 输出到各自的 `<源目录>/_compressed/`，镜像源目录结构，**原文件始终不动**
- 未压缩的文件默认**原样复制**进输出目录，所以输出目录可以替代源目录
- 在输出目录写一份带完整命令行的日志，可用 `--log no` 关闭
- 不写台账、不加锁，产物只有压缩后的文件和那份日志

## 下载工具

- caesiumclt：<https://github.com/Lymphatus/caesium-clt>，处理图像
- HandBrakeCLI：<https://handbrake.fr/downloads2.php>，处理视频，放进 HandBrake 安装目录
- ffmpeg / ffprobe：随 <https://ffmpeg.org/download.html> 提供；ffmpeg 压音乐，ffprobe 校验结果

都在 PATH 里最省事；HandBrake 装在非系统盘也能被找到。找不到或找错了，可以用
环境变量直接指定：`CAESIUM_CLT`、`HANDBRAKE_CLI`、`FFMPEG`、`FFPROBE`。

## 参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `<文件或目录...>` | 必填 | 可多个，目录会递归扫描 |
| `-o, --output <目录>` | 各自的 `_compressed/` | 所有输入共用一个输出目录 |
| `--only image\|video\|audio` | 全部 | 只**压缩**这一类；其余仍按 `--copy-unprocessed` 处理（复制而非压缩） |
| `--video-config <文件>` | 脚本旁的 `media-compress.json` | 换成另一个 HandBrake 预设 JSON |
| `--video-preset <名字>` | 该文件里第一个预设 | 从多预设文件里挑一个（**区分大小写**） |
| `--image-quality <0-100>` | `82` | 图像质量，越大越清晰 |
| `--image-format <格式>` | `original` | 图像输出格式：`original`/`jpeg`/`png`/`gif`/`webp`/`tiff` |
| `--image-strip-exif` | 关 | 去掉图像的 EXIF（含 GPS 等隐私信息）；默认保留 |
| `--image-max-edge <像素>` | `5120` | 图像最长边上限，超出才缩；`0` 表示不限制 |
| `--image-jobs <n>` | `3` | 图像并发数；`1` 为串行 |
| `--audio-codec <格式>` | `mp3` | 音乐输出格式：`mp3`/`flac`/`opus`/`aac` |
| `--audio-bitrate <码率>` | `192k` | 仅对有损格式生效（`flac` 忽略）：`128k`/`192k`/`256k`/`320k` |
| `--copy-unprocessed <yes\|no>` | `yes` | 把未压缩的文件原样复制进输出目录；`no` 则不复制 |
| `--dry-run` | 关 | 只打印将执行的命令，**零写入**（连日志和输出目录都不建） |
| `--log [no\|路径]` | `auto` | 默认在输出根写 `media-compress-<时间戳>.log`；`no` 关闭；给路径则写到那里 |

```bash
media-compress ./media                                  # 输出到 ./media/_compressed/
media-compress ./pics --only image --image-quality 70   # 只压图，质量 70
media-compress ./pics --image-format webp               # 图像统一转 webp
media-compress ./pics --image-strip-exif                # 顺带清掉 GPS 等 EXIF 信息
media-compress ./pics --image-max-edge 1920             # 最长边限制到 1920
media-compress ./pics --image-max-edge 0                # 完全不缩放
media-compress ./pics --image-jobs 4                    # 图像开 4 并发
media-compress ./music --only audio                     # 只压音乐
media-compress ./music --audio-codec flac               # 无损压缩（音质零损失）
media-compress ./music --audio-bitrate 128k             # 更省体积
media-compress ./media --copy-unprocessed no            # 只要压缩产物，不复制其余文件
media-compress ./media --log no                         # 不写日志
media-compress ./media --log D:\logs\run.log            # 写到指定文件（追加）
media-compress ./media --video-preset 1080p-h265        # 用内置配置里的另一个预设
media-compress ./media --video-config D:\my-presets.json  # 换成自己的预设文件
media-compress ./media --dry-run                        # 先看清楚会执行什么
```

`--image-format` 只换容器、不换画质（画质看 `--image-quality`），输出的扩展名会自动
跟着变（如 `<名字>.webp`）。指定与源相同的格式也没问题，等于 `original`。

**省不到时保留原件**：转 webp/mp3 若压不动（源本身已压得很紧，转出来反而更大），
脚本复制原文件。扩展名会说谎时（`poster.webp` 里装着 JPEG、`song.mp3` 里装着 FLAC）
加 `.orig` 后缀；扩展名本来就没说错时保持原名：

```
poster.webp.orig    ← 转 webp 没省到，内容仍是 JPEG
song.mp3.orig       ← 转 mp3 没省到，内容仍是 FLAC
modern.mp4          ← 现代编码跳过，本来就是这个格式，不加后缀
note.txt            ← 非媒体文件，原样复制
```

**输出名冲突时自动加序号**：两个源争同一个输出名（同目录的 `song.mp3` 与
`song.flac` 在 `--audio-codec mp3` 下都想叫 `song.mp3`）时，先到者保留原名，后到者
变成 `song-2.mp3`。**任何情况下都不会覆盖文件**，也不会因为撞名而丢文件。

## 压缩音乐

只处理**独立音频文件**（不是视频里的音轨）。规则很简单：**除了已经是目标格式的，全都转**。

| 源格式 | `--audio-codec mp3` | `flac` | `opus` | `aac` |
|---|---|---|---|---|
| `mp3` | 重编 | 转 | 转 | 转 |
| `flac` | 转 | 复制 | 转 | 转 |
| `wav`/`alac`/`ape`/`wv`/`aiff` | 转 | 转 | 转 | 转 |
| `m4a`/`aac` | 转 | 转 | 转 | 复制 |
| `ogg`/`opus` | 转 | 转 | 复制 | 转 |

「复制」只发生在源**已经是目标格式**时——同编码器重转一遍收益接近零（`flac→flac`
实测省 0%），有损的同格式重转更是白掉一次音质。

所以 `--audio-codec opus --audio-bitrate 128k` 会把 mp3 库整体转成 opus（320k mp3
→ 128k opus 实测**省 53%**）。

**重编码只在"往下压"时才有意义**：`mp3 320k → 128k` 省约 60%，而 `320k → 320k` 省 0%、
`128k → 192k` 反而更大——后两种都是白白再掉一次音质。脚本的"省不到 10% 就保留原文件"
规则会自动挡住它们（保留的文件加 `.orig`），所以不必自己判断源码率。

**跨有损格式转换会再损失一次音质**（mp3 → opus 属于二次有损编码）。要避免就选同一个
格式：`--audio-codec mp3` 处理 mp3 库属于同格式调码率，损失最小。

**标签和封面会保住**（`title`/`artist`/`album`/`track` + 内嵌封面），转换后还会校验
是否丢失，丢了就判定失败并保留原文件。**例外**：`opus`（Ogg 容器）装不下内嵌封面，
选它时封面不会被嵌入，需要的话把封面图单独放在同一目录（脚本会照常复制它）。

**mp3 的两个硬限制**：装不下多声道（5.1 会下混成立体声）、采样率上限 48 kHz
（更高会被重采样）。两者都不可逆，但脚本会照转并在日志里写明。

补充：

- 百分比是**体积缩减量**，基数取源文件：`-64%` 表示新大小是原来的 36%
- `TOTAL` 的 `total A -> B` 是本次处理文件的进出总量（`B = A - saved`）；已存在的
  输出不在其中，其数量显示在头部行的 `[n skipped beforehand]`
- 头部第一个数字 `COPY` 是"不压缩、只复制"的文件数（如 `.avif`、`.tif`、`.bmp`）


## 配置与预设

视频参数全部来自预设 JSON（默认是脚本旁的 `media-compress.json`，用 `--video-config`
换），脚本不提供任何视频参数开关。**图像和音频参数不走这里**，它们只看命令行
（`--image-*` / `--audio-*`）——三者没有交叠，所以不存在谁覆盖谁的问题。

**优先级**：命令行 > 配置文件 > 内置默认。

### 内置的 4 个预设

配置文件里按**质量从低到高**排列，所以默认（不传 `--video-preset`）用第一个 `480p-h265`：

| `--video-preset` | 编码器 | 画质 | 分辨率 | 速度档 |
|---|---|---|---|---|
| `480p-h265`（默认，第一个） | `nvenc_h265` | 38 | 720×480 | fastest |
| `720p-h265` | `nvenc_h265` | 22 | 1280×720 | slowest |
| `720p-h264` | `nvenc_h264` | 22 | 1280×720 | medium |
| `1080p-h265` | `nvenc_h265` | 22 | 1920×1080 | medium |

不传 `--video-preset` 时用文件里**第一个**预设，想换默认就调整文件里的顺序。名字**区分
大小写**——HandBrake 就是敏感的，写错会被直接拒绝并列出可用名字。

### 换成自己的预设

1. 打开 HandBrake GUI，调好分辨率、编码器、质量、音频、字幕
2. **Presets → Add New Preset** 保存并命名（可以建多个，甚至放进文件夹）
3. 右键 → **Export** → 导出 JSON
4. 用 `--video-config <该文件>` 指过去，用 `--video-preset <名字>` 挑其中一个

也可以直接覆盖脚本旁的 `media-compress.json` 当默认值。预设文件支持 HandBrake 的
**多层结构**（预设放在文件夹的 `ChildrenArray` 里也认得）。

### 常用字段

| 字段 | 含义 |
|---|---|
| `PresetName` | 预设名，`--video-preset` 就是匹配它 |
| `VideoEncoder` | 编码器，改这里就是改硬编/软编 |
| `VideoQualitySlider` | 画质（`VideoQualityType: 2` 时数值越小越清晰、体积越大） |
| `VideoPreset` | 编码速度档，越慢同画质体积越小 |
| `PictureWidth` / `PictureHeight` | 输出尺寸上限，配 `PictureAllowUpscaling: false` 即不放大 |
| `AudioList` | 音轨编码与码率 |
| `FileFormat` | 容器，决定输出扩展名（`av_mp4` → `.mp4`、`av_mkv` → `.mkv`） |
| `Optimize` | MP4 faststart |
| `SubtitleTrackSelectionBehavior` | 字幕轨取舍，见下 |

## HandBrake 参数说明

### 编码器

`VideoEncoder` 可填：

- `nvenc_h264` / `nvenc_h265` / `nvenc_av1` — NVIDIA 硬件编码，最快
- `qsv_h264` / `qsv_h265` — Intel 核显硬件编码
- `x264` / `x265` — CPU 软编，同体积画质最好，最慢
- `svt_av1` / `VP9` — 更高压缩率，兼容性略差

### 画质与分辨率

- `VideoQualitySlider` — 画质。`VideoQualityType: 2`（恒定质量）时**数值越小越清晰、体积越大**
- `VideoPreset` — 编码速度档（`ultrafast` … `veryslow`）。越慢同画质体积越小
- `PictureWidth` / `PictureHeight` — 输出尺寸上限，配 `PictureAllowUpscaling: false` 即不放大
- `VideoAvgBitrate` — 仅 `VideoQualityType: 1`（平均码率）时生效

### 字幕

`SubtitleTrackSelectionBehavior` 决定保留哪些字幕轨：

| 取值 | 结果 |
|---|---|
| `"none"` | **不保留任何字幕轨** |
| `"first"` | 只保留第一条 |
| `"all"` | 保留全部字幕轨 |

相关字段：`SubtitleLanguageList`（语言白名单，`[]` 为不限）、`SubtitleBurnBehavior`
（是否把字幕烧进画面，烧录不可逆）、`SubtitleAddForeignAudioSearch`。

> 填错值不会报错，会被静默当作 `none` 处理——改完建议先用带字幕的样片转一遍确认。

## 注意事项

- 图像是有损压缩（`--image-quality` 越大越清晰）
- `--image-max-edge` **只在源超出上限时才缩，永不放大**；缩放与压缩在同一次编码里
  完成，不会二次有损。常用取值：`1920`（1080p 屏）、`2560`、`3840`（4K）、
  `5120`（5K，默认）、`6144`、`7680`、`8192`、`0`（不限）
- 压不动的图像、已高效的视频、caesiumclt 读不了的格式，默认都会原样复制进输出目录
  （`[COPY]`），所以输出目录不会缺文件
- **非媒体文件也会原样复制**（`.txt`/`.srt`/`.nfo`/`.md` 等等一切其他文件），
  因为输出目录要能整体替代源目录；只有 `Thumbs.db`/`desktop.ini`/`.DS_Store`
  这类系统垃圾会被有意丢弃
- `.tif/.tiff/.bmp` 和 `.avif/.heic/.heif/.jxl` 不会被压缩，只会原样复制
- `--image-strip-exif` 保留方向标签，所以带 EXIF 旋转的照片不会躺倒
- 省得不够的视频每次运行都会重算一遍（脚本不记状态），但它会被复制，不影响完整性
- 视频字幕丢不丢完全看预设的 `SubtitleTrackSelectionBehavior`
- `_compressed/` 里已有同名非空文件即跳过；想重压某个文件，删掉它的输出再跑
- 压缩图像时，输出目录根部会短暂出现一个 `.media-compress-tmp-<pid>/`，跑完自动删除；
  跳过和 `--dry-run` 都不会创建它。若进程被强杀留下，下次运行会自动清掉过期目录
- HDR 视频、已是 `hevc/av1/vp9/vp8` 且码率不高的视频属于故意不动，不是失败，
  也不会让退出码变成 1
- 退出码：`0` 成功或跳过 / `1` 有失败或工具缺失 / `2` 参数错误
