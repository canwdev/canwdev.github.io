至于 ffmpeg.exe 可以在 [Axiom FFmpeg](https://github.com/MattMcManis/Axiom/releases) 下载

j截取封面.bat
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