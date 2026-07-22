至于 ffmpeg.exe 可以在 [Axiom FFmpeg](https://github.com/MattMcManis/Axiom/releases) 下载

#snippet  FFmpeg 批量截取文件夹下的视频封面
```bat
@echo off

setlocal enableextensions enabledelayedexpansion

rem 指定输入视频文件夹路径
set input_folder=videos\

rem 指定输出封面文件夹路径
set output_folder=videos\

rem 指定ffmpeg执行文件路径
set ffmpeg_path=".\ffmpeg.exe"

rem 检查输出文件夹是否存在，不存在则创建
if not exist %output_folder% (
mkdir %output_folder%
)

for %%f in (%input_folder%*.mp4) do (
rem 按照ffmpeg命令行参数规则编写命令
set command=%ffmpeg_path% -i "%%f" -ss 00:00:01 -vframes 1 -q:v 2  -an -y -f mjpeg "%output_folder%%%~nf.jpg"
echo run: !command!
!command!
)

echo.
echo #######################################
echo # #
echo # #           Complete
echo # #
echo #######################################
echo.

pause
```

FFmpeg tcp 推流
```bat
.\ffmpeg.exe -re -stream_loop -1 -i sd.mp4 -vcodec libvpx -b:v 3500k -r 25 -crf 10 -quality realtime -speed 16 -threads 8 -an -g 25 -f webm tcp://localhost:9090
```