# purple-soul

> A minimalist writing tool for terminal geeks.  
> 给极客的极简终端写作工具。

No Markdown preview. No sidebar. No distraction.  
Just you, your words, and a black screen.

没有预览，没有侧边栏，没有任何干扰。  
只有你、你的文字，和一块纯黑的屏幕。

![screenshot](https://raw.githubusercontent.com/thatgameapple/writer/main/screenshot.png)

![screenshot2](https://raw.githubusercontent.com/thatgameapple/writer/main/screenshot2.png)

---

Built with [Textual](https://github.com/Textualize/textual). Inspired by the idea that writing should feel like thinking — quiet, focused, and fast.

基于 [Textual](https://github.com/Textualize/textual) 构建。写作应该像思考一样——安静、专注、快速。

## Install · 安装

```bash
pipx install purple-soul
```

## Run · 启动

```bash
purple-soul
```

## Shortcuts · 快捷键

| Key | Action |
|-----|--------|
| `Ctrl+S` | Save · 保存 |
| `Ctrl+N` | New file · 新建 |
| `Ctrl+L` | File list + tags · 文件列表与标签 |
| `Ctrl+F` | Search · 搜索 |
| `Ctrl+E` | Copy all to clipboard · 复制全文 |
| `Ctrl+Q` | Quit · 退出 |

## Tags · 标签系统

Write `#tag` or `#parent/child` anywhere in your text to organize files — like [flomo](https://flomoapp.com), but in your terminal.

在文字中直接写 `#标签` 或 `#父级/子级`，自动归类文件——像 flomo，但在终端里。

## Design · 设计理念

- Pure black background · 纯黑背景 `#0d0d0d`
- Terminal default text color · 跟随终端字色
- Purple accent · 紫色点缀 `#7c6af7`
- Breathing status bar · 呼吸感状态栏
- Auto-save every 30 seconds · 每30秒自动保存
- Files saved as plain `.txt` · 纯文本存储
