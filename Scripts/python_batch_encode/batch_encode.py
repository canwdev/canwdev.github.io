import os
import subprocess
import shutil
import time
from datetime import timedelta

# ==================== 配置区域 ====================
# 1. 扫描的源目录（会递归查找该目录下所有子文件夹里的视频文件）
SOURCE_DIR = r"K:\电影\豆瓣电影评分前100部"  

# 2. 目标输出目录（建议先和源目录分开，确保安全；若想原地替换，可设为相同）
OUTPUT_DIR = r".\video_out" 

# 3. HandBrakeCLI.exe 的绝对路径
HANDBRAKE_CLI = r"..\HandBrakeCLI.exe"

# 4. 从 HandBrake GUI 导出的预设 JSON 文件路径
PRESET_JSON_PATH = r".\720p-h264.json"

# 5. 预设名称（需与 JSON 中的 PresetName 一致）
PRESET_NAME = "720p-h264"

# 6. 支持的文件后缀
SUPPORTED_EXTENSIONS = ['.mp4', '.mkv']

# ==================================================

def scan_and_convert():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # 统计信息
    total_files = 0
    success_files = 0
    skip_files = 0
    fail_files = 0
    start_time = time.time()

    # 递归遍历目录
    for root, dirs, files in os.walk(SOURCE_DIR):
        for file in files:
            # 检查是否匹配支持的后缀（不区分大小写）
            file_lower = file.lower()
            if any(file_lower.endswith(ext) for ext in SUPPORTED_EXTENSIONS):
                total_files += 1
                input_path = os.path.join(root, file)
                
                # 保持原有的子目录结构输出
                relative_path = os.path.relpath(root, SOURCE_DIR)
                target_output_dir = os.path.join(OUTPUT_DIR, relative_path)
                if not os.path.exists(target_output_dir):
                    os.makedirs(target_output_dir)
                
                # 构建输出文件名，将后缀改为 .mp4
                output_file_name = os.path.splitext(file)[0] + ".mp4"
                output_path = os.path.join(target_output_dir, output_file_name)
                
                # 如果已存在转换完成的文件则跳过
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    print(f"⏭️ 已存在，跳过: {output_file_name}")
                    skip_files += 1
                    continue
                
                # 临时文件，防止转换中断留下不完整文件；如有残留则清理
                temp_path = output_path + ".tmp"
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                
                print(f"\n" + "="*60)
                print(f"正在处理: {input_path}")
                print(f"临时输出: {temp_path}")
                print("="*60 + "\n")
                
                # 构建 HandBrakeCLI 命令
                cmd = [
                    HANDBRAKE_CLI,
                    "-i", input_path,
                    "-o", temp_path,
                    "--preset-import-file", PRESET_JSON_PATH,
                    "--preset", PRESET_NAME
                ]
                
                try:
                    # 执行转码并等待其结束
                    result = subprocess.run(cmd, check=True)
                    
                    # 校验：检查临时文件是否存在且大小大于 0
                    if result.returncode == 0 and os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                        # 转码成功后重命名为最终文件名
                        os.rename(temp_path, output_path)
                        print(f"🎉 转码成功: {output_file_name}")
                        success_files += 1
                    else:
                        print(f"⚠️ 警告: {file} 转码可能未成功完整完成。")
                        fail_files += 1
                        
                except subprocess.CalledProcessError as e:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    print(f"❌ 错误: {file} 转码失败。错误信息: {e}")
                    fail_files += 1
                    print("🛑 检测到错误，终止后续任务。")
                    break  # 改为 break，跳出当前循环
                except Exception as e:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    print(f"❌ 发生未知异常: {e}")
                    fail_files += 1
                    print("🛑 检测到错误，终止后续任务。")
                    break  # 改为 break，跳出当前循环
            else:
                continue
        else:
            # 如果内层循环正常结束（没有break），继续外层循环
            continue
        # 如果内层循环被break，则外层循环也break
        break

    # 计算耗时
    elapsed_time = time.time() - start_time
    hours = int(elapsed_time // 3600)
    minutes = int((elapsed_time % 3600) // 60)
    seconds = int(elapsed_time % 60)
    time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    # 输出统计信息
    print("\n" + "="*60)
    print("📊 转换任务统计")
    print("="*60)
    print(f"总文件数: {total_files}")
    print(f"转换成功: {success_files}")
    print(f"跳过文件: {skip_files}")
    print(f"失败文件: {fail_files}")
    print(f"总耗时: {time_str}")
    print("="*60 + "\n")

if __name__ == "__main__":
    print("🚀 HandBrake 自动化递归批量转码脚本已启动...")
    scan_and_convert()
    print("🏁 所有任务处理完毕！")
    # 添加当前时间输出
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"🕐 当前时间: {current_time}")