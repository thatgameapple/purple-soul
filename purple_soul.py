from textual.app import App, ComposeResult
from textual.widgets import TextArea, Footer, ListView, ListItem, Label, Input
from textual.binding import Binding
from textual.message import Message
from textual.events import Key
from textual.containers import Horizontal, Vertical, Center
from textual.screen import ModalScreen
from datetime import datetime
import math
import pathlib
import re
import shutil
import subprocess
import sys
import time
import unicodedata


def _portable_base() -> "pathlib.Path | None":
    """便携版（PyInstaller 打包）返回 启动.command 所在目录，让配置与文稿
    都落在硬盘里、跟着盘走；源码 / PyPI 运行返回 None，沿用系统 home 路径。"""
    if getattr(sys, "frozen", False):
        # PyInstaller onefile：单文件可执行就在成品根目录
        return pathlib.Path(sys.executable).resolve().parent
    return None


_PORTABLE = _portable_base()

if _PORTABLE is not None:
    CONFIG_DIR = _PORTABLE / ".purple-soul"
    _DEFAULT_SAVE = _PORTABLE / "文稿"
else:
    CONFIG_DIR = pathlib.Path.home() / ".config" / "purple-soul"
    _DEFAULT_SAVE = pathlib.Path.home() / "Documents" / "purple-soul"

CONFIG_FILE = CONFIG_DIR / "config"
PINNED_FILE = CONFIG_DIR / "pinned_tags"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

if not CONFIG_FILE.exists():
    CONFIG_FILE.write_text(str(_DEFAULT_SAVE), encoding="utf-8")

SAVE_DIR = pathlib.Path(CONFIG_FILE.read_text(encoding="utf-8").strip())
SAVE_DIR.mkdir(parents=True, exist_ok=True)


def load_pinned() -> list[str]:
    if PINNED_FILE.exists():
        return [l.strip() for l in PINNED_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]
    return []

def save_pinned(pinned: list[str]) -> None:
    PINNED_FILE.write_text("\n".join(pinned), encoding="utf-8")


def list_txt_files() -> list[pathlib.Path]:
    """SAVE_DIR \u4e0b\u6240\u6709 .txt\uff0c\u6309\u4fee\u6539\u65f6\u95f4\u5012\u5e8f\uff08\u8df3\u8fc7\u9690\u85cf\u6587\u4ef6\uff09\u3002"""
    return sorted(
        [f for f in SAVE_DIR.rglob("*.txt") if not f.name.startswith(".")],
        key=lambda f: f.stat().st_mtime, reverse=True
    )


def fit_width(text: str, width: int) -> str:
    """\u6309\u7ec8\u7aef\u5217\u5bbd\u622a\u65ad\u5e76\u53f3\u4fa7\u8865\u9f50 \u2014\u2014 \u4e2d\u6587/\u5168\u89d2\u5b57\u7b26\u5360 2 \u5217\uff0c
    \u76f4\u63a5\u7528 f-string \u7684 :<26 \u4f1a\u6309\u5b57\u7b26\u6570\u8865\uff0c\u4e2d\u6587\u540d\u7684\u65f6\u95f4\u6233\u5c31\u5bf9\u4e0d\u9f50\u3002"""
    out, w = "", 0
    for ch in text:
        cw = 2 if unicodedata.east_asian_width(ch) in "WF" else 1
        if w + cw > width:
            break
        out += ch
        w += cw
    return out + " " * (width - w)


def unique_path(target: pathlib.Path) -> pathlib.Path:
    """\u76ee\u6807\u5df2\u5b58\u5728\u5c31\u52a0\u5e8f\u53f7\uff0c\u7edd\u4e0d\u8986\u76d6\u5df2\u6709\u6587\u7a3f\u3002"""
    if not target.exists():
        return target
    counter = 2
    while True:
        candidate = target.with_name(f"{target.stem} {counter}{target.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def parse_tags(text: str) -> list[str]:
    return re.findall(r'#([\w\u4e00-\u9fff]+(?:/[\w\u4e00-\u9fff]+)*)', text)


def build_tag_tree(all_files: list) -> dict:
    tree = {}
    for f in all_files:
        try:
            content = f.read_text(encoding="utf-8")
        except Exception:
            continue
        for tag in set(parse_tags(content)):
            parts = tag.split("/")
            for i in range(1, len(parts) + 1):
                key = "/".join(parts[:i])
                tree.setdefault(key, [])
                if f not in tree[key]:
                    tree[key].append(f)
    return tree


class SettingsScreen(ModalScreen):
    AUTO_FOCUS = "#path-input"
    CSS = """
    SettingsScreen { align: center middle; }
    #settings-box {
        width: 70; height: 10;
        background: #0d0d0d;
        border: solid #2a2a2a;
        padding: 1 2;
    }
    #settings-title { height: 1; color: #555555; margin-bottom: 1; }
    #settings-current { height: 1; color: #3a3a3a; margin-bottom: 1; }
    #path-input {
        background: #141414;
        color: #d0d0d0;
        border: solid #2a2a2a;
    }
    #settings-hint { height: 1; color: #333333; margin-top: 1; }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="settings-box"):
            yield Label("  storage path", id="settings-title")
            yield Label(f"  current: {SAVE_DIR}", id="settings-current")
            yield Input(value=str(SAVE_DIR), id="path-input")
            yield Label("  enter to confirm  esc to cancel", id="settings-hint")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()  # 别冒泡到 App 的搜索框处理器
        new_path = event.value.strip()
        if new_path:
            self.dismiss(new_path)

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)


class RenameScreen(ModalScreen):
    AUTO_FOCUS = "#rename-input"
    CSS = """
    RenameScreen { align: center middle; }
    #rename-box {
        width: 70; height: 10;
        background: #0d0d0d;
        border: solid #2a2a2a;
        padding: 1 2;
    }
    #rename-title { height: 1; color: #555555; margin-bottom: 1; }
    #rename-current { height: 1; color: #3a3a3a; margin-bottom: 1; }
    #rename-input {
        background: #141414;
        color: #d0d0d0;
        border: solid #2a2a2a;
    }
    #rename-hint { height: 1; color: #333333; margin-top: 1; }
    """

    def __init__(self, current_name: str) -> None:
        super().__init__()
        self._current_name = current_name

    def compose(self) -> ComposeResult:
        with Vertical(id="rename-box"):
            yield Label("  rename", id="rename-title")
            yield Label(f"  current: {self._current_name}", id="rename-current")
            yield Input(value=self._current_name, id="rename-input")
            yield Label("  enter to confirm  esc to cancel", id="rename-hint")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()  # 别冒泡到 App 的搜索框处理器
        new_name = event.value.strip()
        if new_name:
            self.dismiss(new_name)

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)


class TagListView(ListView):
    """支持 p 键置顶的标签列表"""

    class PinToggled(Message):
        def __init__(self, index: int) -> None:
            super().__init__()
            self.index = index

    async def _on_key(self, event: Key) -> None:
        if event.key == "p":
            event.stop()
            if self.index is not None:
                self.post_message(self.PinToggled(self.index))
        else:
            await super()._on_key(event)


class FileListScreen(ModalScreen):
    AUTO_FOCUS = "#tag-list"
    CSS = """
    FileListScreen { align: center middle; }
    #filelist-box {
        width: 82; height: 26;
        background: #0d0d0d;
        border: solid #2a2a2a;
    }
    #filelist-hint {
        height: 1;
        color: #333333;
        background: #0d0d0d;
        padding: 0 2;
    }
    #tag-list { width: 26; background: #0d0d0d; border-right: solid #1a1a1a; border: none; }
    #tag-list ListItem { background: #0d0d0d; color: #3a3a3a; padding: 0 2; }
    #tag-list ListItem:hover { background: #141414; color: #aaaaaa; }
    #tag-list ListItem.--highlight { background: #141414; color: #7c6af7; }
    #file-list { background: #0d0d0d; border: none; }
    #file-list ListItem { background: #0d0d0d; color: #444444; padding: 0 2; }
    #file-list ListItem:hover { background: #141414; color: #cccccc; }
    #file-list ListItem.--highlight { background: #141414; color: #e0e0e0; }
    """

    def __init__(self):
        super().__init__()
        self._all_files = list_txt_files()
        self._tag_tree = build_tag_tree(self._all_files)
        self._pinned: list[str] = load_pinned()
        self._pending_delete: tuple[pathlib.Path, float] | None = None

    def compose(self) -> ComposeResult:
        with Vertical(id="filelist-box"):
            yield Label("  tab  enter  esc    p = pin tag    d = delete", id="filelist-hint")
            with Horizontal():
                yield TagListView(id="tag-list")
                yield ListView(id="file-list")

    def on_mount(self) -> None:
        self._load_tags()
        self._load_files(self._all_files)

    def _load_tags(self) -> None:
        tl = self.query_one("#tag-list", ListView)
        tl.clear()
        tl.append(ListItem(Label("  all"), name="all"))
        # 置顶标签优先显示
        valid_pinned = [t for t in self._pinned if t in self._tag_tree]
        for tag in valid_pinned:
            count = len(self._tag_tree.get(tag, []))
            display = tag.split("/")[-1]
            tl.append(ListItem(Label(f"  ★ {display}  {count}"), name=f"tag:{tag}"))
        # 普通标签
        for tag in sorted(self._tag_tree.keys()):
            if tag in valid_pinned:
                continue
            depth = tag.count("/")
            indent = "  " + "    " * depth
            display = tag.split("/")[-1]
            count = len(self._tag_tree.get(tag, []))
            tl.append(ListItem(Label(f"{indent}# {display}  {count}"), name=f"tag:{tag}"))

    def _load_files(self, files: list) -> None:
        fl = self.query_one("#file-list", ListView)
        fl.clear()
        for f in files:
            mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            fl.append(ListItem(Label(f"  {fit_width(f.stem, 26)}  {mtime}"), name=str(f)))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        name = event.item.name or ""
        if event.list_view.id == "tag-list":
            if name == "all":
                self._load_files(self._all_files)
            elif name.startswith("tag:"):
                self._load_files(self._tag_tree.get(name[4:], []))
            self.query_one("#file-list").focus()
        elif event.list_view.id == "file-list":
            self.dismiss(name)

    def on_tag_list_view_pin_toggled(self, message: TagListView.PinToggled) -> None:
        """只有焦点在标签栏时 TagListView 才会发这条消息，
        所以在文件栏按 p 不会误置顶左栏标签。"""
        self._pending_delete = None
        children = list(self.query_one("#tag-list", TagListView).children)
        idx = message.index
        if not (0 <= idx < len(children)):
            return
        item = children[idx]
        if not (item.name and item.name.startswith("tag:")):
            return
        tag = item.name[4:]
        if tag in self._pinned:
            self._pinned.remove(tag)
        else:
            self._pinned.insert(0, tag)
        save_pinned(self._pinned)
        self._load_tags()

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)
        elif event.key == "tab":
            self._pending_delete = None
            focused = self.focused
            if focused and focused.id == "tag-list":
                self.query_one("#file-list").focus()
            else:
                self.query_one("#tag-list").focus()
        elif event.key == "d":
            self._handle_delete_key()
        else:
            self._pending_delete = None

    def _handle_delete_key(self) -> None:
        focused = self.focused
        if not focused or focused.id != "file-list":
            return
        fl = self.query_one("#file-list", ListView)
        idx = fl.index
        if idx is None:
            return
        children = list(fl.children)
        if not (0 <= idx < len(children)):
            return
        item = children[idx]
        if not item.name:
            return
        target = pathlib.Path(item.name)
        now = time.time()
        if self._pending_delete and self._pending_delete[0] == target and now < self._pending_delete[1]:
            self._pending_delete = None
            try:
                self._move_to_trash(target)
            except Exception as e:
                self.notify(f"delete failed: {e}", severity="error", timeout=3)
                return
            self.notify(f"moved to trash: {target.stem}", timeout=2)
            self._all_files = list_txt_files()
            self._tag_tree = build_tag_tree(self._all_files)
            self._load_tags()
            self._load_files(self._all_files)
            new_len = len(list(fl.children))
            if new_len > 0:
                fl.index = min(idx, new_len - 1)
        else:
            self._pending_delete = (target, now + 5.0)
            self.notify(f"delete {target.stem}? press d again within 5s", timeout=5)

    def _move_to_trash(self, path: pathlib.Path) -> None:
        trash = pathlib.Path.home() / ".Trash"
        trash.mkdir(exist_ok=True)
        dest = trash / path.name
        counter = 1
        while dest.exists():
            dest = trash / f"{path.stem} {counter}{path.suffix}"
            counter += 1
        shutil.move(str(path), str(dest))


def _pbcopy(text: str) -> None:
    try:
        subprocess.run("pbcopy", input=text.encode("utf-8"), check=False)
    except Exception:
        pass


def _pbpaste() -> str:
    try:
        return subprocess.run("pbpaste", capture_output=True, check=False).stdout.decode("utf-8")
    except Exception:
        return ""


class Editor(TextArea):
    """复制/剪切/粘贴接 macOS 系统剪贴板（pbcopy/pbpaste），
    绕开 Textual 默认的 OSC52 —— macOS 终端不支持，导致复制不到系统剪贴板。
    键位沿用 TextArea 自带的 Ctrl+C / Ctrl+X / Ctrl+V；另把 Ctrl+E 改回“复制全文”
    （TextArea 默认 Ctrl+E 是“光标移到行尾”，会盖掉 App 的复制全文，故在此覆盖）。"""

    BINDINGS = [Binding("ctrl+e", "copy_all", "copy all", show=False)]

    def action_copy(self) -> None:
        text = self.selected_text or self.text
        if text:
            _pbcopy(text)

    def action_cut(self) -> None:
        if self.selected_text:
            _pbcopy(self.selected_text)
            start, end = sorted([self.selection.start, self.selection.end])
            self.delete(start, end)

    def action_paste(self) -> None:
        text = _pbpaste()
        if not text:
            return
        start, end = sorted([self.selection.start, self.selection.end])
        self.replace(text, start, end)

    def action_copy_all(self) -> None:
        if self.text.strip():
            _pbcopy(self.text)
            self.app.notify("copied all.", timeout=2)


class WriterApp(App):
    CSS = """
    Screen { background: #0d0d0d; }

    ScrollBar { display: none; }
    ScrollBarCorner { display: none; }
    Vertical { scrollbar-size: 0 0; }
    Center { scrollbar-size: 0 0; }
    Screen { scrollbar-size: 0 0; }

    #editor-wrap {
        align: center top;
        background: #0d0d0d;
        height: 1fr;
    }

    TextArea {
        background: #0d0d0d;
        color: ansi_default;
        border: none;
        padding: 4 0;
        width: 80;
        scrollbar-size: 0 0;
    }

    TextArea:focus { border: none; }

    #search-bar {
        height: 10;
        background: #0d0d0d;
        border-top: solid #1a1a1a;
        align: center top;
        padding: 1 0;
        display: none;
    }

    #search-wrap {
        width: 80;
    }

    #search-bar Input {
        background: #0d0d0d;
        color: #d0d0d0;
        border: none;
        border-bottom: solid #2a2a2a;
        padding: 0 0;
    }

    #search-results { background: #0d0d0d; border: none; padding: 0; }
    #search-results ListItem { background: #0d0d0d; color: #444444; padding: 0 0; }
    #search-results ListItem:hover { background: #0d0d0d; color: #cccccc; }
    #search-results ListItem.--highlight { background: #0d0d0d; color: #e0e0e0; }

    #statusbar {
        height: 1;
        background: #111111;
        color: #333333;
        padding: 0 2;
    }

    Footer { background: #111111; color: #333333; }

    .footer-key--key {
        color: #7c6af7;
        background: #111111;
        padding: 0 1;
    }

    .footer-key--description { color: #444444; padding: 0 1; }
    """

    ENABLE_COMMAND_PALETTE = False

    BINDINGS = [
        Binding("ctrl+q", "quit", "quit"),
        Binding("ctrl+s", "save", "save"),
        Binding("ctrl+n", "new_file", "new"),
        Binding("ctrl+e", "export_clipboard", "copy all", show=False),
        Binding("ctrl+l", "open_list", "files", show=False),
        Binding("ctrl+g", "toggle_search", "search", show=False),
        Binding("ctrl+p", "open_settings", "path", show=False),
        Binding("ctrl+r", "rename", "rename", show=False),
        Binding("escape", "close_search", "", show=False),
    ]

    def __init__(self):
        super().__init__()
        self._current_file: pathlib.Path | None = None
        self._dirty: bool = False
        self._search_visible = False
        self._last_keyword: str = ""
        self._last_loaded_content: str = ""
        self._search_timer = None
        self._last_minute: str = ""

    def compose(self) -> ComposeResult:
        with Vertical():
            with Center(id="editor-wrap"):
                yield Editor(language="markdown", id="editor")
            with Vertical(id="search-bar"):
                with Vertical(id="search-wrap"):
                    yield Input(placeholder="> search_", id="search-input")
                    yield ListView(id="search-results")
        yield Label("", id="statusbar")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "writer"
        self.query_one("#editor").focus()
        self._update_status()
        self.set_interval(30, self._auto_save)
        self._breath_step = 0
        self.set_interval(0.1, self._breathe)

    def _breathe(self) -> None:
        self._breath_step += 1
        # 慢呼吸：4秒一个周期
        val = (math.sin(self._breath_step * 0.16) + 1) / 2
        # 在 #1a1a1a 和 #3a3a3a 之间变化
        v = int(0x1a + val * 0x20)
        color = f"#{v:02x}{v:02x}{v:02x}"
        self.query_one("#statusbar", Label).styles.color = color
        # 状态栏的钟原本只在敲字时才刷新，坐着不动就停住了
        now = datetime.now().strftime("%H:%M")
        if now != self._last_minute:
            self._update_status()

    def _update_status(self) -> None:
        count = len(self.query_one("#editor", TextArea).text.replace("\n", "").replace(" ", ""))
        fname = self._current_file.stem if self._current_file else "untitled"
        now = datetime.now().strftime("%H:%M")
        self._last_minute = now
        self.query_one("#statusbar", Label).update(f"  {fname}  ·  {count} chars  ·  {now}")

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        current = self.query_one("#editor", TextArea).text
        self._dirty = current != self._last_loaded_content
        self._update_status()

    def _save_current(self) -> None:
        """切走当前这篇之前先落盘 —— 自动保存是 30 秒一次，
        中间切文件/新建会把这段时间敲的字丢掉。"""
        if self._dirty:
            self._do_save(silent=True)

    def _open_file(self, path: pathlib.Path) -> str | None:
        """保存当前 → 载入目标文章。返回载入的正文，失败返回 None。"""
        self._save_current()
        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            self.notify(f"open failed: {e}", severity="error", timeout=3)
            return None
        self._current_file = path
        self.query_one("#editor", TextArea).load_text(content)
        self._last_loaded_content = content
        self._dirty = False
        self._update_status()
        return content

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.item.name and event.item.name.startswith("search:"):
            path = pathlib.Path(event.item.name.replace("search:", ""))
            content = self._open_file(path)
            if content is None:
                return
            self.action_close_search()
            self._jump_to_keyword(content, self._last_keyword)

    def _cancel_search_timer(self) -> None:
        if self._search_timer is not None:
            self._search_timer.stop()
            self._search_timer = None

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "search-input":
            return
        kw = event.value.strip()
        self._last_keyword = kw
        self._cancel_search_timer()
        self._do_global_search(kw, announce=True)

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != "search-input":
            return
        self._cancel_search_timer()
        kw = event.value.strip()
        if len(kw) >= 2:
            self._last_keyword = kw
            # 防抖：每敲一个字就把全库读一遍会卡，停手 0.25 秒再搜
            self._search_timer = self.set_timer(0.25, lambda: self._do_global_search(kw))

    def _jump_to_keyword(self, content: str, keyword: str) -> None:
        if not keyword:
            return
        from textual.widgets.text_area import Selection
        editor = self.query_one("#editor", TextArea)
        lines = content.splitlines()
        for row, line in enumerate(lines):
            col = line.lower().find(keyword.lower())
            if col != -1:
                editor.move_cursor((row, col))
                editor.selection = Selection(
                    (row, col), (row, col + len(keyword))
                )
                break

    def _do_global_search(self, keyword: str, announce: bool = False) -> None:
        if not keyword:
            return
        self._search_timer = None
        results = self.query_one("#search-results", ListView)
        results.clear()
        found = 0
        for f in list_txt_files():
            try:
                content = f.read_text(encoding="utf-8")
            except Exception:
                continue
            if keyword.lower() in content.lower():
                for line in content.splitlines():
                    if keyword.lower() in line.lower():
                        preview = line.strip()[:40]
                        break
                else:
                    preview = ""
                mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%m-%d")
                results.append(ListItem(Label(f"  {mtime}  {preview}"), name=f"search:{f}"))
                found += 1
        # 边打边搜时不弹通知，只有回车确认才报数（否则每敲一个字闪一次）
        if announce:
            self.notify(f"found {found} file(s)", timeout=2)

    def action_new_file(self) -> None:
        self._save_current()
        self._current_file = None
        self._dirty = False
        self.query_one("#editor", TextArea).load_text("")
        self._last_loaded_content = ""
        self.query_one("#editor").focus()
        self._update_status()

    def action_save(self) -> None:
        self._do_save()

    def _auto_save(self) -> None:
        if self._dirty and self.query_one("#editor", TextArea).text.strip():
            self._do_save(silent=True)

    def _do_save(self, silent=False) -> None:
        content = self.query_one("#editor", TextArea).text
        if not content.strip():
            return
        if self._current_file is None:
            first_line = content.strip().splitlines()[0][:30].strip()
            name = re.sub(r'[#/\\:*?"<>|]', '', first_line).strip()
            name = name if name else datetime.now().strftime("%Y%m%d_%H%M%S")
            # 首行重名时加序号，绝不覆盖已有文稿
            self._current_file = unique_path(SAVE_DIR / f"{name}.txt")
        self._current_file.write_text(content, encoding="utf-8")
        self._last_loaded_content = content
        self._dirty = False
        self._update_status()
        if not silent:
            self.notify("saved.", timeout=2)

    def action_export_clipboard(self) -> None:
        content = self.query_one("#editor", TextArea).text
        if content.strip():
            _pbcopy(content)
            self.notify("copied to clipboard.", timeout=2)

    def action_open_list(self) -> None:
        def handle(path: str | None):
            if path and self._open_file(pathlib.Path(path)) is not None:
                self.query_one("#editor").focus()
        self._save_current()
        self.push_screen(FileListScreen(), handle)

    def action_open_settings(self) -> None:
        def handle(new_path: str | None):
            if new_path:
                global SAVE_DIR
                p = pathlib.Path(new_path).expanduser()
                p.mkdir(parents=True, exist_ok=True)
                CONFIG_FILE.write_text(str(p), encoding="utf-8")
                SAVE_DIR = p
                self.notify(f"saved to: {p}", timeout=3)
        self.push_screen(SettingsScreen(), handle)

    def action_rename(self) -> None:
        editor = self.query_one("#editor", TextArea)
        # 还没保存过的，先存一下生成文件，再重命名
        if self._current_file is None:
            if not editor.text.strip():
                self.notify("nothing to rename yet.", timeout=2)
                return
            self._do_save(silent=True)
        if self._current_file is None:
            return

        def handle(new_name: str | None) -> None:
            if not new_name:
                return
            name = re.sub(r'[#/\\:*?"<>|]', '', new_name).strip()
            if not name:
                self.notify("invalid name.", timeout=2)
                return
            target = self._current_file.with_name(f"{name}.txt")
            if target == self._current_file:
                return
            if target.exists():
                self.notify(f"'{name}' already exists.", timeout=3)
                return
            try:
                self._current_file.rename(target)
            except Exception as e:
                self.notify(f"rename failed: {e}", timeout=3)
                return
            self._current_file = target
            self._update_status()
            self.notify(f"renamed: {name}", timeout=2)

        self.push_screen(RenameScreen(self._current_file.stem), handle)

    def action_toggle_search(self) -> None:
        self._search_visible = not self._search_visible
        self.query_one("#search-bar").display = self._search_visible
        if self._search_visible:
            self.query_one("#search-input", Input).focus()
            self.query_one("#search-results", ListView).clear()
        else:
            self.query_one("#editor").focus()

    def action_close_search(self) -> None:
        if self._search_visible:
            self._search_visible = False
            self.query_one("#search-bar").display = False
            self.query_one("#editor").focus()

    def action_quit(self) -> None:
        self._do_save(silent=True)
        self.exit()


def main():
    WriterApp().run()


if __name__ == "__main__":
    main()
