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

## Install · 安装

需要先安装 pipx（如果没有）：

```bash
# Mac
brew install pipx

# Windows / Linux
pip install pipx
```

安装 purple-soul：

```bash
pipx install purple-soul
```

## Run · 启动

```bash
purple-soul
```

---

## Shortcuts · 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+S` | 保存当前文件 |
| `Ctrl+N` | 新建文件 |
| `Ctrl+L` | 打开文件列表 / 标签浏览 |
| `Ctrl+F` | 全局搜索 |
| `Ctrl+E` | 复制全文到剪贴板 |
| `Ctrl+P` | 设置存储路径 |
| `Ctrl+Q` | 退出（自动保存） |
| `Esc` | 关闭搜索 / 关闭弹窗 |

---

## Storage · 存储路径

### 默认路径

首次启动后，文件默认保存到：

```
~/Documents/purple-soul/
```

### 在 app 内修改路径

按 `Ctrl+P` 打开路径设置界面，输入新路径后按回车确认。

**路径写法示例：**

| 存储位置 | 路径写法 |
|----------|----------|
| 桌面 | `~/Desktop/purple-soul` |
| 文稿 | `~/Documents/我的笔记` |
| iCloud | `~/Library/Mobile Documents/com~apple~CloudDocs/purple-soul` |
| 外置硬盘 / 固态硬盘 | `/Volumes/硬盘名称/文件夹名` |

> `~` 是你的主目录的简写，相当于 `/Users/你的用户名`，不需要写完整路径。

### 如何找到外置硬盘的路径（/Volumes 是什么）

Mac 上所有外接硬盘、U盘、固态硬盘插入后，都会挂载到 `/Volumes/` 这个目录下。

**第一步：查看硬盘名称**

打开 Finder，左侧边栏找到你的硬盘，记住它的名字（比如"剪辑"、"SSD"）。

**第二步：在终端确认路径**

```bash
ls /Volumes/
```

会列出所有已连接的硬盘名称。

**第三步：填写路径**

假设硬盘名叫"剪辑"，想把文件存在里面的 `writer_notes` 文件夹：

```
/Volumes/剪辑/writer_notes
```

> ⚠️ 外置硬盘拔掉后路径会失效，purple-soul 启动时会自动重新创建文件夹（如果硬盘已连接）。建议只在硬盘常驻连接时使用这个路径。

### 手动修改路径

也可以直接编辑配置文件：

```bash
open ~/.config/purple-soul/config
```

把文件里的路径改成你想要的目录，保存后重启 purple-soul 生效。

---

## Tags · 标签系统

在文字中直接写 `#标签` 或 `#父级/子级`，自动归类文件。

```
今天去了海边 #日记

这个想法很重要 #灵感/产品

读完了这本书 #读书/2026
```

按 `Ctrl+L` 打开文件列表，左侧可以按标签筛选文件。

---

## Update · 更新

```bash
pipx install purple-soul --force
```

或指定版本：

```bash
pipx install purple-soul==0.2.0 --force
```

---

## Design · 设计理念

- 纯黑背景 `#0d0d0d`
- 跟随终端字色
- 紫色点缀 `#7c6af7`
- 呼吸感状态栏
- 每 30 秒自动保存
- 纯文本 `.txt` 存储，永不锁定你的数据
