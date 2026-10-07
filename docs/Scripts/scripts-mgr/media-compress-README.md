# media-compress — 图像 / 视频批量压缩

## 功能

- 图像走 **caesiumclt**，视频走 **HandBrakeCLI**，按扩展名自动分流，互不干扰
- 三个工具路径**自动查找**，无需配置；找不到只在真正要处理该类媒体时才报错
- 输出到各自的 `<源目录>/_compressed/`，镜像源目录结构，原文件不动
- `--in-place` 则在 ffprobe 校验通过后用 `os.replace` **原子替换**原文件
- 不写日志、不写台账、不加锁，唯一产物就是压缩后的文件本身

## 参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `<文件或目录...>` | 必填 | 可多个，目录会递归扫描 |
| `-o, --output <目录>` | 各自的 `_compressed/` | 所有输入共用一个输出目录 |
| `--in-place` | 关 | 原子替换原文件；与 `-o` 互斥 |
| `--only image\|video` | 全部 | 只处理一类媒体 |
| `-q, --quality <0-100>` | `82` | **仅图像**；视频画质见配置文件 |
| `--dry-run` | 关 | 只打印将执行的命令，零写入 |
| `-y, --yes` | 关 | 跳过 `--in-place` 的确认提示 |

```bash
media-compress ./media                      # 输出到 ./media/_compressed/
media-compress ./media --in-place -y        # 原地替换
media-compress ./pics --only image -q 70    # 只压图，质量 70
media-compress ./media --dry-run            # 先看清楚会执行什么
```

工具找错了可以用环境变量覆盖：`CAESIUM_CLT`、`HANDBRAKE_CLI`、`FFPROBE`。

## 下载工具

- caesiumclt：<https://github.com/Lymphatus/caesium-clt>
- HandBrakeCLI：<https://handbrake.fr/downloads2.php>，放进 HandBrake 安装目录
- ffprobe：随 <https://ffmpeg.org/download.html> 提供，仅用于校验转码结果

三者都在 PATH 里最省事；HandBrake 装在非系统盘也能被找到（会遍历各盘符的 `Program Files\HandBrake`）。

## 配置与预设导出

视频参数全部来自脚本旁的 `media-compress.json`，脚本不提供任何视频参数开关。

1. 打开 HandBrake GUI，调好分辨率、编码器、质量、音频
2. **Presets → Add New Preset** 保存（例如 `720p-h264`）
3. 右键该预设 → **Export** → 导出 JSON，覆盖脚本旁的 `media-compress.json`
4. `--preset` 名由脚本从 JSON 的 `PresetList[0].PresetName` 自动读出

常用字段：

| 字段 | 含义 |
|---|---|
| `VideoEncoder` | 编码器，改这里就是改硬编/软编 |
| `VideoQualitySlider` | 画质（`VideoQualityType: 2` 时为恒定质量，数值越小越清晰、体积越大） |
| `PictureWidth` / `PictureHeight` | 输出上限，配 `PictureAllowUpscaling: false` 即不放大 |
| `AudioList` | 音轨编码与码率 |
| `FileFormat` | 容器，决定输出扩展名（`av_mp4` → `.mp4`） |
| `Optimize` | MP4 faststart |

## 编码器

`VideoEncoder` 可填（实测本机可选）：

- `nvenc_h264` / `nvenc_h265` / `nvenc_av1` — NVIDIA 硬件编码，最快
- `qsv_h264` / `qsv_h265` — Intel 核显硬件编码
- `x264` / `x265` — CPU 软编，同体积画质最好，最慢
- `svt_av1` / `VP9` — 更高压缩率，兼容性略差

默认预设用的是 `nvenc_h264`。

## 注意事项

- 图像是有损压缩（`-q` 越大越清晰）；`--in-place` 前建议先跑一次不带该参数的
- 视频若转码后**省不到 5%**，脚本丢弃结果、保留原文件，并打印"省得不够"
- 省得不够的视频**每次运行都会重算一遍**——没有状态文件可作标记，这是不写台账的代价
- `_compressed/` 里已有同名非空文件即跳过；想重压某个文件，删掉它的输出再跑
- HDR 视频、已是 `hevc/av1/vp9/vp8` 且码率不高的视频、动画 WebP/GIF 会直接跳过
- `.avif/.heic/.heif/.jxl` 不处理（caesiumclt 1.5.0 读不了）
- 退出码：`0` 成功或跳过 / `1` 有失败或工具缺失 / `2` 参数错误
