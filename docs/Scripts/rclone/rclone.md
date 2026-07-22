> 非常好用的命令行文件同步工具、类似 rsync 但是跨平台支持，并且支持多种网盘
> https://rclone.org/

使用示例：

同步本地文件到目标文件（覆盖并删除目标），从 `E:\SoftwarePacks\` 到 `I:\SoftwarePacks\`
- `--track-renames` 检测目标文件的重命名（本地或目标有重命名的文件直接移动，而不是删除后重新复制）
- `--progress` 打印进度
- `-v` 显示更多日志

```
rclone sync E:\SoftwarePacks\ I:\SoftwarePacks\ --track-renames --progress -v
```