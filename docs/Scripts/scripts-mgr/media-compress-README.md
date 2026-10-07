# media-compress — 图像 / 视频批量压缩

## 功能

- 图像走 **caesiumclt**，视频走 **HandBrakeCLI**，按扩展名自动分流，互不干扰
- 三个工具路径**自动查找**，无需配置；找不到只在真正要处理该类媒体时才报错
- 输出到各自的 `<源目录>/_compressed/`，镜像源目录结构，**原文件始终不动**
- 图像压不动时**原样复制**到输出目录，保证输出目录不缺图
- 不写日志、不写台账、不加锁，唯一产物就是压缩后的文件本身

## 参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `<文件或目录...>` | 必填 | 可多个，目录会递归扫描 |
| `-o, --output <目录>` | 各自的 `_compressed/` | 所有输入共用一个输出目录 |
| `--only image\|video` | 全部 | 只处理一类媒体 |
| `--image-quality <0-100>` | `82` | 图像质量，越大越清晰 |
| `--image-format <格式>` | `original` | 图像输出格式：`original`/`jpeg`/`png`/`gif`/`webp`/`tiff` |
| `--image-strip-exif` | 关 | 去掉图像的 EXIF（含 GPS 等隐私信息）；默认保留 |
| `--dry-run` | 关 | 只打印将执行的命令，零写入 |

```bash
media-compress ./media                                  # 输出到 ./media/_compressed/
media-compress ./pics --only image --image-quality 70   # 只压图，质量 70
media-compress ./pics --image-format webp               # 图像转 webp（扩展名自动跟着变）
media-compress ./pics --image-strip-exif                # 顺带清掉 GPS 等 EXIF 信息
media-compress ./media --dry-run                        # 先看清楚会执行什么
```

`--image-format` 只换容器、不换画质（画质看 `--image-quality`）。转成 webp 后输出是
`<名字>.webp`，下次运行能识别出"已经压过"；想额外再要一份 jpg 的，去掉该参数重跑即可。

工具找错了可以用环境变量覆盖：`CAESIUM_CLT`、`HANDBRAKE_CLI`、`FFPROBE`。

## 输出格式

全部为英文，逐文件一行，格式固定，方便 `grep` / `awk` 解析：

```
IMAGE 4 / VIDEO 1  (preset 480p-h265, container .mp4)
[1/5] [IMAGE] <源路径>
[1/5] [IMAGE] [OK] -64%  183.8 KB -> 66.8 KB  <输出路径>
[4/5] [IMAGE] [COPY] not worth compressing, copied as is  <输出路径>
[5/5] [VIDEO] [FAIL] audio tracks 2 != source 1  <源路径>
TOTAL 5  OK 4  SKIP 1  COPY 1  FAIL 0  saved 10.0 MB
```

状态词只有四个：

| 状态 | 含义 |
|---|---|
| `[OK]` | 已压缩，输出文件存在 |
| `[SKIP]` | 未处理、输出目录里**没有**对应文件 |
| `[COPY]` | 未压缩但**已原样复制**，输出目录里有该文件 |
| `[FAIL]` | 出错，原因跟在后面 |

要点：

- `[SKIP]` 与 `[COPY]` 必须分开看——前者输出目录里缺图，后者不缺
- 百分比是**体积缩减量**，基数取源文件：`-64%` 表示新大小是原来的 36%
- `[1/5]` 的序号只发给**实际待办**的文件；被"已存在"等过滤掉的不占号，所以
  分母与 `TOTAL` 一致
- 分类行 `TOTAL` 的 `SKIP` 与 `COPY` 会同时 +1（同一个文件既跳过又复制），
  因此 `OK + SKIP + COPY + FAIL` 可能大于 `TOTAL`

## 下载工具

- caesiumclt：<https://github.com/Lymphatus/caesium-clt>
- HandBrakeCLI：<https://handbrake.fr/downloads2.php>，放进 HandBrake 安装目录
- ffprobe：随 <https://ffmpeg.org/download.html> 提供，仅用于校验转码结果

三者都在 PATH 里最省事；HandBrake 装在非系统盘也能被找到（会遍历各盘符的 `Program Files\HandBrake`）。

## 配置与预设导出

视频参数全部来自脚本旁的 `media-compress.json`，脚本不提供任何视频参数开关。

1. 打开 HandBrake GUI，调好分辨率、编码器、质量、音频、字幕
2. **Presets → Add New Preset** 保存并命名
3. 右键该预设 → **Export** → 导出 JSON，覆盖脚本旁的 `media-compress.json`
4. 预设名由脚本从 JSON 的 `PresetList[0].PresetName` 自动读出，不必同步改脚本

常用字段：

| 字段 | 含义 |
|---|---|
| `VideoEncoder` | 编码器，改这里就是改硬编/软编 |
| `VideoQualitySlider` | 画质（`VideoQualityType: 2` 时为恒定质量，数值越小越清晰、体积越大） |
| `VideoPreset` | 编码速度档，越慢同画质体积越小 |
| `PictureWidth` / `PictureHeight` | 输出上限，配 `PictureAllowUpscaling: false` 即不放大 |
| `AudioList` | 音轨编码与码率 |
| `FileFormat` | 容器，决定输出扩展名（`av_mp4` → `.mp4`） |
| `Optimize` | MP4 faststart |
| `SubtitleTrackSelectionBehavior` | 字幕轨取舍，见下节 |

## HandBrake 参数说明

预设 JSON 就是 HandBrake 自己的导出格式，字段名与 GUI 一一对应。除了用 GUI 导出，
也可以直接改字段；脚本不做任何校验，**改错了 HandBrake 通常不会报错，而是静默按默认值处理**。

### 编码器

`VideoEncoder` 可填（实测本机可选）：

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

`SubtitleTrackSelectionBehavior` 决定保留哪些字幕轨，实测（源 2 条字幕）：

| 取值 | 结果 |
|---|---|
| `"none"` | **不保留任何字幕轨** |
| `"first"` | 只保留第一条 |
| `"all"` | 保留全部字幕轨 |

相关字段：

- `SubtitleLanguageList` — 语言白名单，`[]` 表示不限语言
- `SubtitleBurnBehavior` — 是否把字幕**烧进画面**（`foreign`/`none`/`all`）。烧录不可逆
- `SubtitleAddForeignAudioSearch` — 自动搜索外语片段字幕

> 注意：非法取值会被静默回退成 `none`，且**不报错、不警告**——一个字母打错就等于字幕全丢。
> 改完建议先用带字幕的样片转一遍确认。

## 注意事项

- 图像是有损压缩（`--image-quality` 越大越清晰）
- 图像若压不动（省不到 5%），**会把原图原样复制**到输出目录，保证输出目录不缺图；
  这类显示为 `[COPY]`，不计入节省量
- `--image-strip-exif` 保留方向标签，所以带 EXIF 旋转的照片不会躺倒
- 视频若转码后**省不到 5%**，脚本丢弃结果、保留原文件，显示 `[SKIP]`（**不复制**）
- 省得不够的视频**每次运行都会重算一遍**——没有状态文件可作标记，这是不写台账的代价
- 视频字幕丢不丢**完全看预设**的 `SubtitleTrackSelectionBehavior`，脚本只按 JSON 执行
- `_compressed/` 里已有同名非空文件即跳过；想重压某个文件，删掉它的输出再跑
- 图像压缩时会在输出目录里临时生成 `.<文件名>.mc-tmp/`（caesiumclt 只能输出到目录），
  压缩完立即删除；`--dry-run`、跳过、失败都不会留下它
- HDR 视频、已是 `hevc/av1/vp9/vp8` 且码率不高的视频、动画 WebP/GIF 会显示 `[SKIP]`，
  这类是**故意不动**，不是失败，也不会让退出码变成 1
- `.avif/.heic/.heif/.jxl` 不处理（caesiumclt 1.5.0 读不了）
- 退出码：`0` 成功或跳过 / `1` 有失败或工具缺失 / `2` 参数错误
