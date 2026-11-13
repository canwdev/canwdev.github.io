#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序清单 —— 本地服务器 + 静态生成

默认启动服务器（自动挑端口，每次刷新重新读取 json 并生成页面，页面带「运行」按钮）：

    python programs_server.py
    python programs_server.py --port 8080
    python programs_server.py --no-open

只生成静态 HTML（无运行按钮，可离线分发）：

    python programs_server.py --generate
    python programs_server.py --generate -o programs.html

只依赖标准库。所有路径相对 json 所在目录。
"""

from __future__ import annotations

import argparse
import html
import hashlib
import json
import os
import shutil
import socket
import struct
import subprocess
import sys
import threading
import webbrowser
import zlib
from datetime import datetime
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse

DEFAULT_JSON = "programs.json"
DEFAULT_OUT = "programs.html"
PACKAGES = "packages"


# ---------------------------------------------------------------- 工具

def human_size(num: int | None) -> str:
    if not num or num <= 0:
        return "—"
    size = float(num)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.0f} B" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return "—"


def fmt_ts(ts) -> str:
    """毫秒级时间戳（Date.now() 风格）→ 本地日期；兼容秒级。"""
    try:
        v = int(ts)
    except (TypeError, ValueError):
        return ""
    if v > 10 ** 11:
        v /= 1000.0
    try:
        return datetime.fromtimestamp(v).strftime("%Y-%m-%d")
    except (ValueError, OSError, OverflowError):
        return ""


def file_size(rel: str, base: Path) -> int | None:
    if rel and (base / rel).is_file():
        try:
            return (base / rel).stat().st_size
        except OSError:
            return None
    return None


def esc(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def safe_url(value: str) -> str:
    value = (value or "").strip()
    return value if value.lower().startswith(("http://", "https://")) else ""


def load_json(json_path: Path) -> dict:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    if not isinstance(data.get("programs"), list):
        raise ValueError("缺少 programs 数组")
    return data


# ---------------------------------------------------------------- 图标提取
#
# 用 Windows 自带的 PrivateExtractIconsW 直接取 256px 图标，再自己编码 PNG，
# 全程标准库，不需要 Pillow。.msi / .zip 没有图标资源，会落到首字母占位块。

ICONS = "icons"
_icon_api_cache = {}


def _icon_api():
    """首次调用时构建 ctypes 结构体并声明 argtypes（不声明会把 64 位句柄当 int）。"""
    if _icon_api_cache:
        return _icon_api_cache
    import ctypes
    from ctypes import wintypes

    class ICONINFO(ctypes.Structure):
        _fields_ = [("fIcon", wintypes.BOOL), ("xHotspot", wintypes.DWORD),
                    ("yHotspot", wintypes.DWORD), ("hbmMask", wintypes.HBITMAP),
                    ("hbmColor", wintypes.HBITMAP)]

    class BITMAP(ctypes.Structure):
        _fields_ = [("bmType", wintypes.LONG), ("bmWidth", wintypes.LONG),
                    ("bmHeight", wintypes.LONG), ("bmWidthBytes", wintypes.LONG),
                    ("bmPlanes", wintypes.WORD), ("bmBitsPixel", wintypes.WORD),
                    ("bmBits", ctypes.c_void_p)]

    class BIH(ctypes.Structure):
        _fields_ = [("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG),
                    ("biHeight", wintypes.LONG), ("biPlanes", wintypes.WORD),
                    ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                    ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", wintypes.LONG),
                    ("biYPelsPerMeter", wintypes.LONG), ("biClrUsed", wintypes.DWORD),
                    ("biClrImportant", wintypes.DWORD)]

    user32, gdi32 = ctypes.windll.user32, ctypes.windll.gdi32
    user32.PrivateExtractIconsW.argtypes = [
        wintypes.LPCWSTR, ctypes.c_int, ctypes.c_int, ctypes.c_int,
        ctypes.POINTER(wintypes.HICON), ctypes.POINTER(wintypes.UINT),
        wintypes.UINT, wintypes.UINT]
    user32.PrivateExtractIconsW.restype = wintypes.UINT
    user32.GetIconInfo.argtypes = [wintypes.HICON, ctypes.POINTER(ICONINFO)]
    user32.GetIconInfo.restype = wintypes.BOOL
    user32.DestroyIcon.argtypes = [wintypes.HICON]
    user32.GetDC.argtypes = [wintypes.HWND]
    user32.GetDC.restype = wintypes.HDC
    user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
    gdi32.GetObjectW.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p]
    gdi32.GetObjectW.restype = ctypes.c_int
    gdi32.GetDIBits.argtypes = [wintypes.HDC, wintypes.HBITMAP, wintypes.UINT,
                                wintypes.UINT, ctypes.c_void_p,
                                ctypes.c_void_p, wintypes.UINT]
    gdi32.GetDIBits.restype = ctypes.c_int

    _icon_api_cache.update(ctypes=ctypes, wintypes=wintypes, user32=user32,
                           gdi32=gdi32, ICONINFO=ICONINFO, BITMAP=BITMAP, BIH=BIH)
    return _icon_api_cache


def _icon_to_rgba(hicon):
    api = _icon_api()
    ctypes, wintypes = api["ctypes"], api["wintypes"]
    user32, gdi32 = api["user32"], api["gdi32"]

    info = api["ICONINFO"]()
    if not user32.GetIconInfo(hicon, ctypes.byref(info)):
        return None
    bmp = api["BITMAP"]()
    gdi32.GetObjectW(info.hbmColor, ctypes.sizeof(bmp), ctypes.byref(bmp))
    w, h = bmp.bmWidth, bmp.bmHeight
    if w <= 0 or h <= 0:
        return None

    hdc = user32.GetDC(None)
    bih = api["BIH"]()
    bih.biSize = ctypes.sizeof(bih)
    bih.biWidth = w
    bih.biHeight = -h                      # 负高度 = 自上而下
    bih.biPlanes = 1
    bih.biBitCount = 32
    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(hdc, info.hbmColor, 0, h, buf, ctypes.byref(bih), 0)
    user32.ReleaseDC(None, hdc)

    px = bytearray(buf.raw)
    red = px[0::4]
    px[0::4], px[2::4] = px[2::4], red   # BGRA -> RGBA
    if not any(px[3::4]):                  # 老图标没有 alpha 通道，补成不透明
        px[3::4] = b"\xff" * (w * h)
    return w, h, bytes(px)


def _write_png(path: Path, w: int, h: int, rgba: bytes) -> None:
    raw = b"".join(b"\x00" + rgba[y * w * 4:(y + 1) * w * 4] for y in range(h))

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw, 9))
           + chunk(b"IEND", b""))
    path.write_bytes(png)


def icon_rel_path(rel: str) -> str:
    """图标文件名按源文件路径哈希，避开中文和特殊字符。"""
    return ICONS + "/" + hashlib.sha1(rel.encode("utf-8")).hexdigest()[:16] + ".png"


def ensure_icon(rel: str, base: Path) -> str:
    """保证图标存在且不旧于源文件，返回相对路径；拿不到就返回空串。"""
    if os.name != "nt" or not rel:
        return ""
    src = base / rel
    try:
        if not src.is_file():
            return ""
        out = base / icon_rel_path(rel)
        if out.is_file() and out.stat().st_mtime >= src.stat().st_mtime:
            return icon_rel_path(rel)

        api = _icon_api()
        ctypes, wintypes = api["ctypes"], api["wintypes"]
        user32 = api["user32"]
        hicon = wintypes.HICON()
        got = user32.PrivateExtractIconsW(str(src), 0, 256, 256,
                                          ctypes.byref(hicon), None, 1, 0)
        if got <= 0 or not hicon:
            return ""
        try:
            rgba = _icon_to_rgba(hicon)
        finally:
            user32.DestroyIcon(hicon)
        if not rgba:
            return ""
        out.parent.mkdir(exist_ok=True)
        _write_png(out, *rgba)
        return icon_rel_path(rel)
    except (OSError, ValueError, AttributeError):
        return ""


CSS = """
:root{
  --bg:#f7fcff; --panel:#fff; --tint:#e6f4ff; --line:#dcefff; --line2:#bfe2f7;
  --tx:#181919; --tx2:#4d6273; --tx3:#8ba6b8;
  --ac:#0099ff; --ac-deep:#0077cc; --ac-soft:#e6f4ff; --radius:12px;
  --shadow:0 1px 2px rgba(0,119,204,.05), 0 10px 26px -16px rgba(0,119,204,.16);
}
*{box-sizing:border-box}
body{
  margin:0; background:var(--bg); color:var(--tx);
  font:14px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei","PingFang SC",sans-serif;
  -webkit-font-smoothing:antialiased;
}
.wrap{max-width:1000px;margin:0 auto;padding:40px 24px 80px}

h1{font-size:24px;font-weight:650;letter-spacing:-.02em;margin:0 0 12px}
.stats{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:26px}
.stat{background:#fff;border:1px solid var(--line);border-radius:999px;padding:4px 12px;font-size:12.5px;color:var(--tx2)}
.stat b{color:var(--tx);font-weight:600;margin-left:4px}

.toolbar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:22px}
.search{flex:1 1 240px;position:relative}
.search input{
  width:100%;padding:9px 13px 9px 33px;border:1px solid var(--line2);border-radius:10px;
  background:#fff;color:var(--tx);font-size:13.5px;outline:none;transition:.15s;
}
.search input:focus{border-color:var(--ac);box-shadow:0 0 0 3px var(--ac-soft)}
.search svg{position:absolute;left:11px;top:50%;transform:translateY(-50%);opacity:.4}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{
  border:1px solid var(--line2);background:#fff;color:var(--tx2);padding:6px 12px;
  border-radius:999px;font-size:12.5px;cursor:pointer;transition:.15s;font-family:inherit;
}
.chip:hover{border-color:var(--ac);color:var(--ac)}
.chip.on{background:var(--ac);border-color:var(--ac);color:#fff;font-weight:500}

.card{
  position:relative;
  background:#fff;border:1px solid var(--line);border-radius:var(--radius);
  padding:14px 16px;margin-bottom:9px;box-shadow:var(--shadow);
  display:flex;gap:13px;align-items:flex-start;transition:border-color .15s;
}
.card:hover{border-color:var(--line2)}
.ico{
  flex:0 0 34px;width:34px;height:34px;border-radius:9px;
  display:flex;align-items:center;justify-content:center;background:var(--tint);
}
.ico img{width:30px;height:30px;object-fit:contain;display:block}
.ico.ph{font-size:15px;font-weight:650;color:var(--ac);background:var(--ac-soft)}
.idx{
  position:absolute;right:16px;top:10px;
  font-size:19px;font-weight:700;line-height:1;letter-spacing:-.03em;
  color:#aec4d4;user-select:none;
}
.body{flex:1 1 auto;min-width:0}
.row{display:flex;flex-wrap:wrap;align-items:center;gap:8px;padding-right:46px}
.name{font-size:15px;font-weight:600;letter-spacing:-.01em}
.en{font-size:12px;color:var(--tx3)}
.badge{
  font-size:11px;padding:2px 7px;border-radius:6px;border:1px solid var(--line);
  color:var(--tx2);background:#f6fcff;white-space:nowrap;
}
.badge.p{color:var(--ac);background:var(--ac-soft);border-color:transparent}
.badge.g{color:#4a7a94;background:#eef8ff;border-color:transparent}

.fileline{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin-top:9px}
.file{
  background:var(--tint);border:1px solid var(--line);border-radius:7px;padding:2px 8px;
  font-size:12px;color:var(--tx);word-break:break-all;
}
.acts{display:flex;gap:6px;margin-left:auto;flex-wrap:wrap}
a.act,button.act{
  display:inline-flex;align-items:center;justify-content:center;text-decoration:none;
  border:1px solid var(--line2);background:#fff;color:var(--tx2);padding:5px 10px;
  border-radius:8px;font-size:12px;transition:.15s;font-family:inherit;cursor:pointer;
  line-height:1.5;
}
a.act:hover,button.act:hover{border-color:var(--ac);color:var(--ac)}
a.act.primary,button.act.primary{background:var(--ac);border-color:var(--ac);color:#fff}
a.act.primary:hover,button.act.primary:hover{color:#fff;filter:brightness(1.06)}
button.act:disabled{opacity:.55;cursor:default}
button.act.primary:disabled{filter:none}

.meta{display:flex;flex-wrap:wrap;gap:14px;font-size:12.5px;color:var(--tx2);margin-top:9px}
.meta b{color:var(--tx3);font-weight:500;margin-right:4px}
.empty-tip{text-align:center;color:var(--tx3);padding:56px 0;font-size:13px}
.toast{
  position:fixed;left:50%;bottom:26px;transform:translate(-50%,12px);background:#0f3448;
  color:#fff;padding:8px 15px;border-radius:9px;font-size:13px;opacity:0;
  pointer-events:none;transition:.2s;z-index:9;max-width:80vw;
}
.toast.on{opacity:1;transform:translate(-50%,0)}

@media (max-width:640px){
  .wrap{padding:24px 14px 60px}
  h1{font-size:20px}
  .card{flex-wrap:wrap}
  .fileline .acts{margin-left:0;width:100%}
}
"""

JS = """
(function(){
  var input=document.getElementById('q'),
      chips=[].slice.call(document.querySelectorAll('.chip')),
      cards=function(){return [].slice.call(document.querySelectorAll('.card'))},
      empty=document.getElementById('empty'),
      cat='all';

  function apply(){
    var q=input.value.trim().toLowerCase(), total=0;
    cards().forEach(function(c){
      var hit=(cat==='all'||c.dataset.cat===cat)&&(!q||(c.dataset.search||'').indexOf(q)>-1);
      c.style.display=hit?'':'none';
      if(hit) total++;
    });
    empty.style.display=total?'none':'';
  }

  input.addEventListener('input',apply);
  chips.forEach(function(ch){
    ch.addEventListener('click',function(){
      chips.forEach(function(x){x.classList.remove('on')});
      ch.classList.add('on');
      cat=ch.dataset.cat;
      apply();
    });
  });

  var toast=document.getElementById('toast'),timer;
  function flash(msg){
    toast.textContent=msg;
    toast.classList.add('on');
    clearTimeout(timer);
    timer=setTimeout(function(){toast.classList.remove('on')},2200);
  }

  [].slice.call(document.querySelectorAll('[data-install]')).forEach(function(b){
    b.addEventListener('click',function(){
      var file=b.dataset.install,name=b.dataset.name||file;
      b.disabled=true;
      flash('正在运行 '+name+' …');
      fetch('/install',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({file:file})
      }).then(function(r){return r.json()}).then(function(d){
        flash(d.message||(d.ok?'已启动 '+name:'启动失败'));
        b.disabled=false;
      }).catch(function(){
        flash('启动失败：服务无响应');
        b.disabled=false;
      });
    });
  });

  apply();
})();
"""


# ---------------------------------------------------------------- 页面

def render_card(index: int, prog: dict, base: Path, show_cat: bool,
                server: bool = False, install: bool = False) -> str:
    rel = (prog.get("file") or "").strip()
    name_cn = prog.get("name_cn") or prog.get("name") or "未命名"
    name_en = prog.get("name") or ""
    version = prog.get("version") or ""
    platform = prog.get("platform") or ""
    category = (prog.get("category") or "其他").strip() or "其他"
    source = prog.get("source_site") or ""
    page_url = safe_url(prog.get("page_url") or "")

    exists = bool(rel) and (base / rel).is_file()
    size = file_size(rel, base) or prog.get("size_bytes")

    badges = []
    if version:
        badges.append(f'<span class="badge p">{esc(version)}</span>')
    if platform:
        badges.append(f'<span class="badge">{esc(platform)}</span>')
    if show_cat:
        badges.append(f'<span class="badge g">{esc(category)}</span>')

    acts = []
    if exists:
        href = f"/download?file={quote(rel)}" if server else quote(rel)
        acts.append(f'<a class="act" href="{esc(href)}" target="_blank" rel="noopener">本地下载</a>')
    if page_url:
        acts.append(f'<a class="act" href="{esc(page_url)}" target="_blank" rel="noopener">官网下载</a>')
    if install and exists:
        acts.append(
            f'<button class="act primary" data-install="{esc(rel)}" '
            f'data-name="{esc(name_cn)}">运行</button>'
        )

    file_html = f'<span class="file">{esc(rel)}</span>' if rel else ""

    metas = []
    if source:
        metas.append(f"<span><b>来源</b>{esc(source)}</span>")
    metas.append(f"<span><b>体积</b>{esc(human_size(size))}</span>")
    updated = fmt_ts(prog.get("updated_at"))
    if updated:
        metas.append(f"<span><b>更新</b>{esc(updated)}</span>")

    hay = " ".join(x for x in (name_cn, name_en, version, platform, category, source, rel) if x).lower()
    en_html = f'<span class="en">{esc(name_en)}</span>' if name_en and name_en != name_cn else ""
    acts_html = f'<div class="acts">{"".join(acts)}</div>' if acts else ""

    icon = ensure_icon(rel, base)
    if icon:
        icon_html = f'<div class="ico"><img src="{esc(icon)}" alt="" loading="lazy"></div>'
    else:
        letter = esc((name_cn or "?")[0].upper())
        icon_html = f'<div class="ico ph">{letter}</div>'

    return f"""
      <article class="card" data-search="{esc(hay)}" data-cat="{esc(category)}">
        <span class="idx">#{index}</span>
        {icon_html}
        <div class="body">
          <div class="row">
            <span class="name">{esc(name_cn)}</span>
            {en_html}
            {''.join(badges)}
          </div>
          <div class="fileline">{file_html}{acts_html}</div>
          <div class="meta">{''.join(metas)}</div>
        </div>
      </article>"""


def build(data: dict, json_path: Path, server: bool = False,
          install: bool = False) -> tuple[str, dict]:
    base = json_path.parent
    programs = data.get("programs") or []
    meta = data.get("meta") or {}

    cats: list[str] = []
    for p in programs:
        c = (p.get("category") or "其他").strip() or "其他"
        if c not in cats:
            cats.append(c)

    total = 0
    for p in programs:
        rel = (p.get("file") or "").strip()
        total += file_size(rel, base) or (p.get("size_bytes") or 0)

    cards = "\n".join(
        render_card(i, p, base, True, server=server, install=install)
        for i, p in enumerate(programs, 1)
    )
    body = f'\n    <section class="group">\n      {cards}\n    </section>'

    chips = ['<button class="chip on" data-cat="all">全部</button>']
    chips += [f'<button class="chip" data-cat="{esc(c)}">{esc(c)}</button>' for c in cats]

    title = meta.get("title") or "程序安装清单"
    date = fmt_ts(meta.get("timestamp")) or datetime.now().strftime("%Y-%m-%d")

    page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
  <h1>{esc(title)}</h1>
  <div class="stats">
    <span class="stat">程序<b>{len(programs)}</b></span>
    <span class="stat">总体积<b>{human_size(total)}</b></span>
    <span class="stat">更新<b>{esc(date)}</b></span>
  </div>

  <div class="toolbar">
    <div class="search">
      <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><circle cx="7" cy="7" r="4.5"/><path d="M10.5 10.5L14 14"/></svg>
      <input id="q" type="search" placeholder="搜索" autocomplete="off" spellcheck="false">
    </div>
    <div class="chips">{''.join(chips)}</div>
  </div>

  {body}

  <div class="empty-tip" id="empty" style="display:none">没有匹配的程序</div>
</div>
<div class="toast" id="toast"></div>
<script>{JS}</script>
</body>
</html>
"""
    return page, {"total": len(programs), "size": total, "cats": cats}


# ---------------------------------------------------------------- 运行文件

def resolve_package(rel: str, base: Path) -> tuple[Path | None, str]:
    """把相对路径解析到 packages 内的真实文件，越界/不存在都返回错误。"""
    rel = (rel or "").strip().replace("\\", "/")
    if not rel:
        return None, "缺少文件参数"
    pkg = (base / PACKAGES).resolve()
    target = (base / rel).resolve()
    if not str(target).startswith(str(pkg) + os.sep):
        return None, "非法路径"
    if not target.is_file():
        return None, f"文件不存在：{rel}"
    return target, ""


def launch(rel: str, base: Path) -> tuple[bool, str]:
    """校验并用系统默认程序打开 packages 下的文件。返回 (成功, 提示)。"""
    target, err = resolve_package(rel, base)
    if target is None:
        return False, err

    try:
        if os.name == "nt":
            os.startfile(str(target))  # noqa: S606 — 本地可信环境，交给系统关联
        else:
            subprocess.Popen(
                ["open" if sys.platform == "darwin" else "xdg-open", str(target)],
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
    except OSError as exc:
        return False, f"启动失败：{exc}"
    return True, f"已启动 {target.name}"


# ---------------------------------------------------------------- HTTP

class Handler(BaseHTTPRequestHandler):
    server_version = "ProgramList/2.0"

    # 渲染结果缓存：{(json 路径, 是否本机): (指纹, html 字节, info)}
    # 本机和远程页面按钮不同，必须分开存两份
    _cache: dict = {}
    _cache_lock = threading.Lock()

    def __init__(self, *args, json_path: Path, host: str, **kwargs):
        self.json_path = json_path
        self.base = json_path.parent
        self.host = host
        super().__init__(*args, **kwargs)

    def log_message(self, fmt, *args):
        sys.stdout.write("  %s\n" % (fmt % args))

    def _send(self, code: int, body: bytes, ctype: str):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _json(self, code: int, payload: dict):
        self._send(code, json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                   "application/json; charset=utf-8")

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/download":
            self._download(parsed.query)
            return
        if path.startswith("/" + ICONS + "/"):
            self._serve_icon(path)
            return
        if path not in ("/", "/index.html"):
            self._send(404, "404".encode(), "text/plain; charset=utf-8")
            return

        local = self._client_is_local()
        fingerprint = self._json_fingerprint()
        key = (str(self.json_path), local)

        # json 没变就直接吐缓存：不读盘、不重算体积、不重渲染
        with Handler._cache_lock:
            cached = Handler._cache.get(key)
        if fingerprint and cached and cached[0] == fingerprint:
            self._send(200, cached[1], "text/html; charset=utf-8")
            print(f"  缓存 ← {self.client_address[0]}（{self.json_path.name} 未变更）")
            return

        try:
            data = load_json(self.json_path)
        except FileNotFoundError:
            self._send(500, "programs.json 不存在".encode(), "text/plain; charset=utf-8")
            return
        except (json.JSONDecodeError, ValueError) as exc:
            msg = f"programs.json 读取失败：{exc}"
            self._send(500, msg.encode(), "text/plain; charset=utf-8")
            return

        page, info = build(data, self.json_path, server=True, install=local)
        body = page.encode("utf-8")
        with Handler._cache_lock:
            Handler._cache[key] = (fingerprint, body, info)
        self._send(200, body, "text/html; charset=utf-8")
        print(f"  重新生成 ← {self.client_address[0]} · {info['total']} 项 · {human_size(info['size'])}"
              f"{'' if local else ' · 远程只读'}")

    def _json_fingerprint(self):
        """(mtime_ns, size)：文件没动过就当内容没变，零成本。"""
        try:
            st = self.json_path.stat()
            return (st.st_mtime_ns, st.st_size)
        except OSError:
            return None

    # --- 权限：只有本机（127.0.0.1 / localhost）才展示并允许运行
    def _client_is_local(self) -> bool:
        if self.client_address[0] not in ("127.0.0.1", "::1"):
            return False
        host = (self.headers.get("Host") or "").strip().lower()
        if host.startswith("["):                 # [::1]:8080
            host = host[1:].split("]")[0]
        else:
            host = host.split(":")[0]
        return host in ("", "127.0.0.1", "localhost")

    # --- 图标（只允许 icons/ 下的 png）
    def _serve_icon(self, path: str) -> None:
        name = path[len("/" + ICONS + "/"):]
        if not name or "/" in name or "\\" in name or name.startswith("."):
            self._send(404, b"404", "text/plain; charset=utf-8")
            return
        try:
            data = (self.base / ICONS / name).read_bytes()
        except OSError:
            self._send(404, b"404", "text/plain; charset=utf-8")
            return
        self._send(200, data, "image/png")

    # --- 下载本地文件
    def _download(self, query: str) -> None:
        rel = (parse_qs(query).get("file") or [""])[0]
        target, err = resolve_package(rel, self.base)
        if target is None:
            self._send(404, err.encode(), "text/plain; charset=utf-8")
            print(f"  ✘ 下载 {rel}：{err}")
            return
        try:
            size = target.stat().st_size
        except OSError as exc:
            self._send(500, f"读取失败：{exc}".encode(), "text/plain; charset=utf-8")
            return

        ascii_name = target.name.encode("ascii", "ignore").decode().strip() or "package"
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(size))
        self.send_header("Content-Disposition",
                         f"attachment; filename=\"{ascii_name}\"; "
                         f"filename*=UTF-8''{quote(target.name)}")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            with target.open("rb") as fp:
                shutil.copyfileobj(fp, self.wfile, 256 * 1024)
        except (BrokenPipeError, ConnectionResetError):
            print(f"  ~ 下载中断 {target.name}")
            return
        print(f"  下载 {target.name} · {human_size(size)} ← {self.client_address[0]}")

    def do_POST(self):
        if urlparse(self.path).path != "/install":
            self._json(404, {"ok": False, "message": "未知接口"})
            return
        if not self._client_is_local():
            self._json(403, {"ok": False, "message": "仅允许本机运行"})
            print(f"  ✘ 拒绝远程运行请求 ← {self.client_address[0]}")
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
            payload = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            self._json(400, {"ok": False, "message": "请求体不是合法 JSON"})
            return

        ok, message = launch(payload.get("file", ""), self.base)
        print(f"  {'✔' if ok else '✘'} {message}")
        self._json(200 if ok else 400, {"ok": ok, "message": message})


def lan_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return ""


def port_available(port: int, host: str = "0.0.0.0") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((host, port))
        except OSError:
            return False
    return True


def pick_port(preferred: int = 0, host: str = "0.0.0.0") -> int:
    if preferred and port_available(preferred, host):
        return preferred
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, 0))
        return s.getsockname()[1]


def serve(json_path: Path, port: int, open_browser: bool, host: str = "0.0.0.0") -> int:
    port = pick_port(port, host)
    handler = partial(Handler, json_path=json_path, host=host)
    try:
        httpd = ThreadingHTTPServer((host, port), handler)
        httpd.daemon_threads = True
    except OSError as exc:
        print(f"[错误] 无法监听端口：{exc}", file=sys.stderr)
        return 1

    url = f"http://127.0.0.1:{port}/"
    print(f"服务已启动 {url}")
    ip = lan_ip()
    if host in ("0.0.0.0", "") and ip:
        print(f"  局域网：http://{ip}:{port}/  （只读，不显示运行按钮）")
    print(f"  目录：{json_path.parent}")
    print(f"  运行按钮仅在本机 127.0.0.1 / localhost 打开时展示")
    print(f"  仅当 {json_path.name} 变更时才重新生成，其余请求走缓存；Ctrl+C 退出\n")

    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")
    finally:
        httpd.server_close()
    return 0


# ---------------------------------------------------------------- 入口

def main(argv: list[str] | None = None) -> int:
    try:                       # 输出重定向时也能实时看到日志
        sys.stdout.reconfigure(line_buffering=True)
    except (AttributeError, ValueError):
        pass

    ap = argparse.ArgumentParser(
        description="程序清单：默认启动本地服务器，--generate 只生成静态 HTML"
    )
    ap.add_argument("-i", "--input", default=DEFAULT_JSON, help=f"清单 json（默认 {DEFAULT_JSON}）")
    ap.add_argument("-o", "--output", default=DEFAULT_OUT, help=f"静态输出（默认 {DEFAULT_OUT}）")
    ap.add_argument("-p", "--port", type=int, default=0, help="指定端口，默认自动寻找可用端口")
    ap.add_argument("--host", default="0.0.0.0",
                    help="监听地址，默认 0.0.0.0（局域网可访问，只读）；填 127.0.0.1 则仅本机")
    ap.add_argument("--generate", action="store_true", help="只生成静态 HTML，不启动服务器")
    ap.add_argument("--no-open", action="store_true", help="启动服务器后不自动打开浏览器")
    ap.add_argument("--group", action="store_true", help="按分类分组（仅 --generate 有效）")
    args = ap.parse_args(argv)

    json_path = Path(args.input).expanduser().resolve()
    if not json_path.is_file():
        print(f"[错误] 找不到 {args.input}", file=sys.stderr)
        return 1
    try:
        data = load_json(json_path)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"[错误] {exc}", file=sys.stderr)
        return 1

    if not args.generate:
        return serve(json_path, args.port, not args.no_open, args.host)

    page, info = build(data, json_path, server=False, install=False)
    out = Path(args.output).expanduser()
    if not out.is_absolute():
        out = json_path.parent / out
    out.write_text(page, encoding="utf-8")
    print(f"已生成 {out.name} · {info['total']} 项 · {human_size(info['size'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
