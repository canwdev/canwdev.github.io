# media-compress — 图像 / 视频批量压缩

## 功能

- 图像走 **caesiumclt**，视频走 **HandBrakeCLI**，按扩展名自动分流，互不干扰
- 工具路径**自动查找**，无需配置
- 输出到各自的 `<源目录>/_compressed/`，镜像源目录结构，**原文件始终不动**
- 未压缩的文件默认**原样复制**进输出目录，所以输出目录可以替代源目录
- 不写日志、不写台账、不加锁，产物只有压缩后的文件本身

## 下载工具

- caesiumclt：<https://github.com/Lymphatus/caesium-clt>
- HandBrakeCLI：<https://handbrake.fr/downloads2.php>，放进 HandBrake 安装目录
- ffprobe：随 <https://ffmpeg.org/download.html> 提供，仅用于校验转码结果

三者都在 PATH 里最省事；HandBrake 装在非系统盘也能被找到。找不到或找错了，可以用
环境变量直接指定：`CAESIUM_CLT`、`HANDBRAKE_CLI`、`FFPROBE`。

## 参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `<文件或目录...>` | 必填 | 可多个，目录会递归扫描 |
| `-o, --output <目录>` | 各自的 `_compressed/` | 所有输入共用一个输出目录 |
| `--only image\|video` | 全部 | 只处理一类媒体 |
| `--image-quality <0-100>` | `82` | 图像质量，越大越清晰 |
| `--image-format <格式>` | `original` | 图像输出格式：`original`/`jpeg`/`png`/`gif`/`webp`/`tiff` |
| `--image-strip-exif` | 关 | 去掉图像的 EXIF（含 GPS 等隐私信息）；默认保留 |
| `--image-jobs <n>` | `3` | 图像并发数；`1` 为串行 |
| `--copy-unprocessed <yes\|no>` | `yes` | 把未压缩的文件原样复制进输出目录；`no` 则不复制 |
| `--dry-run` | 关 | 只打印将执行的命令，零写入 |

```bash
media-compress ./media                                  # 输出到 ./media/_compressed/
media-compress ./pics --only image --image-quality 70   # 只压图，质量 70
media-compress ./pics --image-format webp               # 图像统一转 webp
media-compress ./pics --image-strip-exif                # 顺带清掉 GPS 等 EXIF 信息
media-compress ./pics --image-jobs 4                    # 图像开 4 并发
media-compress ./media --copy-unprocessed no            # 只要压缩产物，不复制其余文件
media-compress ./media --dry-run                        # 先看清楚会执行什么
```

`--image-format` 只换容器、不换画质（画质看 `--image-quality`），输出的扩展名会自动
跟着变（如 `<名字>.webp`）。指定与源相同的格式也没问题，等于 `original`。

## 用作"压完替换原目录"

典型用途是**压缩资源后抽查，无误就直接删掉原文件夹**。判定依据是最后一行：

```
2026-10-07 11:44:23 output tree complete for 4 file(s); the source folder can be replaced by the output tree
```

看到这一行，说明输出目录里每个源文件都有对应物。反之会打印警告并列出缺口：

```
2026-10-07 11:44:23 WARNING: 3 file(s) are NOT in the output tree; do NOT delete the source folder:
2026-10-07 11:44:23   [IMAGE] not_smaller  ...\tiny.jpg
2026-10-07 11:44:23   [VIDEO] modern_codec  ...\sub\modern.mp4
```

用 `--copy-unprocessed no` 时输出目录**必然不完整**（头部行会写明），此时它只能用来
取压缩产物，**不能用来替换原目录**。

## 输出格式

全部为英文，每行以本地时间戳开头（`YYYY-MM-DD HH:MM:SS`，可排序、可切分）：

```
2026-10-07 11:44:23 IMAGE 4 / VIDEO 1 / COPY 1  (preset 480p-h265, container .mp4)
2026-10-07 11:44:23 [1/6] [IMAGE] <源路径>
2026-10-07 11:44:23 [1/6] [IMAGE] [OK] -64%  183.8 KB -> 66.8 KB  <输出路径>
2026-10-07 11:44:23 [4/6] [IMAGE] [COPY] not worth compressing, copied as is  <输出路径>
2026-10-07 11:44:23 [6/6] [COPY] [COPY] unsupported format, copied as is  <输出路径>
2026-10-07 11:44:23 TOTAL 6  OK 4  SKIP 0  COPY 2  FAIL 0  total 9.3 MB -> 643.4 KB  saved 8.6 MB  (93%)
2026-10-07 11:44:23 output tree complete for 6 file(s); the source folder can be replaced by the output tree
```

状态词只有四个：

| 状态 | 含义 |
|---|---|
| `[OK]` | 已压缩，输出文件存在 |
| `[COPY]` | 未压缩但**已在输出目录**（原样复制） |
| `[SKIP]` | **输出目录里没有这个文件 —— 缺口，不可删原目录** |
| `[FAIL]` | 出错，原因跟在后面 |

补充：

- 百分比是**体积缩减量**，基数取源文件：`-64%` 表示新大小是原来的 36%
- `TOTAL` 的 `total A -> B` 是本次处理文件的进出总量（`B = A - saved`）；已存在的
  输出不在其中，其数量显示在头部行的 `[n skipped beforehand]`
- 头部第一个数字 `COPY` 是"不压缩、只复制"的文件数（如 `.avif`、`.tif`、`.bmp`）


## 配置与预设导出

视频参数全部来自脚本旁的 `media-compress.json`，脚本不提供任何视频参数开关。

1. 打开 HandBrake GUI，调好分辨率、编码器、质量、音频、字幕
2. **Presets → Add New Preset** 保存并命名
3. 右键该预设 → **Export** → 导出 JSON，覆盖脚本旁的 `media-compress.json`
4. 预设名由脚本自动读出，不必同步改脚本

也可以直接编辑该 JSON 的字段（字段名与 HandBrake GUI 一一对应），常用的是：

| 字段 | 含义 |
|---|---|
| `VideoEncoder` | 编码器，改这里就是改硬编/软编 |
| `VideoQualitySlider` | 画质（`VideoQualityType: 2` 时数值越小越清晰、体积越大） |
| `VideoPreset` | 编码速度档，越慢同画质体积越小 |
| `PictureWidth` / `PictureHeight` | 输出尺寸上限，配 `PictureAllowUpscaling: false` 即不放大 |
| `AudioList` | 音轨编码与码率 |
| `FileFormat` | 容器，决定输出扩展名（`av_mp4` → `.mp4`） |
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
- 压不动的图像、已高效的视频、caesiumclt 读不了的格式，默认都会原样复制进输出目录
  （`[COPY]`），所以输出目录不会缺文件
- `.tif/.tiff/.bmp` 和 `.avif/.heic/.heif/.jxl` 不会被压缩，只会原样复制
- `--image-strip-exif` 保留方向标签，所以带 EXIF 旋转的照片不会躺倒
- 省得不够的视频每次运行都会重算一遍（脚本不记状态），但它会被复制，不影响完整性
- 视频字幕丢不丢完全看预设的 `SubtitleTrackSelectionBehavior`
- `_compressed/` 里已有同名非空文件即跳过；想重压某个文件，删掉它的输出再跑
- 压缩图像时输出目录里会有临时目录，压缩完立即删除（跳过和 `--dry-run` 都不会产生）
- HDR 视频、已是 `hevc/av1/vp9/vp8` 且码率不高的视频属于故意不动，不是失败，
  也不会让退出码变成 1
- 退出码：`0` 成功或跳过 / `1` 有失败或工具缺失 / `2` 参数错误
