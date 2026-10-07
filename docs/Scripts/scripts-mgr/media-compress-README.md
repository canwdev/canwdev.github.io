# media-compress — 图像 / 视频 / 音频批量压缩

## 功能

- 图像走 **caesiumclt**，视频走 **HandBrakeCLI**，音频走 **ffmpeg**；按扩展名自动分流，
  互不干扰
- 工具路径**自动查找**，无需配置
- 输出到各自的 `<源目录>/_compressed/`，镜像源目录结构，**原文件始终不动**
- 未压缩的文件默认**原样复制**进输出目录，所以输出目录可以替代源目录
- 在输出目录写一份带完整命令行的日志，可用 `--log no` 关闭

## 下载工具

- caesiumclt：<https://github.com/Lymphatus/caesium-clt>，处理图像
- HandBrakeCLI：<https://handbrake.fr/downloads2.php>，处理视频，放进 HandBrake 安装目录
- ffmpeg / ffprobe：随 <https://ffmpeg.org/download.html> 提供，处理音频

都在 PATH 里最省事；HandBrake 装在非系统盘也能被找到。找不到或找错了，可以用
环境变量直接指定：`CAESIUM_CLT`、`HANDBRAKE_CLI`、`FFMPEG`、`FFPROBE`。

只处理某一类媒体时，不会去查找另一类工具——所以只压音频的机器上不需要装 HandBrake。

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
| `--audio-codec <格式>` | `mp3` | 音频输出格式：`mp3`/`flac`/`opus`/`aac` |
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
media-compress ./music --audio-codec opus --audio-bitrate 128k   # 体积最小
media-compress ./music --audio-codec flac               # 无损压缩
media-compress ./media --copy-unprocessed no            # 只要压缩产物，不复制其余文件
media-compress ./media --log no                         # 不写日志
media-compress ./media --log D:\logs\run.log            # 写到指定文件（追加）
media-compress ./media --video-preset 1080p-h265        # 用内置配置里的另一个预设
media-compress ./media --video-config D:\my-presets.json  # 换成自己的预设文件
media-compress ./media --dry-run                        # 先看清楚会执行什么
```

`--image-format` 只换容器、不换画质（画质看 `--image-quality`），输出的扩展名会自动
跟着变（如 `<名字>.webp`）。指定与源相同的格式也没问题，等于 `original`。

## 输出命名

默认用最简名：`a.png` 转 webp 得到 `a.webp`。**只有当这个名字和别的文件撞上时，才把
源扩展名也写进文件名**（`a.jpg` 与 `a.png` 同时转 webp → 两者分别得到 `a.jpg.webp`
和 `a.png.webp`）。扩展名本来就相符时（`--image-format original`、现代编码跳过的视频、
非媒体文件）不加任何后缀，保持 `a.webp`、`a.txt`、`a.mp4` 这样的原名。

这样命名有两个好处：

- **扩展名始终诚实**：名字的最后一段就是实际格式。压不动而保留原件的文件仍是源名
  （`a.flac` 里装的就是 flac），不会出现"叫 `.mp3` 其实是 flac"的情况。
- **一个源对应一个输出名，且互不冲突**：撞名时两边都会带上源扩展名，所以**正常情况
  不会出现带序号的文件名**。

```
photo.png   --转 webp 成功-->   photo.webp         （无冲突，用最简名）
clip.wav    --转 mp3 成功-->    clip.mp3
tight.webp  --压不动，保留-->   tight.webp         （内容就是 webp）
album.flac  --转 mp3 没省到-->  album.flac         （内容就是 flac）
sub\v.mp4   --现代编码跳过-->   sub\v.mp4
note.txt    --原样复制-->       note.txt
```

只有同 stem 的多个源会争同一个最简名，这时**两边都加源扩展名限定**：

```
a.png + a.webp   --都转 webp-->   a.png.webp   和  a.webp
s.flac + s.wav   --都转 mp3 -->   s.flac.mp3   和  s.wav.mp3
```

（上例第二个的 `a.webp` 没加限定，是因为 `a.png` 限定后叫 `a.png.webp`，已经和它分开了。）

`s.flac` 与 `s.wav` 若**单独**存在、没有同名的兄弟文件，就都用最简名 `s.mp3`。

**注意限定的是"产出名"**：压不动而保留原件时，落脚名仍是源本名（`s.flac`），因为那才是
内容的真实格式。所以同一个 `s.flac` 可能产出 `s.flac.mp3`（转换成功）或 `s.flac`（保留
原件），取决于压了划不划算。

**什么时候会出现 `-2` 这样的序号**：两个源严格同名（同一个目录里不可能），或者输出
目录里已经存在同名文件。都属异常，正常流程不会遇到。**任何情况下都不会覆盖文件**。

**同格式调码率时名字不变**：`--audio-codec mp3 --audio-bitrate 128k` 处理 320k 的
`c.mp3`，输出仍叫 `c.mp3`（扩展名本来就对，不需要双后缀）。所以改码率后重跑时，
输出目录里已有同名文件、脚本会跳过它；想按新码率重新压，先删掉那个输出文件。

## 压缩音乐

处理的是**独立音频文件**，不是视频里的音轨（视频的音频由预设决定，见下）。

规则：**除了已经是目标格式的，全都转**；同格式的文件只有在你**显式改了码率**时才重编。

| 源格式 | `--audio-codec mp3` | `flac` | `opus` | `aac` |
|---|---|---|---|---|
| `mp3` | 见下¹ | 转 | 转 | 转 |
| `flac` | 转 | 复制 | 转 | 转 |
| `wav`/`alac`/`ape`/`wv`/`aiff` | 转 | 转 | 转 | 转 |
| `m4a`/`aac` | 转 | 转 | 转 | 复制 |
| `ogg`/`opus` | 转 | 转 | 复制 | 转 |

¹ **同格式调码率**：`--audio-bitrate` 与默认值（`192k`）**不同**时，同格式的文件也会
重编——所以 `--audio-codec mp3 --audio-bitrate 128k` 能把 320k 的 mp3 压到 128k
（省一半左右）。用默认码率时不重编，避免白跑一趟还没收益。无损格式（`flac`）忽略码率，
所以同格式一律复制。

**压了也不会省的，直接跳过**：源与目标**编码器相同**、且目标码率没有明显低于源码率时，
脚本在启动编码器**之前**就放弃，不会白跑一遍：

```
note: source is already mp3 @ 286k, target 320k would not be smaller — skipping re-encode
[1/4] [AUDIO] [COPY] bitrate_not_worth_it, copied as is  <输出路径>
```

这很重要，因为音频编码很慢：单线程、约 0.4% 实时速度（**5 小时的音频要 65 秒**，
且用不上多核）。提前判断只花二十几毫秒，能把这类白跑的时间全省掉。

判断带容差，因为 VBR 文件报告的只是**平均**码率，同一档位不同内容的差距可能很大。
跨编码器时不做这个比较——opus 128k 的信息量约等于 mp3 256k，数字接近没有可比性。

「复制」的另两种情况是源已经是目标格式且没有调码率、或者转出来省不到
（见《输出命名》，保留原文件时仍用源名）。

### 选哪个格式

| 格式 | 适合 | 注意 |
|---|---|---|
| `mp3` | 通用性最好，什么设备都能放 | 效率最低，同体积下音质最差 |
| `opus` | **体积最小**，128k 已接近透明 | 装不下封面；老设备、部分车机放不了 |
| `aac` | 兼容性好（`.m4a`），可内嵌封面 | 效率介于两者之间 |
| `flac` | **无损**，只压未压缩源（如 wav） | 对已是 flac 的源没有收益 |

### 几个要知道的点

- **有损转有损会再损失一次音质**（mp3 → opus 属于二次编码）。想损失最小就在同一格式里
  调码率：`--audio-codec mp3` 处理 mp3 库。
- **往下压才有收益**：`mp3 320k → 128k` 能省一半左右，而源码率已经不高时再压可能省不到
  ——这时脚本会保留原文件，不会白白掉一次音质。
- **标签会保住**：`title`/`artist`/`album`/`track`/内嵌歌词等都会跟着走。
- **封面**：`mp3`/`aac`/`flac` 能内嵌封面（会保留）；**`opus` 不能**，选它时封面不会
  进入音频文件。封面图本身如果是独立文件，会照常被复制到输出目录。
- **`mp3` 不支持多声道和 48 kHz 以上采样率**：5.1 会被下混成立体声，96/192 kHz 会被
  重采样。两者都不可逆，脚本会照转并在日志里写明。

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

### 视频的音轨

视频里的音频由预设的 `AudioList` 决定，`--audio-*` 参数**不影响**它。默认 4 个预设都是
`av_aac` 160kbps 立体声，即**5.1 会被下混成立体声**；想保留环绕声，改预设里的
`AudioList`（编码器、码率）与 `AudioMixdown`。

## 注意事项

- 图像和音频的转码都是**有损**的（无损源转 `flac` 除外）
- `--image-max-edge` **只在源超出上限时才缩，永不放大**；缩放与压缩在同一次编码里
  完成，不会二次有损。常用取值：`1920`（1080p 屏）、`2560`、`3840`（4K）、
  `5120`（5K，默认）、`6144`、`7680`、`8192`、`0`（不限）
- **输出目录始终是完整的**：压不动的、已高效的、不支持的格式、以及一切非媒体文件
  （`.txt`/`.srt`/`.nfo`/`.md`…）默认都会原样复制进去。只有 `Thumbs.db`/
  `desktop.ini`/`.DS_Store` 这类系统垃圾会被有意丢弃。用 `--copy-unprocessed no`
  时输出目录**不完整**，只能用来取产物
- `.tif/.tiff/.bmp` 和 `.avif/.heic/.heif/.jxl` 图像不会被压缩，只会原样复制
- `--image-strip-exif` 保留方向标签，所以带 EXIF 旋转的照片不会躺倒
- **独立的字幕文件**（`.ass`/`.srt`/`.ssa`/`.vtt`/`.sub`/`.idx`/`.sup`）不会被压缩，
  一律原样复制（连 BOM 都保持），所以外挂字幕不会丢
- **视频里的字幕轨**丢不丢完全看预设的 `SubtitleTrackSelectionBehavior`
- 处理顺序是 **原样复制 → 图像 → 音频 → 视频**（视频最慢，放最后不拖住别的阶段）
- HDR 视频、已是 `hevc/av1/vp9/vp8` 且码率不高的视频属于故意不动，不是失败，
  也不会让退出码变成 1
- 输出目录里已有同名非空文件即跳过；想重压某个文件，删掉它的输出再跑
- **中间产物会自动清理**：编码时会在目标目录里生成 `<名字>-<pid>-<序号>.mctmp` 这类
  临时文件，每个用完即删；如果进程被强杀留下残留，**下次运行开始时会自动清掉**
  （日志会写 `cleaned up N leftover temp file(s)`）。`.mctmp` 是脚本专有后缀，
  你自己的文件（包括 `.tmp`）不会被误删
- `--output` 不能与源目录重叠（等于、在内部、包住它都会被拒绝），否则结果会悄悄出错
- 退出码：`0` 成功或跳过 / `1` 有失败或工具缺失 / `2` 参数错误
