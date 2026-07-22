# batch_encode.py — HandBrake 批量转码脚本

## 功能

- 递归扫描源目录下所有 `.mkv` 文件
- 调用 HandBrakeCLI 使用自定义预设 + NVIDIA NVENC 硬件编码转码为 `.mp4`
- 保持源目录的子目录结构输出
- 先输出到 `.tmp` 临时文件，转换成功后再重命名为 `.mp4`，避免中断产生残缺文件
- 已存在的输出文件自动跳过，支持断点续传
- 遇到错误立即终止，不继续处理后续文件

## 使用前准备

### 1. 安装 HandBrake

- 本体：[https://handbrake.fr/downloads.php](https://handbrake.fr/downloads.php)
- CLI：[https://handbrake.fr/downloads2.php](https://handbrake.fr/downloads2.php)

下载 CLI 后将 `HandBrakeCLI.exe` 放到本体安装目录下（如 `D:\Program Files\HandBrake\`）。

### 2. 导出预设

1. 打开 HandBrake GUI
2. 配置好你想要的参数（分辨率、码率、滤镜等）
3. 点击 **Presets → Add New Preset** 保存为预设（如 `720p-h264`）
4. 右键该预设 → **Export** → 导出为 JSON 文件

### 3. 修改配置

编辑 `batch_encode.py` 顶部的配置区域：

| 变量 | 说明 |
|---|---|
| `SOURCE_DIR` | 源目录，会递归扫描其下所有 mkv |
| `OUTPUT_DIR` | 输出目录 |
| `HANDBRAKE_CLI` | HandBrakeCLI.exe 路径 |
| `PRESET_JSON_PATH` | 上一步导出的预设 JSON 文件路径 |

### 4. 运行

```bash
python batch_encode.py
```

## 编码器

默认使用 `nvenc_h264`（NVIDIA NVENC H.264 硬件编码）。如需修改，调整 `--encoder` 参数，或修改 json 中的`VideoEncoder` 配置：

- `nvenc_h264` — H.264（兼容性最好）
- `nvenc_h265` — H.265/HEVC（更高压缩率）
- `nvenc_h265_10bit` — 10-bit H.265（更高画质）
- `x264` — CPU 软件编码

## 注意事项

- 首次运行前先在 HandBrake GUI 中测试预设是否正常
- 确保磁盘空间充足（临时文件和最终文件同时存在）
- 强制中断后，`.tmp` 残留文件会在下次启动时自动清理
