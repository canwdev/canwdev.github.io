- 教学视频：[即將失傳的古老技藝 Vim](https://www.bilibili.com/video/BV1fV41187Zr) 

## 02 Install vim

Windows: [gvim](https://github.com/vim/vim-win32-installer/releases)

## 03 Type in vim

- Toggle Input mode: `i` key
- Toggle Command mode: `esc` key or `ctrl+[`

## 04 Move cursor

- in Command mode, type `h` `j` `k` `l` to move cursor

## 05 Move faster

- `w` for jump a word forward, `W` 表示可以跳过标点符号
- `b` 与 `w` 相反，是往前跳单词，`B` 也可以跳过标点符号
- `G` jump to file end, `gg` jump to file start
- `0` jump to line start, `$` jump to line end
- `gj` jump to up block(上方的区块), `gk` jump to down block

## 06 Search text

- /TEXT_TO_SEARCH
- :set hlsearch      把搜索结果高亮
- `n` jump to next search result, `N` for previousi
- ?TEXT_TO_SEARCH    The only difference is `n` or `N` keys direction is reversed!
- `*` or `#` search current cursor text
- :set nohlsearch     turn off hlsearch
- `fa` jumpt to next `a`, the `a` is custom. `Fa` jump to previous `a`

- `zz` 让当前行显示在画面中间
- `zt` to top, `zb` to bottom

## 07 Select Copy Paste

- Enter visual mode: `v`, then you can select
- In visualt mode, you can press `fa` `Fa` `w` `b` `gg` `G` etc... just like command mode
- `V` for select whole line
- `y` for copy(yank), copied context is in register(寄存器)
- `p` for paste, `5p` paste 5 times
- `yy` copy whole line, `yyp`, `yy5p`

## 08 More Select Copy Paste

- `2yy` copy two lines...
- `P` paste before cursor
- `y$` copy to line end, `y0` copy to line start `yw` `yb` `yG` `ygg`...
- `u` for undo, `R` for redo

Vim has multiple Registers

- `  "ay  ` copy selected to Register `a`
- `  "by  ` copy selected to Register `b`...
- `  "ap  ` paste Register `a` content, `   "bp    `...
- :reg      check all Register

- :set clipboard=unnamed       让剪贴板和寄存器互通

## 09 How to edit text

Insertion

- `I` jump to line first and enter Insert mode, `i`...
- `A` jump to line end and enter Insert mode, `a`...
- `O` create a new line above current line and enter Insert mode, `o`...

Deletetion

- `x` delete character in current cursor, also worked in selected(Visual mode)
- `d` delete what you are selected, `D` delete everything after cursor(in current line)
- `dd` delete one line, `2dd` delete two lines...
- `dG` `dgg`...
- `c` equals delete and enter Insert mode (press `d` and press `i`)
- `C` likes `D` and then `i`
- `rx` replace current cursor to letter `x`

Indentation(缩进)

- `>>` indent right current line, `3>>`...
- `<<` indent left current line
- :set shiftwidth=8      设置缩进距离

## 10 Edit multiple files

- :tabe     Create new tab
- :tabe FILENAME      Create new tab and open FILENAME
- `gt` `gT` switch tabs
- :new      Create new horizontal window, `ctrl+w+w` loop switch opened windows, `ctrl+w+j` `ctrl+w+k`...
- :vnew     Create new vertical window, `ctrl+w+h` `ctrl+w+l`...
- vim -o file1 file2      Open multiple files in vertical window at once
- vim -O file1 file2      (horizontal)
- vim -p file1 file3      Open multiple files in tabs
- :qa        :quitall      Close all file


## 11 Edit multiple files 2

   A buffer is the in-memory text of a file.
   A window is a viewport on a buffer.
   A tab page is a collection of windows.

- vim file1 file2      Open two files in buffer
- :ls                  Show all opened buffers
- :b3                  Jump to buffer #3, :b2 :b1 ...
- ctrl+^               Jump to previous buffer
- :b file1             Jump to file1 buffer
- :bn                  Jump to next buffer(:bnext), :bp(:bprevious), :bl(:blast), :bf(:bfirst)
- :bd                  Close current buffer
- :tab ba              Expand all buffers to tabs

