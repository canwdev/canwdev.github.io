param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$bat,

    [Parameter(Position = 1)]
    [string]$icon,

    [string]$out,

    [switch]$console
)

$ErrorActionPreference = 'Stop'

function Find-Csc {
    $cmd = Get-Command csc.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    foreach ($path in @(
        "$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319\csc.exe",
        "$env:WINDIR\Microsoft.NET\Framework\v4.0.30319\csc.exe"
    )) {
        if (Test-Path $path) { return $path }
    }

    $found = Get-ChildItem "$env:WINDIR\Microsoft.NET" -Recurse -Filter csc.exe -ErrorAction SilentlyContinue |
        Sort-Object FullName -Descending |
        Select-Object -First 1
    if ($found) { return $found.FullName }

    throw 'csc.exe not found. Install .NET Framework.'
}

function Resolve-FullPath([string]$PathValue) {
    if ([IO.Path]::IsPathRooted($PathValue)) {
        return [IO.Path]::GetFullPath($PathValue)
    }
    return [IO.Path]::GetFullPath((Join-Path (Get-Location) $PathValue))
}

function Ensure-IconExtractor {
    if ('Bat2Exe.IconExtractor' -as [type]) { return }

    Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Runtime.InteropServices;

namespace Bat2Exe
{
    public static class IconExtractor
    {
        [DllImport("User32.dll", CharSet = CharSet.Unicode)]
        private static extern uint PrivateExtractIcons(
            string lpszFile, int nIconIndex, int cxIcon, int cyIcon,
            IntPtr[] phicon, int[] piconid, uint nIcons, uint flags);

        [DllImport("User32.dll", SetLastError = true)]
        private static extern bool DestroyIcon(IntPtr hIcon);

        public static void SaveHighResIcon(string sourcePath, string outIco)
        {
            int[] sizes = { 256, 48, 32, 16 };
            var bitmaps = new List<Bitmap>();

            try
            {
                foreach (int size in sizes)
                {
                    IntPtr[] icons = new IntPtr[1];
                    int[] ids = new int[1];
                    uint count = PrivateExtractIcons(sourcePath, 0, size, size, icons, ids, 1, 0);
                    if (count == 0 || icons[0] == IntPtr.Zero)
                        continue;

                    try
                    {
                        using (Icon icon = (Icon)Icon.FromHandle(icons[0]).Clone())
                        using (Bitmap src = icon.ToBitmap())
                        {
                            if (bitmaps.Exists(b => b.Width == src.Width && b.Height == src.Height))
                                continue;
                            bitmaps.Add(new Bitmap(src));
                        }
                    }
                    finally
                    {
                        DestroyIcon(icons[0]);
                    }
                }

                if (bitmaps.Count == 0)
                {
                    using (Icon fallback = Icon.ExtractAssociatedIcon(sourcePath))
                    {
                        if (fallback == null)
                            throw new InvalidOperationException("Failed to extract icon from: " + sourcePath);
                        using (var fs = File.Create(outIco))
                            fallback.Save(fs);
                    }
                    return;
                }

                // 优先保留最大尺寸，避免只有放大糊图
                bitmaps.Sort((a, b) => b.Width.CompareTo(a.Width));
                WriteBmpIco(outIco, bitmaps);
            }
            finally
            {
                foreach (Bitmap bmp in bitmaps)
                    bmp.Dispose();
            }
        }

        private static void WriteBmpIco(string path, List<Bitmap> bitmaps)
        {
            var images = new List<byte[]>();
            foreach (Bitmap bmp in bitmaps)
                images.Add(ToIcoImageData(bmp));

            using (var fs = File.Create(path))
            using (var bw = new BinaryWriter(fs))
            {
                bw.Write((ushort)0);
                bw.Write((ushort)1);
                bw.Write((ushort)bitmaps.Count);

                int offset = 6 + (16 * bitmaps.Count);
                for (int i = 0; i < bitmaps.Count; i++)
                {
                    int w = bitmaps[i].Width;
                    int h = bitmaps[i].Height;
                    byte[] data = images[i];
                    bw.Write((byte)(w >= 256 ? 0 : w));
                    bw.Write((byte)(h >= 256 ? 0 : h));
                    bw.Write((byte)0);
                    bw.Write((byte)0);
                    bw.Write((ushort)1);
                    bw.Write((ushort)32);
                    bw.Write(data.Length);
                    bw.Write(offset);
                    offset += data.Length;
                }

                foreach (byte[] data in images)
                    bw.Write(data);
            }
        }

        private static byte[] ToIcoImageData(Bitmap src)
        {
            using (var bmp = new Bitmap(src.Width, src.Height, PixelFormat.Format32bppArgb))
            using (var g = Graphics.FromImage(bmp))
            {
                g.Clear(Color.Transparent);
                g.DrawImage(src, 0, 0, src.Width, src.Height);

                int w = bmp.Width;
                int h = bmp.Height;
                int xorStride = w * 4;
                int andStride = ((w + 31) / 32) * 4;
                int xorSize = xorStride * h;
                int andSize = andStride * h;

                var header = new byte[40];
                BitConverter.GetBytes(40).CopyTo(header, 0);
                BitConverter.GetBytes(w).CopyTo(header, 4);
                BitConverter.GetBytes(h * 2).CopyTo(header, 8);
                BitConverter.GetBytes((short)1).CopyTo(header, 12);
                BitConverter.GetBytes((short)32).CopyTo(header, 14);
                BitConverter.GetBytes(xorSize + andSize).CopyTo(header, 20);

                var xor = new byte[xorSize];
                var data = bmp.LockBits(
                    new Rectangle(0, 0, w, h),
                    ImageLockMode.ReadOnly,
                    PixelFormat.Format32bppArgb);
                try
                {
                    for (int y = 0; y < h; y++)
                    {
                        IntPtr row = data.Scan0 + ((h - 1 - y) * data.Stride);
                        Marshal.Copy(row, xor, y * xorStride, xorStride);
                    }
                }
                finally
                {
                    bmp.UnlockBits(data);
                }

                var and = new byte[andSize];
                var ms = new MemoryStream(header.Length + xor.Length + and.Length);
                ms.Write(header, 0, header.Length);
                ms.Write(xor, 0, xor.Length);
                ms.Write(and, 0, and.Length);
                return ms.ToArray();
            }
        }
    }
}
'@
}

function Get-IconFile([string]$IconPath, [string]$TempIco) {
    $ext = [IO.Path]::GetExtension($IconPath).ToLowerInvariant()
    if ($ext -eq '.ico') {
        return (Resolve-FullPath $IconPath)
    }

    Ensure-IconExtractor
    [Bat2Exe.IconExtractor]::SaveHighResIcon($IconPath, $TempIco)
    return $TempIco
}

$batPath = Resolve-FullPath $bat
if (-not (Test-Path -LiteralPath $batPath)) {
    throw "Bat not found: $batPath"
}

if (-not $out) {
    $out = [IO.Path]::ChangeExtension($batPath, '.exe')
}
else {
    $out = Resolve-FullPath $out
}

$workDir = Join-Path $env:TEMP ("bat2exe_" + [guid]::NewGuid().ToString('n'))
New-Item -ItemType Directory -Path $workDir | Out-Null

try {
    $batBytes = [IO.File]::ReadAllBytes($batPath)
    $batB64 = [Convert]::ToBase64String($batBytes)
    $csPath = Join-Path $workDir 'wrapper.cs'
    $createNoWindow = if ($console) { 'false' } else { 'true' }

    @"
using System;
using System.Diagnostics;
using System.IO;
using System.Text;

internal static class Program
{
    private static readonly string BatBase64 = "$batB64";

    private static string Quote(string value)
    {
        return "\"" + value.Replace("\"", "\"\"") + "\"";
    }

    private static void Main(string[] args)
    {
        string tempBat = Path.Combine(Path.GetTempPath(), "bat2exe_" + Guid.NewGuid().ToString("n") + ".bat");
        File.WriteAllBytes(tempBat, Convert.FromBase64String(BatBase64));
        try
        {
            var argLine = new StringBuilder();
            foreach (string arg in args)
            {
                argLine.Append(' ');
                argLine.Append(Quote(arg));
            }

            // 用 call 转发参数，避免 cmd /c 引号剥离导致“打开方式”丢路径
            string comspec = Environment.GetEnvironmentVariable("ComSpec");
            if (string.IsNullOrEmpty(comspec))
                comspec = "cmd.exe";

            var psi = new ProcessStartInfo
            {
                FileName = comspec,
                Arguments = "/d /c call " + Quote(tempBat) + argLine,
                UseShellExecute = false,
                CreateNoWindow = $createNoWindow,
            };

            using (Process p = Process.Start(psi))
            {
                if (p != null)
                    p.WaitForExit();
            }
        }
        finally
        {
            try { File.Delete(tempBat); } catch { }
        }
    }
}
"@ | Set-Content -LiteralPath $csPath -Encoding ASCII

    $cscArgs = @('/nologo', '/optimize+', "/out:$out", $csPath)
    if ($console) {
        $cscArgs = @('/target:exe') + $cscArgs
    }
    else {
        $cscArgs = @('/target:winexe') + $cscArgs
    }

    if ($icon) {
        $iconPath = Resolve-FullPath $icon
        if (-not (Test-Path -LiteralPath $iconPath)) {
            throw "Icon not found: $iconPath"
        }
        $tempIco = Join-Path $workDir 'app.ico'
        $iconFile = Get-IconFile $iconPath $tempIco
        $cscArgs = @("/win32icon:$iconFile") + $cscArgs
        Write-Host "Icon: $iconPath"
    }

    $csc = Find-Csc
    Write-Host "Bat : $batPath"
    Write-Host "Out : $out"
    Write-Host "CSC : $csc"
    & $csc @cscArgs
    if ($LASTEXITCODE -ne 0) {
        throw 'Compile failed.'
    }

    Write-Host "Done: $out"
}
finally {
    Remove-Item -LiteralPath $workDir -Recurse -Force -ErrorAction SilentlyContinue
}
