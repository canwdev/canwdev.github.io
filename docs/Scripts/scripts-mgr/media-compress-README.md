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
| `--image-jobs <n>` | `3` | 图像并发数；`1` 为串行。只作用于图像，视频始终串行 |
| `--copy-unprocessed <yes\|no>` | `yes` | 把未压缩的文件原样复制进输出目录；`no` 则不复制 |
| `--dry-run` | 关 | 只打印将执行的命令，零写入 |

```bash
media-compress ./media                                  # 输出到 ./media/_compressed/
media-compress ./pics --only image --image-quality 70   # 只压图，质量 70
media-compress ./pics --image-format webp               # 图像转 webp（扩展名自动跟着变）
media-compress ./pics --image-strip-exif                # 顺带清掉 GPS 等 EXIF 信息
media-compress ./pics --image-jobs 4                    # 图像开 4 并发
media-compress ./media --copy-unprocessed no            # 只要压缩产物，不复制其余文件
media-compress ./media --dry-run                        # 先看清楚会执行什么
```

`--image-format` 只换容器、不换画质（画质看 `--image-quality`）。转成 webp 后输出是
`<名字>.webp`，下次运行能识别出"已经压过"；想额外再要一份 jpg 的，去掉该参数重跑即可。

**当目标格式与源格式相同时，该参数不会真正下传**（`webp` 源 + `--image-format webp`
等于 `original`）。因为 caesiumclt 拒绝"转成自身格式"，实测 `png→png`、`jpg→jpeg`、
`webp→webp`、`gif→gif` 全部报 `Cannot convert to the same format` 并退化成"压缩失败
后复制"。所以指定与源相同的格式无害，也不会白费压缩机会。

### 并发

**只有图像之间并发，视频始终串行。** 实测 12 张 2000×1500 的 PNG：

| `--image-jobs` | 耗时 | 加速 |
|---|---|---|
| `1`（串行） | 2.63s | 1.00x |
| `3`（默认） | 1.26s | 2.09x |
| `4` | 1.01s | 2.60x |

不要把视频和图像放在一起并发：HandBrake 的管线本身就吃 CPU（软件解码、缩放、色彩
转换、封装），即使 `nvenc_h265` 硬编也一样。实测视频与图像并发时，**视频侧慢 1.8 倍**，
整体比串行还慢。所以脚本固定"图像阶段并发 → 视频阶段串行"。

代价：`--image-jobs` 个 caesiumclt 进程会同时各加载一张图，峰值内存约为单进程的
`--image-jobs` 倍。调很高时留意大图批量。

工具找错了可以用环境变量覆盖：`CAESIUM_CLT`、`HANDBRAKE_CLI`、`FFPROBE`。

## 用作"压完替换原目录"

这个脚本的典型用途是**压缩资源后抽查，无误就直接删掉原文件夹**。默认配置就是为这条
工作流准备的，判定依据是最后一行：

```
output tree complete for 4 file(s); the source folder can be replaced by the output tree
```

看到这一行才说明输出目录里**每个源文件都有对应物**。反之会打印警告并列出缺口：

```
WARNING: 3 file(s) are NOT in the output tree; do NOT delete the source folder:
  [IMAGE] not_smaller  ...\tiny.jpg
  [VIDEO] modern_codec  ...\sub\modern.mp4
  [COPY] unsupported format, not copied  ...\sub\pic.avif
```

**只有这两种情况会造成缺口**，都跟 `--copy-unprocessed` 有关：

| 情况 | 是否复制 | 受 `--copy-unprocessed` 控制 |
|---|---|---|
| 故意跳过（省得不够 / `modern_codec` / `hdr`） | `yes` 时复制 | 是 |
| caesiumclt 读不了的格式（`.avif/.heic/.heif/.jxl/.tif/.tiff/.bmp`） | `yes` 时复制 | 是 |
| **压缩失败**（工具报错 / 校验未通过） | **永远复制** | 否 |
| 路径过长、输出撞名、复制本身失败 | 不复制 | 否（做不到） |

失败文件不受该参数控制是有意的：它直接决定"删原文件夹会不会丢数据"，不该交给开关。

用 `--copy-unprocessed no` 时输出目录**必然不完整**（头部行会写明），此时它只能用来
取压缩产物，**不能用来替换原目录**。

## 输出格式

全部为英文，每行都以本地时间戳开头（`YYYY-MM-DD HH:MM:SS`，可排序、可 `sort`/`awk`
直接切分），逐文件一行，方便 `grep` 解析：

```
2026-10-07 11:44:23 IMAGE 4 / VIDEO 1 / COPY 1  (preset 480p-h265, container .mp4)
2026-10-07 11:44:23 [1/6] [IMAGE] <源路径>
2026-10-07 11:44:23 [1/6] [IMAGE] [OK] -64%  183.8 KB -> 66.8 KB  <输出路径>
2026-10-07 11:44:23 [4/6] [IMAGE] [COPY] not worth compressing, copied as is  <输出路径>
2026-10-07 11:44:23 [6/6] [COPY] [COPY] unsupported format, copied as is  <输出路径>
2026-10-07 11:44:23 TOTAL 6  OK 4  SKIP 0  COPY 2  FAIL 0  total 9.3 MB -> 643.4 KB  saved 8.6 MB  (93%)
2026-10-07 11:44:23 output tree complete for 6 file(s); the source folder can be replaced by the output tree
```

时间戳打在**每一行**上，所以"某个文件什么时候开始/结束"可以直接看出来。`.avif`
之类只复制的文件没有耗时信息，但两头的时间戳能给出区间。

状态词只有四个：

| 状态 | 含义 |
|---|---|
| `[OK]` | 已压缩，输出文件存在 |
| `[COPY]` | 未压缩但**已在输出目录**（原样复制） |
| `[SKIP]` | **输出目录里没有这个文件 —— 缺口，不可删原目录** |
| `[FAIL]` | 出错，原因跟在后面 |

要点：

- `[SKIP]` 现在等同于"缺口"：正常路径下只会看到 `[OK]` 和 `[COPY]`
- 百分比是**体积缩减量**，基数取源文件：`-64%` 表示新大小是原来的 36%
- `TOTAL` 行的 `total A -> B` 是**本次处理文件**的进出总量（`B = A - saved`）；
  被"已存在"预过滤的文件不在其中，其数量显示在头部行的 `[n skipped beforehand]`
- 所有输出都实时 flush，重定向到文件或后台运行时时间戳不会被缓冲拖后

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
- 压不动（省不到 5%）的图像、`modern_codec`/`hdr` 的视频、caesiumclt 读不了的格式，
  默认都会**原样复制**进输出目录（`[COPY]`），保证输出目录不缺文件
- `.tif/.tiff/.bmp` 属于"读不了"那类：caesiumclt 对它们必定报
  `Unable to compute the base path`，所以不会被压缩，只会原样复制。想压这类文件
  得先转成 PNG（实测 2.4 MB TIFF → 191 KB PNG），但那不属于本脚本的职责
- `--image-strip-exif` 保留方向标签，所以带 EXIF 旋转的照片不会躺倒
- 省得不够的视频**省不到就不重压**，但会被复制；每次运行仍会重算一遍——没有状态
  文件可作标记，这是不写台账的代价
- 视频字幕丢不丢**完全看预设**的 `SubtitleTrackSelectionBehavior`，脚本只按 JSON 执行
- `_compressed/` 里已有同名非空文件即跳过；想重压某个文件，删掉它的输出再跑
- 图像压缩时会在输出目录里临时生成 `.<文件名>.mc-tmp/`（caesiumclt 只能输出到目录），
  压缩完立即删除；`--dry-run`、跳过、失败都不会留下它
- HDR 视频、已是 `hevc/av1/vp9/vp8` 且码率不高的视频属于**故意不动**，不是失败，
  也不会让退出码变成 1
- 退出码：`0` 成功或跳过 / `1` 有失败或工具缺失 / `2` 参数错误
