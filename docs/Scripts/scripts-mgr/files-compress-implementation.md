# files-compress.py — 实现说明

状态：**已实现并通过实测** —— [`files-compress.py`](files-compress.py) v0.7.0，规则版本（`RULES_VERSION`）2。在 Windows + ffmpeg（n7.x）+ ffprobe + caesiumclt 1.5.0 上，[`tests/`](tests/) 里的验收套件 **96/96 项全部通过**（见 §11）。

v0.3.0 落地了 §16：压缩档位 `--profile balanced|small|tiny`，以及“已压缩即终态”的台账语义（新 reason `already_compressed`）。`RULES_VERSION` 保持 2 —— 策略变化由 `policy` 指纹表达，旧记录按 `balanced` 继承，不需要一次性作废。

v0.4.0 落地了 §5.6：**硬件解码加速**（默认开启，实测输出逐字节不变、4K 源快约 11%），新增 `--no-hwaccel` 与报告里的 `hwaccel` 字段。

v0.5.0 落地了 §5.7：**硬件编码**（`--encoder qsv|qsv-hevc`，opt-in，快约 3–6 倍但同体积画质差约一档；按码率驱动，失败自动回退 x264），编码器进入 `policy` 指纹。

v0.6.0 落地了 §5.5：**删掉总时长上限**（原公式会让长视频误杀，实测 4 分钟视频需 158 秒而旧上限只有 120 秒），改为**卡死看门狗**（`--stall-timeout`，0 = 完全不设时限）；同时修掉一批日志问题（命令行可复制粘贴、结束行带耗时与速度、编码心跳、工具版本独立成行、中断行带计数）。

v0.7.0 落地了 §5.6/§5.7 的健壮性与可诊断性：**硬件失败预算**（单个文件的硬解/硬编失败不再把整轮切到 CPU，连续 3 次才切换）、**探针失败给出 ffmpeg 的原始原因**、**运行头一次列全四条硬件路径**（`硬件探针 d3d11va=True qsv=False encoder_qsv=True encoder_qsv-hevc=True`）。起因是真实使用中出现的"第一个坏文件之后整轮都在软解"。

本文档就是评审时定下的设计，并按实现结果做了回填：§1 记录工具的真实行为（有两条假设被实测推翻），§11 记录验收结论，§14 列出有意接受的取舍。

只想用工具的话，按这个顺序看：§10（命令行）、§0（三种模式）、§14（取舍）。其余章节解释的是“为什么是这样”。

---

## 0. 范围与模式

### 0.1 目标

1. **先做决策，再压缩**：分辨率上限优先，字节阈值其次，再往后才是编码器/HDR/动画等闸门 —— 因为降质量只能省几个百分点，而像素数减半能在编码器介入之前就省掉约 50%。
2. **越跑越收敛**：重复运行不会对已决策过的文件重新探测、重新编码，`--audit` 可以证明这一点。
3. **可选的原地替换**：单文件层面原子、配 `--keep-originals` 可回滚，且绝不会让原文件名下出现“写了一半”或“转了一半”的内容。
4. 保持既定约束：单文件 Python、只用标准库、全部用 `pathlib`、注释与 docstring 英文、控制台输出精简、任何文件失败都以退出码 1 结束。

### 0.2 非目标

- 不做并行（与“单个共享临时目录”和“台账单写者”冲突）。
- 不做 watch 模式、不做 GUI；归档文件只记录不处理。
- 阈值/上限/质量全部是硬编码常量，不开放命令行开关。
- **编码过程本身永远不是原子的，只有“换名”是原子的**。有损转码不存在原子性可言；能保证的是：目标路径上任何时刻要么是完整的旧文件，要么是完整的新文件。

### 0.3 三种模式

| 模式 | 参数 | “已处理”的判定 | 原文件 | 报告 + 台账位置 |
| --- | --- | --- | --- | --- |
| 复制输出（默认） | *无* | 输出已存在 **或** 台账命中 | 完全不动 | `<输出目录>/`（`_compressed/`） |
| 原地替换 | `--in-place` | 台账命中 | 被替换 | `<输入目录>/.compress-state/` |
| 原地 + 备份 | `--in-place --keep-originals [DIR]` | 台账命中（+ 备份存在） | 镜像到 `_originals/` | 同上 |

`--in-place` 不带 `--keep-originals` 是允许的；对它的推荐流程是先 `--dry-run`，再 `--limit N` 小步验证。

三种模式都受 `--profile`（§16）影响，但**档位只作用于从未被压缩过的文件** —— 已压缩的文件是终态，换档不会重压它。

**与原计划的差异：台账现在两种模式都有，不再只服务原地模式。** “输出已存在”能覆盖已替换的文件，却覆盖不了**压不动**的文件（`not_smaller`、`modern_codec` 等）—— 没有台账的话，这些文件每跑一次都会被重新探测、重新转码，而一个 2 GB 的视频恰恰是最不该重复转的那类，这正是本工具要避免的浪费。

---

## 1. 实测确认的工具事实（M0）

下面每一条都在写代码前实测过；❌/⚠️ 表示假设错误或只部分成立。

| # | 原假设 | 实测结果 | 对设计的影响 |
| --- | --- | --- | --- |
| 1 | caesiumclt 用 `-q` / `-o`，输出沿用输入的文件名与扩展名 | ✅ 1.5.0：`-q 82 -o <目录> photo.jpg` → `<目录>/photo.jpg` | 按计划实现 |
| 2 | 尺寸上限开关叫 `-S`/`--size` | ❌ **`-S` 是 `--keep-structure`**；真正的尺寸参数是 `--long-edge`、`--width`、`--height`、`--short-edge`，外加 `--no-upscale` | 缩放改用 `--long-edge 4096 --no-upscale`（实测 1200×900 → 600×450） |
| 3 | 覆盖行为 | `-O all\|never\|bigger`，默认 `all` | 传 `-O all`，且本来就写进全新临时目录 |
| 4 | ffmpeg 带 `libx264` 与 `aac` | ✅（另有 libx265、libsvtav1、libvpx-vp9） | 预检时抓取 `ffmpeg -encoders` |
| 5 | `-fps_mode passthrough` 可用 | ✅ | 所有视频都带上 |
| 6 | 能用 `ctypes` 调 `ReplaceFileW` | ⚠️ 只有带 `REPLACEFILE_IGNORE_MERGE_ERRORS`（0x2）才成功；不带会返回 `ERROR_ACCESS_DENIED`（5），目标文件保持不动 | 带该标志调用，失败则回退 `os.replace` |
| 7 | Windows 上 `os.stat()` 会填 `st_ino`/`st_dev` | ✅ 硬链接共享二者（`nlink=2`） | 同 inode 闸门成立 |
| 8 | ffprobe 能给出各闸门需要的字段 | ✅ codec、bit_rate、pix_fmt、color_transfer、nb_frames、chapters 都有；**静态图片没有 duration，也没有 `nb_frames`** | 字段一律做了容错读取；图片不需要时长 |
| 9 | caesiumclt 能读我们判定为“图片”的所有格式 | ❌ **AVIF 读不了**（`exit −1`，"Unable to compute the base path for the files."）；WebP/JPEG/PNG/GIF/TIFF/APNG 正常 | 新增 `unsupported_by_tool` 闸门，跳过 AVIF/HEIC/HEIF/JXL |
| 10 | 节省余量必须由我们自己判定 | ✅ 但 caesiumclt 自带 `--min-savings <字节\|n%\|尺寸>`，**不达标时退出 0 且不写任何文件** | 用它做“不值得替换”的信号（`no_size_gain`），我们自己的 5% / 64 KiB 规则作为第二道闸 |
| 11 | EXIF 与时间戳可保留 | ✅ `-e` 保 EXIF（用 Pillow 往返验证）、`--keep-orientation` 保方向、`--keep-dates` 保 mtime | 三个参数都传给 caesiumclt |
| 12 | 动画内容可判定 | ✅ 动画 GIF 报 `nb_frames > 1`；动画 WebP 的 codec/format 是 `webp_anim`；APNG 是 `apng` | 动画闸门成立 |
| 13 | HDR 可判定 | ✅ 文件带标记时能读到 `color_transfer=smpte2084` / `arib-std-b67` | HDR 闸门成立 |
| 14 | Python 的 `stat` 模块有 `FILE_ATTRIBUTE_RECALL_ON_OPEN` | ❌ 没有暴露 | 本地自定义常量（0x40000） |

---

## 2. 处理流水线

```
扫描 → 分类 → 廉价闸门 → 台账命中 → 输出已存在（复制模式）
     → ffprobe → 策略（上限 / 阈值 / 编码器）→ [dry-run：只记录计划，结束]
     → 编码到临时文件 → 校验临时文件 → 复核原文件 → 换名 → 写台账 → 写报告
```

这个顺序带来的几条硬性规则：

- **廉价闸门绝不探测**。垃圾文件、下载未完成、云端占位、归档、不支持的扩展名、空文件、超长路径、重复 inode，全靠文件名和 `stat()` 判定。
- **查台账在 ffprobe 之前**，所以重复运行每个文件只花一次 `stat()`，而不是一次探测；对压不动的文件更是省下一整次转码。
- **每个文件恰好产生一条报告记录**，`reason` 取自 §3 的枚举，最多再产生一条台账记录。
- **`--dry-run` 在策略判定后即结束**：会读台账，但不建临时目录、不写台账、不产出任何媒体文件，只在报告里标注 `"planned": true`。

---

## 3. 闸门与 reason 码

### 3.1 廉价闸门（按判定顺序）

| 闸门 | 触发条件 | `reason` |
| --- | --- | --- |
| 垃圾文件 | 文件名命中 `JUNK_FILES`（`.DS_Store`、`Thumbs.db`、`desktop.ini` 等） | `junk` |
| 下载未完成 | 后缀命中 `.part .crdownload .!ut .aria2 .partial .download` | `in_progress` |
| 空文件 | `st_size == 0` | `empty` |
| 云端占位（Windows） | `st_file_attributes` 含 `OFFLINE` / `RECALL_ON_OPEN` / `RECALL_ON_DATA_ACCESS` | `cloud_placeholder` |
| 超长路径（Windows） | `len(str(path)) > 240` | `too_long_path` |
| 可能仍在写入 | `mtime` 距今不足 300 秒 | `in_progress` |
| 重复 inode | 本轮已见过同一 `(st_dev, st_ino)` | `duplicate_inode` |
| 归档 | 命中归档后缀 | `archive` |
| 不支持 | 扩展名未知且魔数也认不出 | `unsupported` |
| 产物目录 | 任一父目录是 `_compressed`、`_originals`、`.compress-state`、`.compress-tmp` | *（不记录）* |

无扩展名的下载文件用魔数识别（JPEG/PNG/GIF/BMP/TIFF/RIFF-WEBP/AVI、Matroska、FLV、ASF、`ftyp` 品牌），因为 `imghdr` 在 Python 3.13 已被移除。

### 3.2 reason 码全集

`junk`、`in_progress`、`cloud_placeholder`、`too_long_path`、`duplicate_inode`、`empty`、`archive`、`unsupported`、`unsupported_by_tool`、`container_incompatible`、`animated`、`hdr`、`modern_codec`、`below_threshold`、`already_processed`、`not_smaller`、`no_size_gain`、`changed_during_run`、`locked`、`failed_probe`、`failed_encode`、`failed_verify`、`timeout`、`no_disk_space`、`interrupted`。

元组 `REASONS` 就是契约本身；`RETRYABLE_REASONS` 标出值得重试的失败；`NEVER_LEDGER_REASONS`（`in_progress`、`cloud_placeholder`、`duplicate_inode`、`locked`）本质上是暂态，永远不写进台账。

---

## 4. 图片策略

### 4.1 先判分辨率上限，再判质量

| 常量 | 取值 | 理由 |
| --- | --- | --- |
| `IMAGE_MAX_LONG_EDGE` | 4096 | 手机照片与截图原样放过，只动超大的扫描件/渲染图/全景图 |
| `IMAGE_DOWNSCALE_TOLERANCE` | 1.05 | 4100 px 的图不会为了 1% 的收益被缩放 |
| 放大 | 从不 | `--no-upscale` |
| 宽高比 | 由 caesiumclt 保持 | 实测 1200×900 → 600×450 |

只要满足 `size > 阈值` **或** `长边 > 上限 × 容差` 就会处理，所以“已经压得很好但尺寸超标”的图片照样会被缩放 —— 省下来的字节主要就在那里。

质量取值由“是哪一条判定命中”决定：

| 情况 | `-q` | 效果 |
| --- | --- | --- |
| 超过字节阈值 | 82 | 常规有损压缩 |
| 只是尺寸超标（本来已经很省） | 95 | 只缩放，几乎不动质量 |
| 已是现代容器（WebP/JXL） | 100 | 只缩放 |

实测：6000×4000 的 JPEG 输出为 4096×2731；3000×2000 的 PNG 从 8.3 MB 降到 5.3 MB。

### 4.2 元数据

- `-e` 保 EXIF，`--keep-orientation` 保方向标签，`--keep-dates` 恢复 mtime。已实测往返：原地替换后 `DateTimeOriginal`、`Make` 仍在，`mtime` 逐纳秒一致（`st_mtime_ns`）。
- 对台账的影响：`mtime` 是被我们**有意恢复**的，所以它只能与文件大小一起当作“文件有没有被换过”的新鲜度信号（见 §8.3）。

### 4.3 有意不实现的两个图片闸门

原计划里还有两个图片闸门，但对照现有的“每像素字节数”阈值后发现它们**永远不可能触发**，属于死代码：

- *纯色/线稿闸门*（`bpp < 0.15` 走无损）：PNG 的阈值是 0.65 bpp，所以低于 0.15 bpp 的文件不可能超过阈值。这类图片只可能因为“尺寸超标”进入处理，而对它做缩放恰恰是正确的。
- *JPEG 代际损失闸门*（读 DQT 量化表，源质量 ≤ 82 就跳过）：JPEG 的 0.28 bpp 档位本身就大致对应质量 82，所以超过它的 JPEG 都是真该压的；而已经处于质量 82 的 JPEG 会落到阈值之下，被 `below_threshold` 跳过。

两者都选择不写，而不是留成无法测试的分支；`already_at_target_quality` 也从 reason 全集里删掉了。**这张档位表本身就是“是否已经足够省”的判据。**

---

## 5. 视频策略

### 5.1 闸门（按顺序）

1. **HDR**（`color_transfer` ∈ {`smpte2084`, `arib-std-b67`}）→ 跳过 `hdr`。直接喂给 x264 会丢掉传输特性元数据，画面上会发灰发白。
2. **容器兼容性（仅原地模式）**：编码结果要沿用原文件名，容器必须装得下 H.264/AAC。后缀不在
   `{.mp4 .m4v .mov .3gp .mkv .avi .flv .ts .m2ts}` 之内（即 WebM、WMV、MPEG）→ 跳过 `container_incompatible`。复制输出模式下这些格式会写成同名的 `.mp4` 兄弟文件。
3. **现代编码器**：`hevc`、`h265`、`av1`、`vp9`、`vp8`，且实测码率 ≤ 对应档位 × 1.2 → 跳过 `modern_codec`。用 x264 重压它们通常是画质降级，体积却几乎不变。
4. **字节阈值**（档位码率 × 时长，钳制在 2 MiB … 8 GiB）**或** **分辨率上限**（`height > 1440 × 1.05`）→ 编码；否则跳过 `below_threshold`。

档位码率沿用最初规格：240p→400、360p→800、480p→1400、720p→2800、1080p→5500、1440p→9000、2160p→18000 kbit/s。

### 5.2 ffmpeg 调用

```
ffmpeg -y -hide_banner -loglevel error -nostdin [-hwaccel d3d11va] -i <源文件>
  -map 0:v:0 [-map 0:a?] [-map 0:<字幕流序号>? …]
  -map_metadata 0 -map_chapters 0
  -c:v libx264 -crf 23 -preset medium [-vf scale=-2:1440] [-pix_fmt yuv420p]
       # --encoder qsv / qsv-hevc 时改为（见 §5.7）：
       # -c:v h264_qsv|hevc_qsv -b:v <目标码率>k -preset … -pix_fmt nv12 [-tag:v hvc1]
  -fps_mode passthrough
  -an | -c:a copy | -c:a aac -b:a 128k
  [-c:s mov_text | -sn]
  [-movflags +faststart]           # 仅 .mp4/.m4v/.mov/.3gp
  <目标文件>
```

| 参数 | 原因 |
| --- | --- |
| `-hwaccel <name>` | **输入选项，放在 `-i` 之前**：把解码放到 GPU 上（见 §5.6）。默认 `d3d11va`（Windows），`--no-hwaccel` 关闭 |
| `-nostdin` | 批量运行时不让 ffmpeg 抢终端输入 |
| `-map 0:v:0` + `-map 0:a?` + 显式字幕流序号 | 原来的单 `-map` 会静默丢掉多余音轨、章节、附件与元数据；显式映射还能避免 data/attachment 流把封装搞崩 |
| `scale=-2:1440` | 绝不放大，且宽高恒为偶数（H.264 要求） |
| `-pix_fmt yuv420p` | 缩放时，或源不是 4:2:0 8-bit 时 |
| `-fps_mode passthrough` | 否则手机拍的 VFR 视频时序会被改变 |
| 所有音轨都在 MP4 安全集（`aac mp3 ac3 eac3 alac`）里时用 `-c:a copy` | 把 96 kbit/s 的 AAC 重编成 128 kbit/s 反而会变大，直接把“更小”的判据顶翻 |
| 文本字幕转 `-c:s mov_text`，位图字幕则 `-sn` | 位图字幕无法封装进 MP4；被丢弃的数量记在 `dropped_bitmap_subtitles` |
| 仅 MP4 家族输出才加 `-movflags +faststart` | **验收时发现**：matroska/avi/flv 的 muxer 不认这个参数，否则原地模式下每个 `.mkv` 都会失败 |

### 5.5 时间限制：没有总时长上限，只有卡死看门狗

**曾经的公式是 bug，不是保守设置。** `60 + 0.25 × 时长` 隐含假设"编码速度 ≥ 4× 实时"，而实测 x264 medium 在 1080p 上只有 **0.7× 实时（空闲、易压内容）到 2.8× 实时（难压内容）**，老机器还要再差 2–5 倍。而且**同一台机器上速度还随负载大幅波动**：验收里那段 2 分钟视频，前一次跑用了 158 秒出头（4 分钟素材），负载重的一次实测 **464 秒（0.259× 实时）** —— 旧公式对 2 分钟素材只允许 **90 秒**，差了 **5 倍**。代进去就是：这台机器上**任何超过约 2 分钟的视频都可能被误杀**（难压内容 24 秒就够）。真实使用中确实发生了：

```
14:31:51 失败 timeout ***：timeout after 289s    ← 对应约 15 分钟的视频
14:41:50 失败 timeout ***：timeout after 599s    ← 对应约 36 分钟的视频
```

代价还不只是"失败"：长视频要**先烧掉 5–10 分钟 CPU** 才判定失败。

**现在：没有任何总时长上限。** 慢机器、长视频、4K、慢 preset 都不会被误杀。取而代之的是一个**卡死看门狗**，它只对"什么都没发生"反应：

| | 旧的总时长上限 | 现在的卡死看门狗 |
| --- | --- | --- |
| 触发条件 | 总耗时超过 `60 + 0.25×时长` | **连续 N 秒没有任何进度输出**（默认 N = 600） |
| 慢机器 / 长视频 / 4K / preset slow | 误杀 | 不触发 |
| 真的挂住（网络盘 I/O、硬解死锁） | 要等到算出的那一刻才杀 | N 秒内杀掉 |

- **数据来源**：ffmpeg 带 `-nostats -progress pipe:1` 运行，进度行（`frame=`/`out_time_ms=`/`speed=`）由一条读取线程消费（实测每 ~0.2 秒一行）。
- **心跳**：`run.log` 每 60 秒写一行进度，TTY 上每 15 秒显示一次 —— 长视频不再是黑箱。
- **`--stall-timeout N`**：改阈值；`0` 表示**彻底不设时限**（看门狗也关掉）。
- **图片（caesiumclt）没有进度输出**，因此同样不设时限：它的工作量由源图本身决定（实测 70 Mpx 源在 `tiny` 设置下 2.6 秒、`balanced` 下 4.5 秒），设限只会带来误杀。
- **看门狗失效时不会误杀**：读取线程一旦异常退出，看门狗自动放弃判定（否则会把正常编码误判为卡死）。
- 卡死记为 `timeout`（可重试、不写台账），错误信息写明"连续 N 秒无进度、用时多少、最后进度"。

### 5.6 硬件解码加速（默认开启）

只把**解码**放到 GPU 上，编码仍是 CPU 的 libx264。意义在于：硬解不改变输出的任何一个比特，却能把高码率 / 4K / HEVC 源的解码开销从 CPU 上拿走。

本机实测（i5-1135G7 + Iris Xe，4K 56 Mbps H.264 源 → 1440p x264 crf23）：

| 方式 | 用时 | 输出 |
| --- | --- | --- |
| 纯软解 | 10.5 s | md5 `DD956972DB` |
| **`-hwaccel d3d11va`** | **9.3 s（−11%）** | md5 `DD956972DB`（逐字节相同） |
| `-hwaccel auto` | 9.8 s | 同上 |

1080p HEVC 源同样测过：9.9 s → 9.0 s（−9%），输出逐字节相同。收益上限受编码耗时限制 —— 解码省下的时间不会超过总耗时里解码所占的那部分。

设计要点：

- **平台选择**：Windows 用 `-hwaccel d3d11va`，其他平台交给 ffmpeg 的 `auto`。**不用 `-hwaccel qsv`**：实测它在 CPU 滤镜链（以及不缩放直接接 x264）下都会失败并产出 0 字节文件 —— QSV 的硬解帧需要显式 `hwdownload`/`vpp_qsv` 才能回到系统内存，而 `d3d11va` 能自动转换。
- **失败预算，不是一票否决**：某个文件让硬件路径失败**一次**，不代表这台机器不能用硬件。所以允许 `HARDWARE_MAX_FAILURES`（默认 3）次文件级失败，超过才把本次运行后续文件切到软件路径；日志写成 `硬解失败（第 1/3 次），本文件改用软解重试` → 第 3 次才 `硬解已失败 3 次，本次运行后续文件改用软解`。（历史教训：早期版本一次失败就整轮关闭硬件，导致"第一个坏文件之后全库都在软解"。）
- **探针一次列全四条路径并给出原因**：运行开始时（非 `--dry-run`/`--audit`）在状态目录生成一个约 50 KB 的 H.264 小样，一次性探测两条解码路径（`d3d11va`、`qsv`）与两个硬件编码器（`qsv`、`qsv-hevc`），日志写成两行：
  ```
  硬件探针 d3d11va=True qsv=False encoder_qsv=True encoder_qsv-hevc=True
  硬件探针原因 qsv: Impossible to convert between the formats supported by the filter 'graph -1 input from stream 0:0' and the filter 'auto_scale_0'
  ```
  失败原因取 ffmpeg 的**第一**行 —— 它先报原因、再吐一串后果，最后一行通常是无用的 `Nothing was written into output file`。
- **为什么解码用 `d3d11va` 而不是 `-hwaccel qsv`**：本机 QSV 解码器输出的是 `qsv` 硬件帧，喂给 CPU 滤镜链时自动转换失败（上面那条原因就是它）。显式加 `-hwaccel_output_format qsv` + `scale_qsv` + `hwdownload` 可以绕开，但命令复杂且收益相同 —— `d3d11va` 用的是同一块核显，实测输出逐字节一致。
- **可关闭**：`--no-hwaccel` 跳过探针与参数，用于排查问题或需要与纯软件解码严格一致的场合。
- **报告与日志**：`success.json` 每条记录带 `hwaccel`（实际使用值，未使用为 `null`），运行头带 `hwaccel=d3d11va|off`。
- **不在范围内**：硬件**编码**（`h264_qsv` 等）默认关闭 —— 它是用画质换速度，见 §5.7；只有显式 `--encoder qsv` / `qsv-hevc` 才启用。

### 5.7 硬件编码（QSV，opt-in）

`--encoder qsv`（`h264_qsv`）或 `--encoder qsv-hevc`（`hevc_qsv`）把**编码**也交给 Intel 核显。默认仍是 `x264`：这一步是**用画质换速度**，不像 §5.6 的硬解那样零代价。

本机实测（i5-1135G7 + Iris Xe）：

| 场景 | `x264`（默认） | `qsv` | `qsv-hevc` |
| --- | --- | --- | --- |
| 20 s 1080p CBR 源，纯编码耗时 | 14.0 s | **3.6 s（≈3.9×）** | 6.1 s（≈2.3×） |
| 5 s 加噪 1080p 源，纯编码耗时 | 13.9 s | **1.9 s（≈7×）** | 2.3 s |
| 同体积画质（加噪源 SSIM） | 12.06 MB / **0.9324** | 12.71 MB / 0.9028 | 5.00 MB / 0.8426（对比 x264 crf30 的 4.95 MB / 0.8532） |

**速度收益取决于内容，大致 3–6 倍**；端到端（含进程启动、探测）在短视频上会被固定开销摊薄。

关键约束（全部实测得出）：

- **本机 QSV 没有可用的画质模式**：`-global_quality`/`-q:v` 完全不生效（18/26/34/42 四档输出逐字节相同），`-look_ahead 1`（LA-ICQ）直接失败产出 0 字节。因此只能用**码率目标**驱动。
- **码率目标是上限而非等号**：`目标 = max(QSV_MIN_BITRATE_KBPS, min(档位在该输出分辨率的码率 × threshold_factor, 源码率 × QSV_MAX_SOURCE_RATIO))`。前一项让体积符合档位策略（`tiny` 更小），后一项保证"一定比源小"。VBR 在难压/带填充的源上贴近目标（目标 16M → 实测 15.7 Mbps），在极易压的内容上会**远低于**目标（4K testsrc 目标 9 Mbps → 输出仅 0.1 MB）—— 这对体积是好事。
- **画质旋钮失效**：QSV 模式下 `video_crf` 等画质参数不起作用，档位里仍然生效的是**入场阈值、缩放上限、最小节省**。即 `--profile tiny --encoder qsv` 会按 720p 上限缩放并按更低码率目标编码。`-preset` 对 QSV 只影响画质分布，不影响目标体积（实测 b4M 与 b4M-veryslow 输出同为 2.66 MB）。
- **同体积画质差约一档**（`h264_qsv`）；`qsv-hevc` 基本追平 x264。**想最小体积就用 x264**（或 `tiny` + x264）。
- **HEVC 需要标签**：`qsv-hevc` 在 MP4 家族输出时加 `-tag:v hvc1`，否则不少播放器拒播；它同时改变了编码格式，老设备兼容性需自行权衡。
- **必须能回退**：启动时用 320×240 小样试编一次，失败则本次运行整体回退 x264，并把 `policy` 一并改成 x264 组合；即使探针通过，个别文件失败也按 `(硬解,硬编) → (硬解,x264) → (软解,x264)` 顺序退让，全部失败才记 `failed_encode`。**文件级失败同样走失败预算**（`HARDWARE_MAX_FAILURES` = 3，见 §5.6）：单个文件失败不会把整轮切到 CPU。
- **卡死不重试第二次硬件路径**：若某次尝试因卡死（`ToolStalled`）被看门狗中止，只会再用**纯软解**那条路试一次（硬件死锁是常见原因），不会为一个文件连续等两个 600 秒。
- **编码器是策略的一部分**：`--encoder` 参与 `policy` 指纹（硬解不参与，因为它逐字节相同）。于是换编码器会**重新评估**当初判 `no_change` 的文件（例如 x264 CRF 下"压不动"、但按码率目标能压小的文件），而**已压缩文件仍是终态**（§16.1），不会被重压。
- **报告**：`success.json` 每条记录带 `encoder`（实际使用值，回退时也如实记录），三种报告与 `audit.json` 都带本次的 `encoder` 与 `policy`。

---

## 6. 常量表（全部策略一张表）

**与档位无关的全局常量**（三档共用）：

| 常量 | 取值 |
| --- | --- |
| `RULES_VERSION` | 2（只管规则结构，且只让 `no_change` 失效；见 §16.3） |
| `IMAGE_BYTES_PER_PIXEL` | png 0.65、bmp 0.90、tif 0.80、gif 0.35、jpg/jpeg/jfif 0.28、webp 0.20、heic 0.22、avif 0.15，默认 0.50 |
| `IMAGE_DEFAULT_BYTES_PER_PIXEL` | 0.50 |
| `IMAGE_DOWNSCALE_TOLERANCE` / `VIDEO_DOWNSCALE_TOLERANCE` | 1.05 / 1.05 |
| `VIDEO_KBPS_TIERS` | 240→400 … 2160→18000 |
| `MODERN_VIDEO_CODECS` | hevc、h265、av1、vp9、vp8 |
| `HDR_COLOR_TRANSFERS` | smpte2084、arib-std-b67 |
| `IN_PROGRESS_MTIME_SECONDS` / `MAX_PATH_LENGTH` | 300 秒 / 240 |
| `PROBE_TIMEOUT` | 60 秒（只用于 ffprobe 与启动探针这类有界操作） |
| `STALL_TIMEOUT_SECONDS` | 600 秒无进度即判定卡死（`--stall-timeout`，0 = 关闭） |
| `PROGRESS_LOG_SECONDS` / `PROGRESS_TTY_SECONDS` | 60 / 15 秒（编码心跳间隔） |
| `FREE_SPACE_MARGIN` / `REPLACE_RETRIES` / 间隔 | 64 MiB / 3 / 0.5 秒 |
| `HASH_CHUNK` | 64 KiB（首尾指纹） |
| `HWACCEL_DECODE` | Windows 上 `d3d11va`，其他平台 `auto`（见 §5.6；`--no-hwaccel` 可关） |
| `ENCODERS` / `ENCODER_CODECS` | `x264`→libx264、`qsv`→h264_qsv、`qsv-hevc`→hevc_qsv（见 §5.7） |
| `QSV_MAX_SOURCE_RATIO` / `QSV_MIN_BITRATE_KBPS` | 0.80 / 150（QSV 码率目标的上下界） |
| `HARDWARE_MAX_FAILURES` | 3（文件级硬件失败预算，超过才把整轮切到软件路径） |

**每档一套的常量**（`IMAGE_QUALITY`、`IMAGE_MAX_LONG_EDGE`、`VIDEO_CRF`、最小节省等）现在都在 `Profile` 里，见 §16.2 的三档表。运行时用 `--profile` 选一套，默认 `balanced` 与 v0.2.0 的数值逐字节相同。

---

## 7. 原地替换的原子性

### 7.1 操作顺序（不可颠倒）

1. 编码到**同卷**临时目录里的临时文件。
2. 校验临时文件（§7.3）。失败 → 删临时文件、原文件不动、记 `failed_verify`。
3. 乐观复核：再 `stat()` 一次原文件；与做计划时相比 size 或 mtime 有任何变化 → `changed_during_run`，什么都不替换。
4. 给临时文件补元数据（`os.utime`；图片的 EXIF/mtime 已由 caesiumclt 处理）。
5. `--keep-originals`：先把原文件复制到 `_originals/<相对路径>`，并校验副本大小，**然后**才换名。
6. 换名（§7.4）。
7. 写台账，再写报告。

**为什么是“先换名、后记账”**：万一崩在两步之间，留下的是“已压缩但未记录”的文件；下轮它会重压一次，结果达不到 5% 就会被 `not_smaller` 丢弃，代价只是一次白跑的转码。反过来先记账则会留下“已记录但根本没压”的文件，而且**永远**被跳过。D1 用例实测：编码中途硬杀进程，原文件逐字节不变，台账里也没有任何“已替换”的假记录。

### 7.2 临时目录

- 复制输出：`<输出目录>/.compress-tmp/`；原地替换：`<输入目录>/.compress-tmp/`。两者都会被扫描排除。
- 每轮一个目录，每个文件前清空（`prepare_temp_dir`），`finally` 里删除（`cleanup_temp_dir`）。崩溃残留由下一次运行清掉（D2 用例实测）。
- **必须同卷** —— 跨卷的 `os.replace` 会退化成“复制 + 删除”，就不再原子了。
- caesiumclt 的输出名由输入名推导，所以图片是落到临时**目录**（`photo.jpg`）再被换名过去的；这也是“一个共享目录 + 顺序处理”就够用的原因，也是并行化（M6）必须改成“每 worker 一个子目录”的原因。

### 7.3 临时文件校验（比换名更重要）

| 校验 | 规则 |
| --- | --- |
| 存在 / 非空 | 是常规文件，`size > 0` |
| 可否解码 | `ffprobe` 退出码为 0 |
| 几何 | 图片：长边 ≤ 上限且 ≤ 输入，宽高比误差 < 2%（未缩放时则要求尺寸完全一致）；视频：高度与目标相差 ≤ 2 px，时长在 `max(0.5 秒, 1%)` 之内 |
| 流数量 | 至少一路视频；音频流数量与源一致 |
| 节省是否有意义 | `size_after ≤ 0.95 × size_before` **或** `size_before − size_after ≥ 64 KiB`，且必须真的比原文件小 |

### 7.4 换名

| 平台 | 调用 | 说明 |
| --- | --- | --- |
| Windows | `ctypes` → `ReplaceFileW(target, temp, None, 0x2, …)` | 实测**只有**带 `REPLACEFILE_IGNORE_MERGE_ERRORS` 才成功 |
| 回退 / POSIX | `os.replace(temp, target)` | NTFS 上是 `MoveFileExW(REPLACE_EXISTING)`，POSIX 上是 `rename(2)` |
| 重试 | 3 次，退避 0.5/1.0/1.5 秒 | 应对资源管理器预览、杀软、同步客户端造成的共享冲突 |

换名失败 → 记 `locked`、删临时文件、原文件不动。**绝不会为了“腾地方”去删原文件。** 只读文件会先清掉只读属性，换名后再恢复。

### 7.5 失败与状态对照

| 失败点 | 原文件 | 临时文件 | 报告 | 台账 |
| --- | --- | --- | --- | --- |
| 探测 | 不动 | 无 | failed `failed_probe` | 无 |
| 策略跳过 | 不动 | 无 | skipped `reason` | `no_change`（暂态闸门除外） |
| 空间不足 | 不动 | 无 | failed `no_disk_space` | 无 |
| 编码 / 超时 | 不动 | 删除 | failed `failed_encode` / `timeout` | 无 |
| 校验 | 不动 | 删除 | failed `failed_verify` | 无 |
| 节省不够 | 不动 | 删除 | skipped `not_smaller` / `no_size_gain` | `no_change` |
| 运行中被改 | 不动 | 删除 | skipped `changed_during_run` | 无 |
| 换名失败 | 不动 | 删除 | failed `locked` | 无 |
| 被中断 | 不动 | `finally` 清理 | 退出码 1 | 已写入的记录保留 |

暂态失败**有意不记账**，否则一次坏运气就会让某个文件永远不再被处理。

---

## 8. 台账（防止重复压缩的状态文件）

### 8.1 位置

| 模式 | 路径 |
| --- | --- |
| 复制输出 | `<输出目录>/state.jsonl`（与 `success.json` 同级，扫描时排除） |
| 原地替换 | `<输入目录>/.compress-state/state.jsonl` |

两者都放在报告旁边、跟着目录树走，并按目录名从扫描中排除。

### 8.2 格式

追加式 JSONL，一行一条，按 key 后写覆盖先写。每条在文件决策完成后**立即写入并 `fsync`**，所以第 400/500 个文件时崩溃不会丢掉前 399 条。加载时遇到半截行会丢弃，把旧文件备份为 `state.jsonl.bak-<epoch>`，并往 `run.log` 记一行（B4 用例实测）。

### 8.3 记录结构与 key 强度

```json
{
  "key": "sub/clip.mp4",
  "rules_version": 2,
  "time": "2026-10-01T11:12:44",
  "status": "replaced",
  "reason": "",
  "source_size": 14797565,
  "output_size": 421133,
  "saved": 14376432,
  "mtime_ns": 1759303451000000000,
  "geometry": {"width_before": 1920, "height_before": 1080, "quality": 82, "target_height": null},
  "head_tail_hash": "9f2c…"
}
```

- **运行时的 key = 相对路径 + mtime_ns + 大小**。原地模式下文件已被替换，所以大小与 `output_size` 比较；复制输出模式下源文件没变，所以与 `source_size` 比较 —— 这正是台账需要知道自己所处模式的原因。
- `head_tail_hash` 只存不校验：每轮为每个文件读 128 KiB 不划算，而 size+mtime 已经足以发现变更。`--audit` 会校验它并汇报 `hash_mismatch`。
- 存相对路径，因此整棵树搬走后台账仍然有效。
- `status` 取 `replaced` 或 `no_change`；`saved` 让“累计节省”在两种模式下都精确。
- `rules_version` 不一致 ⇒ 该记录按过期处理并忽略（B5 用例实测）。

### 8.4 锁与清理

- 单写者：`<状态目录>/state.lock`（内容为 pid 与启动时间，用 `O_CREAT|O_EXCL` 创建），在 `finally` 中删除。第二个实例会**最多等待 `--lock-timeout` 秒（默认 30）后以退出码 2 结束**；`--lock-timeout 0` 表示立即拒绝（C1 用例实测）。超过 6 小时的锁视为过期并接管。
- `--prune` 删除“文件已不存在”的记录，并用 `state.jsonl.tmp` → `os.replace` 原子重写台账。默认**不删**缺失文件，这样外置硬盘没挂载时不会触发全量重压。
- `--dry-run` 绝不写台账；`--audit` 只读。

---

## 9. 报告、日志、退出码、预检与巡检

### 9.1 报告

`success.json`、`failed.json`、`skipped.json`（位置：输出目录，或原地模式的状态目录）：

```json
{
  "root": "D:\\Downloads\\media",
  "rules_version": 2,
  "generated": "2026-10-01T11:12:44",
  "count": 6,
  "mode": "in-place",
  "profile": "balanced",
  "policy": "fffad832d65ee9fa",
  "items": [{"source": "sub/clip.mp4", "output": "sub/clip.mp4", "type": "video",
             "size_before": 14797565, "size_after": 421133, "saved": 14376432,
             "scaled": true, "threshold": 2062500, "codec": "h264", "quality": 82,
             "width_before": 1920, "height_before": 1080, "duration": 3.0,
             "hwaccel": "d3d11va", "encoder": "x264"}]
}
```

路径一律是相对 `root` 的，因此报告在搬盘后依然可用；`failed.json` 的记录带 `reason`、`error`（最多 2 KB 工具输出）和 `retryable`。三种报告都带 `profile` 与 `policy`，让每次运行的产物自描述。

### 9.2 `run.log`

**追加**写入（不覆盖），运行头包含：模式、根目录、输出目录、`dry-run` 标记、`RULES_VERSION`、当前档位与 `policy` 指纹、实际启用的硬件解码器与编码器、卡死阈值（`stall=600s|off`）；工具版本**单独成行**（`工具版本 ffmpeg="…" caesiumclt="…"`，不再是 Python 字典字面量）。之后每个文件记录：

- 台账判定与（原地模式的）换名方式（`ReplaceFileW` / `os.replace`）；
- `exec <完整命令行>`：**可复制粘贴**——安全字符集之外的参数一律加引号（含空格、`&`、括号的路径不会再被拆开）；
- 视频的编码上下文与尝试序号：`完成 <相对路径> 1920x1080->1440p 916s x264/d3d11va [尝试 1/2] 用时 812.4s（已编码 916s 速度 1.13x 帧 27480）` —— 几何、时长、编解码器、第几次尝试、耗时、进度与实时速度都在一行里；
- 编码期间每 60 秒一行心跳进度（TTY 上每 15 秒）；
- 中断时记录已扫描/成功/失败/跳过计数，并说明未完成的部分下次会继续。

运行开始前还有两行**硬件探针**（所有可用路径 + 失败原因），见 §5.6 —— 出现"怎么突然全程软解"这类问题时，先看这两行。

这是跨轮次的审计线索。

### 9.3 控制台

```
输出目录 D:\Downloads\media\.compress-state
档位 balanced（policy fffad832d65ee9fa）
已扫描 23 | 成功 6 | 失败 2 | 跳过 15 | 节省 132.4 MB（累计 132.4 MB）
```

进度行只在 TTY 上出现，每 25 个文件一行。`--dry-run` 会多打一行解释。“累计”数字来自台账。

### 9.4 退出码

| 码 | 含义 |
| --- | --- |
| 0 | 无失败 |
| 1 | 至少一个文件失败（包括 `--dry-run` 期间探测失败，以及被中断） |
| 2 | 预检或用法错误：缺少工具/编码器、输入不是目录、输出包含输入、锁被占用 |

### 9.5 预检

用 `shutil.which` 检查 ffmpeg/ffprobe/caesiumclt；`ffmpeg -encoders` 必须含 `libx264` 与 `aac`；`caesiumclt --version` 必须成功。所有问题一次性打印，退出码 2。

### 9.6 `--audit`

只读收敛巡检：套用同一批闸门与策略，写出 `audit.json`（各 reason 计数、`would_compress` 列表、台账条数/过期数/哈希不符数、复制模式下的不可解码产物，以及本次的 `profile` 与 `policy`），并打印三行摘要。它不加锁、也不写报告，所以不会覆盖真实运行的产物。实测：一次完整的原地运行之后，`would_compress` 为空；把台账里的 `no_change` 记录作废（改 `rules_version` 或换档）后，只有那些**从未被压缩过**的文件会重新出现在 `would_compress` 里，已压缩文件一律计入 `already_compressed`。

---

## 10. 命令行

```
files-compress <输入目录> [-o <输出目录>] [--dry-run]
               [--in-place] [--keep-originals [DIR]] [--audit] [--prune]
               [--limit N] [--order size|name] [--lock-timeout S] [--version]
```

| 参数 | 默认 | 说明 |
| --- | --- | --- |
| `<输入目录>` | 必填 | 递归扫描 |
| `-o/--output` | `<输入目录>/_compressed` | 原地模式下给会被忽略并提示 |
| `--dry-run` | 关 | 只出计划；写报告，但不写台账、不建临时目录、不动媒体 |
| `--in-place` | 关 | 原子替换原文件 |
| `--keep-originals [DIR]` | `_originals` | 换名前镜像原文件（仅原地模式） |
| `--audit` | 关 | 只读收敛巡检，退出码 0 |
| `--no-hwaccel` | 关 | 关闭硬件解码加速（默认开启；见 §5.6） |
| `--encoder` | `x264` | 视频编码器：`x264`（CPU，默认，同体积画质最好）、`qsv`（核显 H.264，快约 3–6 倍，按码率驱动）、`qsv-hevc`（核显 HEVC，更省但换成 HEVC），见 §5.7 |
| `--profile` | `balanced` | 压缩档位：`balanced` 均衡（默认＝v0.2.0 数值）、`small` 更小、`tiny` 极端小（不考虑质量，尽可能小），见 §16 |
| `--prune` | 关 | 清理台账中已不存在的文件记录 |
| `--limit N` | 无 | 用于谨慎的首次试跑 |
| `--order` | `size` | 从大到小：中途中断也已经拿下最大的收益 |
| `--stall-timeout` | 600 | 编码连续 N 秒没有任何进度就判定卡死并中止；`0` = 关闭看门狗，**完全不设时限**（见 §5.5；没有总时长上限） |
| `--lock-timeout` | 30 秒 | 等待并发运行，超时则退出码 2 |
| `--version` | | 脚本版本 + 规则版本 |

有意不开放：阈值、上限、质量、CRF、超时、节省余量。原计划里的 `--backup-dir` 已删除，它与 `--keep-originals DIR` 重复。

> 计划新增的 `--profile balanced|small|tiny` 见 §16（已确认口径，代码未动）。

---

## 11. 验收

### 11.1 测试脚手架

[`tests/files-compress-fixtures.py`](tests/files-compress-fixtures.py) 生成夹具，[`tests/files-compress-accept.py`](tests/files-compress-accept.py) 在一份份夹具副本上运行 CLI 并断言下列检查（后者要用带 Pillow 的 Python 启动；CLI 本身仍用系统 Python 启动，保证被测解释器与真实一致）：

```powershell
python tests/files-compress-fixtures.py "$env:TEMP/fc-accept"
python tests/files-compress-accept.py
```

夹具要点：3000×2000 噪声 PNG、220×180 PNG、6000×4000 JPEG、4 MB 随机字节伪装成的 `.png` 与 `.mp4`、一个 640×360 / CRF 30 的纯噪声视频（重压后是它的 1.12 倍，用于 `not_smaller`）、一个 4K CBR 视频、一个低码率 HEVC、一个 HDR（PQ）文件、一个含两条 AAC 音轨加一条字幕的 1080p CBR 文件、动画 GIF、ZIP、垃圾/空/`.part`/无扩展名文件、一对硬链接、带 EXIF 的 JPEG、一条超过 240 字符的路径，以及一个 mtime 设在**未来一小时**的新鲜文件（用于"下载中"闸门 —— 见 §11.4 第 5 条）。

### 11.2 结果（96/96 通过）

| 分组 | 检查内容 |
| --- | --- |
| A 复制输出 | dry-run 计划 7 个待压缩但不写媒体/台账/临时目录；正式运行编码 6 个，并为 2 个损坏文件返回退出码 1；12 个闸门全部命中（`animated`、`hdr`、`modern_codec`、`archive`、`unsupported`、`junk`、`empty`、`in_progress`、`duplicate_inode`、`below_threshold`、`not_smaller`、`too_long_path`）；原文件未被改动；报告用相对路径；输出镜像目录树；6000×4000 → 4096×2731；4K → 2560×1440 且更小；run.log 含命令行与工具版本；台账把压不动的视频记为 `no_change`；重跑不重压任何文件 |
| B 原地替换 | 6 个文件替换且 `_originals` 副本可逐字节还原；每个产物都更小；mtime 保持不变；EXIF 的 `DateTimeOriginal`/`Make` 存活；台账每个成功对应一条 `replaced`；没有临时目录残留；重跑零动作且 6 个文件全部记为 `already_compressed`；`--audit` 的 `would_compress` 为空；台账半截行被丢弃并备份；改 `rules_version` 后只有 `no_change` 记录过期，已压缩文件仍按终态跳过 |
| C 并发 | 第二个实例加 `--lock-timeout 0` 时以退出码 2 结束并给出明确提示，之后锁文件被释放；编码途中被修改的文件原样保留（`changed_during_run`，原文件哈希不变，且没有台账记录） |
| D 中断 | 编码途中硬杀进程，原文件逐字节不变且没有 `replaced` 记录；残留的 `.compress-tmp` 目录被下一次运行清掉 |
| E 档位与终态 | 三档节省额严格递增（15.0 / 19.7 / 23.5 MB）；图片长边按档位递减 4096→2560→1920、视频高度 1440→1080→720；`tiny` 档日志里能看到 `-q 58`、`-crf 30 -preset slow`、`--zopfli`、`4:2:0`，`balanced` 档则保持 `-q 82`、`-crf 23 -preset medium` 且无额外开关；三个 `policy` 指纹互不相同并与报告一致；原地跑完 `balanced` 后换 `tiny`（再换回 `balanced`）时，3 个已压缩文件全部记 `already_compressed`、内容哈希不变，而未被压缩的 `no_change` 文件被重新评估（走 A）；只改 mtime 不改内容时仍按终态跳过（首尾哈希兜底） |
| F 硬件解码 | 探针跑通且 `-hwaccel d3d11va` 出现在 `-i` 之前；报告记录实际使用的解码器；`--no-hwaccel` 时不探测、不加参数、报告为 `null`；**开/关硬解的输出逐字节一致（md5 相同）**；单元检查：无效硬解名被探针拒绝、`-hwaccel` 只作为输入选项出现、软解命令不含该参数 |
| G 硬件编码 | 三个编码器都能压小；`qsv` 走 `h264_qsv` + `-b:v` + `-pix_fmt nv12`，`qsv-hevc` 走 `hevc_qsv` 且带 `-tag:v hvc1`，`x264` 日志里不出现任何 QSV 参数；编码器进入 `policy` 指纹（三者互不相同）且报告记录实际使用者；**换编码器不重压已压缩文件**（终态，哈希不变），但会把当初判 `no_change` 的文件重新评估并按码率压小 |
| H 时限与日志 | **2 分钟视频正常压完**（不再有任何总时长上限；历史实测：4 分钟视频需 158 秒，而旧公式只允许 120 秒）；无进度的卡死进程在 N 秒内被杀；一直在输出的慢任务不被误杀且进度被解析；`--stall-timeout 0` 时静默 3 秒也放行（完全不设时限）；命令行日志对含空格与 `&`/括号的路径加引号（可复制粘贴）；结束行带用时与进度；运行头不再出现 Python 字典字面量 |
| I 硬件失败预算与探针诊断 | 探针失败带回原始错误（ffmpeg 第一行，而不是无用的最后一行）；硬件探针一次列出四条路径；**单个文件的硬解失败不再关闭整轮硬解**（前两次失败后 `hwaccel` 仍有效、继续被后续文件使用），达到预算 3 次才切换，且失败文件本身仍成功（改走软解） |

对时序敏感：C2 与 D1 需要“编码耗时明显长于测试延时”，所以脚手架会为它们现生成一个 20 秒的 1080p CBR 源（重压约 10–20 秒）。

### 11.3 发现并修掉的问题

1. **复制输出模式从不检查“输出已存在”**（*验收套件发现*），导致重复运行会把所有文件重压一遍 —— 直接违反最初规格。先补上 `dest.exists()` 判定（§2），随后又把台账也给了复制模式（§0.3）。
2. **无条件传了 `-movflags +faststart`**（*验收套件发现*），matroska/avi/flv 的 muxer 不认它 —— 原地模式下每个 `.mkv` 都会失败。现在只对 MP4 家族输出加（§5.2）。
3. **捕获工具输出时用了控制台代码页解码**（*真实使用中发现，验收套件抓不到*）：`subprocess.run(..., text=True)` 按 ANSI 代码页（中文 Windows 上是 cp936）解码，而 ffmpeg/ffprobe 把文件名按 UTF-8 打印，于是任何非 ASCII 文件名的媒体都会在读线程里抛 `UnicodeDecodeError`。运行本身没中断（`subprocess` 会吞掉该异常），但**诊断信息丢了**：`stderr` 回来是空的，`failed_probe` 记下来却没有原因。修复方式：五处捕获调用统一加 `encoding="utf-8", errors="replace"`，脚手架管道同样处理，并用 `setup_console()` 把 stdout/stderr 规范为 UTF-8。复现用例：一个名为 `坏文件-😀测试.mp4` 的损坏文件 —— 修复前是堆栈 + 空 `error` 字段，修复后无堆栈、`failed_probe` 带出
   `"…坏文件-😀测试.mp4: Invalid data found when processing input"`，且 `大图-😀测试.png` / `视频-😀片段.mp4` 的真实编码成功、文件名原样保留。

4. **复制输出模式下“产物被删掉、台账却仍然跳过源文件”**（*实现档位语义时发现*）：旧实现的 `match()` 在复制模式下也按 `source_size` 命中，于是用户清空 `_compressed/` 后再跑，产物不会被重建 —— 与“输出存在即已处理”的对称性矛盾。现在复制模式只认 `dest.exists()`（`replaced` 记录不参与匹配），台账在该模式下只负责 `no_change` 记录。
5. **`match()` 漏掉了 `rules_version` 校验**（*验收套件发现*）：`no_change` 记录只比对了 `policy`，于是把台账的 `rules_version` 改成 999 之后再巡检，那些文件仍被当成“已处理”，`would_compress` 为 0。修复为同时校验 `rules_version` 与 `policy` —— `stale` 计数本来就已把两者算进去，只有匹配逻辑漏了。

6. **总时长上限把长视频误杀**（*真实使用中发现*）：`60 + 0.25 × 时长` 假设了编码速度，实测两个文件在 289 秒与 599 秒被中止（对应约 15 与 36 分钟的视频），而且每次都要先烧掉 5–10 分钟 CPU 才失败。修复见 §5.5：**删掉总时长上限**，改为只对"连续 N 秒没有任何进度"反应的卡死看门狗。
7. **`ProgressReader` 遮蔽了 `Thread.run`**（*实现看门狗时发现*）：读取线程的属性名用了 `run`，把 `Thread.run` 覆盖成 `Run` 数据类实例，线程一启动就抛 `TypeError: 'Run' object is not callable` **静默死掉**；更糟的是看门狗随后会拿一个永远不更新的时间戳判定卡死，**把正常编码误杀**。修复：属性改名（`owner`/`progress`）、读取线程整体套 `try/except`（异常记入 `error` 而不是让线程死掉），并让看门狗在读取线程不存活时**放弃判定**。

8. **一次硬解失败就把整轮切到软解**（*真实使用中发现*）：早期版本在编码重试里对任何一次文件级硬件失败都执行 `run.hwaccel = ""`，于是日志里出现一次 `硬解失败，改用软解重试` 之后，**后续所有文件都不再带 `-hwaccel`**（用户日志可证：其后每个 `exec` 行都没有该参数）。而那次失败的同一个错误在**软解重试时也出现了**，说明问题在文件而不在机器。修复：文件级**失败预算**（`HARDWARE_MAX_FAILURES` = 3），并把"本文件改用软件"与"整轮改用软件"分成两种日志。
9. **探针只记 `ok=False`，不记原因**（*用户提问直接暴露*）：加上原因后立刻露出第二个缺陷 —— 取的是 ffmpeg 的**最后**一行（`Nothing was written into output file…`），而真正的原因在**第一**行（`Impossible to convert between the formats…`）。修复：探针取第一行，编码失败取首尾两行（`原因 | … | 结论`）。现在"`qsv` 为什么用不了"可以直接从 `run.log` 读到。

套件未覆盖、但值得知道的：夹具里有静态 PNG/JPEG/GIF/WebP，却没有 HEIC/AVIF（caesiumclt 根本读不了 AVIF，见 §1.9），也没有 10-bit 非 HDR 视频。夹具文件名全是 ASCII，所以套件抓不到编码类 bug —— 复现它必须用非 ASCII 文件名，方法如上。

### 11.4 测试自身的五个坑（都已修）

跑久了会发现"变红的其实是测试"。这几类必须避免：

1. **`not_smaller` 夹具要够"硬"，而且要考虑"第二代"效应**：最初用 CRF 40 的噪声，它和"CRF 23 重压结果"只差约 1%，线程调度一变就翻转。换成 CRF 30 后又踩第二个坑 —— 我按**第一代**编码尺寸推断余量（以为 CRF 23 会大 3 倍），但夹具本身是**第二代**素材：已被有损压过的噪声更好压，重压结果反而可能更小。实测 640×360 / CRF 30 的源重压后是源的 **1.12 倍** ✓ 稳定丢弃。
2. **夹具尺寸也是正确性的一部分**：1080p 纯噪声在 CRF 30 下是 **43 MB**，把它塞进夹具后每个阶段都慢了一个量级（A 组从 1 分钟变成 8 分钟），还顺带触发了下面第 5 条。降到 640×360 后是 4.8 MB，比值不变（比值只取决于 CRF 差与内容难度）。
3. **断言不能依赖机器速度**：H1 原来断言"耗时 > 旧公式上限"，这在快机器上会**因为产品正常而失败**。现在只断言"长视频必须成功压完"，耗时写进 detail 供人看。
4. **不要用固定 sleep 等"运行中"**：C2 原来 `sleep(3)` 后改动文件；加了启动探针（+2–4 秒）之后，改动落在**扫描之前**，于是被当成"下载中"而不是"运行中被改"。现在改为**轮询日志里的 `exec ffmpeg`**，确认编码真的开始了再动手。
5. **`in_progress` 夹具会"过期"**：`fresh.jpg` 的 mtime 原本在运行时设为"当前时间"，但机器慢/任务长时，等扫描到它已经超过 300 秒窗口，于是它变成普通候选被压掉（A 组"恰好 6 个成功"变成 7）。现在把它的 mtime 设到**未来 1 小时**，整个运行期间都稳定落在"下载中"闸门里。
6. **别用 kill 半途放弃验证**：被 kill 的任务会留下孤儿 ffmpeg 进程（实测把 CPU 占满 100%，其中一个是 1080p veryslow 的怪兽任务），既拖慢后续所有阶段，也会让人误判成"产品变慢了"。kill 之后要 `Get-Process ffmpeg` 确认真的没了 —— 但**不要**去杀不是自己起的进程（这台机器上另有一个 VMware 虚拟机长期占用大量 CPU，那是使用者的环境）。

另外要注意：断言应匹配**稳定结构**而不是整句措辞。F1/G1 原来匹配 `硬解探针 … ok=True`、以及"日志里不出现 qsv"；探针改成一行列出四条路径后（`硬件探针 d3d11va=True qsv=False …`）两条立刻失效 —— 而 `qsv=False` 出现在 x264 运行的日志里**是正常的**。

---

## 12. 分期状态

| 阶段 | 内容 | 状态 |
| --- | --- | --- |
| M0 | 实测确认工具事实 | ✅ §1（两条假设被推翻） |
| M1 | 分辨率上限、编码器/HDR/动画闸门、EXIF 与元数据、节省余量、超时、魔数嗅探 | ✅ |
| M2 | reason 全集、相对路径报告、追加式 run.log（含命令行与版本）、累计节省、退出码 2、`--audit`、TTY 进度 | ✅ |
| M3 | 台账（JSONL、原子追加、锁、损坏恢复、`rules_version`、剪枝） | ✅ **并扩展到复制输出模式** |
| M4 | `--in-place`（临时目录、校验、乐观复核、`ReplaceFileW`/`os.replace`、`--keep-originals`） | ✅ |
| M5 | 运维闸门（下载中、云占位、垃圾文件、超长路径、重复 inode、按体积排序、`--limit`） | ✅ |
| M6 | 并行、watch 模式、HDR tonemap | ❌ 未开始 |

关于 M5 的说明：`cloud_placeholder` 与 `too_long_path` 已实现，在闸门代码里可见，但验收套件造不出 OneDrive 占位文件，也无法端到端验证超过 260 字符的路径，所以这两条靠代码审查而非通过项来保证。

---

## 13. 已做的决策

| 决策 | 选择 | 理由 |
| --- | --- | --- |
| 图片上限 | 长边 4096 | 只动超大的扫描件/渲染图 |
| 视频上限 | 高度 1440 | 4K → 1440p 去掉约 44% 像素，1080p 完全不动 |
| 原地模式不备份 | 允许，但文档推荐 `--keep-originals` | 不做家长式限制，需要时可逆 |
| 台账格式 | JSONL | 追加友好、崩溃友好，不必为每条重写全文件 |
| 复制模式是否用台账 | 用 | 否则压不动的文件每轮都被重压 |
| 台账 key | 路径 + mtime + 大小（哈希只存供巡检） | 没有额外的每轮 I/O 开销，又能识别同名替换 |
| HEVC/AV1/VP9 | 码率低于档位 1.2 倍就跳过 | 用 x264 重压它们通常是降级 |
| `not_smaller` 的后续 | 记为 `no_change`，不再重试 | 避免反复付出昂贵转码；需要重试就提升 `RULES_VERSION` |
| 原地模式改容器 | 拒绝（`container_incompatible`） | 原地替换必须沿用原文件名；复制模式会写成 `.mp4` 兄弟文件 |

---

## 14. 已知取舍

1. **重试“压不动”的文件**需要删掉它的台账记录或提升 `RULES_VERSION`；目前没有 `--retry-failed` / `--force`。
2. **原地模式处理不了 WebM/WMV/MPEG**（H.264/AAC 装不进这些容器），会被记为 `container_incompatible`；这类文件请用复制输出模式，或等将来的 VP9/Opus 路径。
3. **没有并行**：一万张图片就是一个接一个地起 caesiumclt 进程（进程启动开销占主导）。这是有意为之，因为台账与临时目录都建立在“单写者”前提上。
4. **Ctrl+C** 由 `KeyboardInterrupt` + `finally` 处理（清理临时目录、写报告；台账本来就每个文件都已落盘）；套件覆盖的是**硬杀**场景 —— 此时临时目录会有意留到下一次运行去清理。
5. **HDR 是跳过而不是 tonemap**，尚无有损的 HDR 转换路径。
6. **`head_tail_hash` 不在运行时校验**：同名同大小同 mtime 但内容不同的文件会被跳过。`--audit` 会报告这种不符；蓄意保留 mtime 的同尺寸篡改不在设计范围内。
7. **复制模式会忽略同名目录**：树中任何位置名为 `_compressed`/`_originals`/`.compress-state`/`.compress-tmp` 的目录都会被排除，这是有意设计。
8. 音频只在源编码无法复制进 MP4 时才重编为 AAC 128k；没有降混、也没有响度归一化。
9. **硬件编码在运行中途被降级时，`policy` 仍记录请求的编码器**：启动探针失败会同步改写 `policy`（见 §5.7），但"连续 3 个文件失败后才切换 x264"这条路径不会。影响仅限于：之后用另一种编码器跑时，那几个 `no_change` 文件会被重新评估一次（每个多一次探测），**不会重压任何已压缩文件**（`replaced` 是终态）。属于台账记账精度上的小瑕疵，不是正确性问题。

---

## 15. 后续事项

- **命名**：本目录 `files-*` 家族用的都是名词（`files-archiver`、`files-unarchiver`、`files-flatten`）。`files-compressor.py` 更贴合；`files-compress.py` 更像动词命令。以后改名会同时影响已生成的 `.cmd` 包装。
- [`scripts-mgr-README.md`](scripts-mgr-README.md) 的“使用”一节已加了调用示例，[`files-compress.cmd`](files-compress.cmd)（Windows 包装）也已就位，所以在 PATH 里直接敲 `files-compress <目录>` 即可。
- `scripts-mgr.py` 只扫描自己这一层（非递归），所以 [`tests/`](tests/) 对 `shim`/`ls` 不可见，不会为脚手架生成包装。
- 代码内的注释与 docstring 保持英文，模块开头的说明也是英文；若希望它们也一并中文化，改一处即可。

---

## 16. 压缩档位与“已压缩终态”（已实现，v0.3.0）

> 本节口径已全部落地：`--profile balanced|small|tiny`（默认 `balanced`）、`already_compressed` 终态、`policy` 指纹、首尾哈希兜底，验收见 §11.2 的 E 组。

### 16.1 两条不可动摇的规则

1. **已压缩的文件不再重复压缩**。台账里 `status: replaced` 的记录是**终态**：换档位不重压、`RULES_VERSION` 变化不重压、任何情况下都不会被重新压一遍。命中时记新 reason `already_compressed`（与 `already_processed` 分开，报告里一眼能看出“这是我自己压过的产物”）。
2. **档位只面向“没压过”的文件**。它是一个单向、只影响未来的力度选择，**不是“重做一遍”的开关** —— 明确不做“调档后重压全部文件”这种行为。

### 16.2 三档（没有 archive 档）

`balanced` 的数值**逐字节等于今天**，默认行为零变化；`small` 是中间档；`tiny` 是极端档，**不考虑质量，只求尽可能小**。

| 旋钮 | `balanced`（默认 = 现状） | `small` | `tiny`（极端小） |
| --- | --- | --- | --- |
| 入场阈值系数 | ×1.0 | ×0.7 | ×0.4 |
| 图片最小 / 最大字节 | 200 KiB / 12 MiB | 128 KiB / 12 MiB | 64 KiB / 12 MiB |
| 图片长边上限 | 4096 | 2560 | 1920 |
| 图片质量 `-q` | 82 | 72 | 58 |
| PNG 额外优化 | 默认（`--png-opt-level 3`） | `--png-opt-level 6` | `--png-opt-level 6 --zopfli` |
| JPEG 色度抽样 | `auto` | `auto` | `4:2:0` |
| 视频最小 / 最大字节 | 2 MiB / 8 GiB | 1 MiB / 8 GiB | 512 KiB / 8 GiB |
| 视频高度上限 | 1440 | 1080 | 720 |
| x264 `-crf` / `-preset` | 23 / medium | 26 / medium | 30 / slow |
| 音频 | 必要时 AAC 128k | 必要时 AAC 112k | 必要时 AAC 96k |
| 现代编码器跳过系数 | ×1.2 | ×1.5 | ×3.0（基本都尝试重压） |
| 最小节省（换文件身份的门槛） | 5% / 64 KiB | 3% / 32 KiB | 2% / 16 KiB |
| 视频超时系数（见 §16.5） | 0.25 秒/秒 | 0.25 秒/秒 | 0.5 秒/秒 |

三档在**所有轴上单调**：入场更宽 → 输出更狠 → 验收更宽松，因此容易解释、也容易用“排序性质”来测（§16.7）。

入场阈值的算法：`阈值 = clamp(基础阈值 × 系数, 该档最小字节, 该档最大字节)`，基础阈值仍是 §6 里的 bpp 表与码率档位。

### 16.3 台账语义（实现的核心改动）

| 记录 | 匹配条件 | 换档位后 | reason |
| --- | --- | --- | --- |
| `status: replaced` | 大小 == `output_size`，且（`mtime` 一致 **或** 首尾哈希一致） | **仍然跳过**（终态） | `already_compressed` |
| `status: no_change` | 大小 + `mtime` 一致，**且** `policy` 指纹一致 | 指纹不一致 → **重新评估**（文件没被改过，安全） | `already_processed` |

细则：

- **`policy` = 生效常量集合的短哈希**（`blake2b` 前 8 字节的十六进制）。写进每条 `no_change` 记录，同时出现在控制台摘要、`run.log` 运行头、`success.json`/`audit.json` 里，让每次运行的输出自描述。
- 指纹顺带解决“将来加进阶覆盖参数”的问题（比如 `--image-quality`、`--video-crf`）：覆盖值一并进指纹，不需要再维护“档位 × 覆盖”的映射表。
- **`head_tail_hash` 兜底（服务于规则 1）**：同步盘、备份工具经常只改 `mtime` 不改内容；若只认 `mtime`，已压缩文件会被当成新文件**再压一次**。所以 `replaced` 记录在“大小一致但 `mtime` 不同”时，额外比一次首尾 64 KiB 哈希；一致就继续跳过。读盘开销只在 `mtime` 不同时才发生。
- **`RULES_VERSION` 语义收窄**：它现在只让 `no_change` 失效（结构性变更时重评未被改动过的文件）。**不再让 `replaced` 失效** —— 否则改一个常量就会把全库已压缩文件重压一遍，违反规则 1。匹配时 `rules_version` 与 `policy` **两者都要校验**（验收时发现只校验 `policy` 会漏掉版本变更这一类）。
- **复制输出模式的差异**：该模式下源文件从未被改动，所以 `replaced` 记录**不参与匹配**，标记仍然是“输出文件存在”（否则用户清空 `_compressed/` 后重跑不会重建产物）；台账在该模式下只负责 `no_change` 记录。`already_compressed` 因此只出现在原地模式。
- 实现上是在现有的 `Ledger.match()` 里按 `status` 分流并返回 reason；`prune`（文件已不存在）与 `--dry-run` 只读的行为不变。

### 16.4 不随档位变化的东西（安全与能力闸门）

HDR（直接喂 x264 会发灰）、动画图（只留首帧＝丢内容）、AVIF/HEIC（caesiumclt 根本读不了）、位图字幕（容器装不下，只能丢并记录）、原地模式的容器兼容性 —— **三档一律跳过**。`tiny` 也不例外：**“尽可能小”不等于“允许损坏或丢内容”**。

同时被取消的两件事：

- **压缩代数计数器（generation）不再需要**：一个文件最多被压一次，“同一文件多次有损”这个风险由规则 1 直接消除了。
- **DQT 代际损失闸门继续不做**：它原本就是防“已 q82 的文件再压 q72”，既然不会重压，它只剩下“省掉一次注定被丢弃的编码”这点次要价值（§4.3 结论不变）。

### 16.5 预期表现与限制（提前知道，免得当成 bug）

- `tiny` 档对 HEVC/AV1/VP9 基本都会尝试重压（系数 3.0），其中**相当一部分会因“压完更大”被丢弃并记 `not_smaller`** —— 这是正确结果，代价只是一些 CPU。摘要里应把档位与这类计数一起显示，否则会像“跑了一大堆却什么都没省”。
- `tiny` 用 `-preset slow` 明显更慢，所以**视频超时必须随档位缩放**（0.25 → 0.5 秒/秒）。否则长视频会被误判为 `timeout`，白白失败。
- HDR 在 `tiny` 档**仍然跳过**（tonemap 未实现，属 M6）。
- 截图、线稿类图片在 `tiny` 档会出现肉眼可见的有损痕迹（q58，且可能被缩到 1920 长边）。这是该档位的定义，但首次使用建议先 `--dry-run` 看一眼计划。
- **档位是单向的**：先用 `tiny` 压过一批，之后想“其实我该保真”，那些文件不会自己回来 —— 唯一退路是 `--keep-originals` 的 `_originals/` 备份或原始文件本身。
- **库里已经存在的旧产物不会被波及**（`replaced` 永久有效），这符合规则 1。真要用另一档力度“重来一遍”，必须手动删除台账（`state.jsonl`）；工具不会自动做，也不提供 `--force`，这是有意的。

### 16.6 命令行与报告

| 参数 | 默认 | 说明 |
| --- | --- | --- |
| `--profile balanced\|small\|tiny` | `balanced` | `balanced` 的数值逐字节等于今天，默认行为零变化 |

- 控制台摘要加一段 `档位 balanced（policy 9f2c1a3b）`；`run.log` 运行头、`success.json`、`audit.json` 都带 `profile` 与 `policy`。
- `--audit --profile tiny` 回答的是“**还有多少没压过的文件能被压小**”，而不是“已压过的还能再小多少”。后者与规则 1 冲突，明确不做。

### 16.7 验收补充（已实现，见 §11.2 的 E 组）

1. `balanced` 档：原有 56 项全部照旧通过（默认行为零变化）。
2. 三档单调性：同一份夹具跑三棵全新树，节省额 `tiny > small > balanced`，图片长边 4096/2560/1920、视频高度 1440/1080/720。
3. **已压缩终态**：`balanced` 跑完 → 换 `tiny` 跑 → 已压缩文件全部记 `already_compressed` 且**哈希不变**。
4. **切换无害**：`tiny` 跑完 → 换 `balanced` 跑 → 不产生任何替换，文件哈希不变。
5. **指纹重评（走 A）**：`no_change` 记录在换档后被重新评估（用例里 `not_smaller` 的文件在换档后重新出现为 `not_smaller`，而不是 `already_processed`）。
6. **mtime 兜底**：只改已压缩文件的 `mtime`（内容不动，且改成足够旧的值以避开“下载中”闸门）→ 仍跳过并记 `already_compressed`。
7. **`RULES_VERSION` 提升不重压已压缩文件**：把台账的版本号改成 999 后巡检，6 个已压缩文件仍计入 `already_compressed`，只有 `no_change` 记录过期。
8. `tiny` 档的具体数值生效：6000×4000 → 1920 长边、4K → 720p，且 `run.log` 里能看到 `-q 58`、`-crf 30 -preset slow`、`--zopfli`、`--jpeg-chroma-subsampling 4:2:0`。
