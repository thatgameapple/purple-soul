from textual.app import App, ComposeResult
from textual.widgets import TextArea, Footer, ListView, ListItem, Label, Input
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, Center
from textual.screen import ModalScreen
from datetime import datetime
import pathlib
import re

CONFIG_FILE = pathlib.Path.home() / ".config" / "purple-soul" / "config"
CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

if not CONFIG_FILE.exists():
    default_dir = pathlib.Path.home() / "Documents" / "purple-soul"
    CONFIG_FILE.write_text(str(default_dir), encoding="utf-8")

SAVE_DIR = pathlib.Path(CONFIG_FILE.read_text(encoding="utf-8").strip())
SAVE_DIR.mkdir(parents=True, exist_ok=True)


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
        self._all_files = sorted(
            [f for f in SAVE_DIR.rglob("*.txt") if not f.name.startswith(".")],
            key=lambda f: f.stat().st_mtime, reverse=True
        )
        self._tag_tree = build_tag_tree(self._all_files)

    def compose(self) -> ComposeResult:
        with Vertical(id="filelist-box"):
            yield Label("  tab  enter  esc", id="filelist-hint")
            with Horizontal():
                yield ListView(id="tag-list")
                yield ListView(id="file-list")

    def on_mount(self) -> None:
        self._load_tags()
        self._load_files(self._all_files)

    def _load_tags(self) -> None:
        tl = self.query_one("#tag-list", ListView)
        tl.clear()
        tl.append(ListItem(Label("  all"), name="all"))
        for tag in sorted(set(t.split("/")[0] for t in self._tag_tree)):
            count = len(self._tag_tree.get(tag, []))
            tl.append(ListItem(Label(f"  # {tag}  {count}"), name=f"tag:{tag}"))

    def _load_files(self, files: list) -> None:
        fl = self.query_one("#file-list", ListView)
        fl.clear()
        for f in files:
            mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%m-%d %H:%M")
            fl.append(ListItem(Label(f"  {f.stem:<32} {mtime}"), name=str(f)))

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

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)
        elif event.key == "tab":
            focused = self.focused
            if focused and focused.id == "tag-list":
                self.query_one("#file-list").focus()
            else:
                self.query_one("#tag-list").focus()


class WriterApp(App):
    CSS = """
    Screen { background: #0d0d0d; }

    ScrollBar { display: none !important; }
    ScrollBarCorner { display: none !important; }
    * > ScrollBar { display: none !important; }
    * > ScrollBarCorner { display: none !important; }

    #editor-wrap {
        align: center top;
        background: #0d0d0d;
    }

    TextArea {
        background: #0d0d0d;
        color: ansi_default;
        border: none;
        padding: 4 0;
        width: 80;
    }

    TextArea:focus { border: none; }

    #search-bar {
        height: 12;
        background: #0d0d0d;
        border-top: solid #1a1a1a;
        padding: 0 2;
        display: none;
    }

    #search-bar Input {
        background: #141414;
        color: #d0d0d0;
        border: solid #2a2a2a;
    }

    #search-results { background: #0d0d0d; border: none; padding: 0; }
    #search-results ListItem { background: #0d0d0d; color: #444444; padding: 0 2; }
    #search-results ListItem:hover { background: #141414; color: #cccccc; }
    #search-results ListItem.--highlight { background: #141414; color: #e0e0e0; }

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
        Binding("ctrl+f", "toggle_search", "search", show=False),
        Binding("escape", "close_search", "", show=False),
    ]

    def __init__(self):
        super().__init__()
        self._current_file: pathlib.Path | None = None
        self._search_visible = False

    def compose(self) -> ComposeResult:
        with Vertical():
            with Center(id="editor-wrap"):
                yield TextArea(language="markdown", id="editor")
            with Vertical(id="search-bar"):
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
        self.set_interval(0.05, self._breathe)

    def _breathe(self) -> None:
        import math
        self._breath_step += 1
        # 慢呼吸：4秒一个周期
        val = (math.sin(self._breath_step * 0.08) + 1) / 2
        # 在 #1a1a1a 和 #3a3a3a 之间变化
        v = int(0x1a + val * 0x20)
        color = f"#{v:02x}{v:02x}{v:02x}"
        self.query_one("#statusbar", Label).styles.color = color

    def _update_status(self) -> None:
        count = len(self.query_one("#editor", TextArea).text.replace("\n", "").replace(" ", ""))
        fname = self._current_file.stem if self._current_file else "untitled"
        now = datetime.now().strftime("%H:%M")
        self.query_one("#statusbar", Label).update(f"  {fname}  ·  {count} chars  ·  {now}")

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        self._update_status()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.item.name and event.item.name.startswith("search:"):
            path = pathlib.Path(event.item.name.replace("search:", ""))
            try:
                content = path.read_text(encoding="utf-8")
            except Exception:
                return
            self._current_file = path
            self.query_one("#editor", TextArea).load_text(content)
            self.action_close_search()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._do_global_search(event.value.strip())

    def on_input_changed(self, event: Input.Changed) -> None:
        if len(event.value.strip()) >= 2:
            self._do_global_search(event.value.strip())

    def _do_global_search(self, keyword: str) -> None:
        if not keyword:
            return
        results = self.query_one("#search-results", ListView)
        results.clear()
        files = sorted(
            [f for f in SAVE_DIR.rglob("*.txt") if not f.name.startswith(".")],
            key=lambda f: f.stat().st_mtime, reverse=True
        )
        found = 0
        for f in files:
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
        self.notify(f"found {found} file(s)", timeout=2)

    def action_new_file(self) -> None:
        self._current_file = None
        self.query_one("#editor", TextArea).load_text("")
        self.query_one("#editor").focus()
        self._update_status()

    def action_save(self) -> None:
        self._do_save()

    def _auto_save(self) -> None:
        if self.query_one("#editor", TextArea).text.strip():
            self._do_save(silent=True)

    def _do_save(self, silent=False) -> None:
        content = self.query_one("#editor", TextArea).text
        if not content.strip():
            return
        if self._current_file is None:
            first_line = content.strip().splitlines()[0][:30].strip()
            name = re.sub(r'[#/\\:*?"<>|]', '', first_line).strip()
            name = name if name else datetime.now().strftime("%Y%m%d_%H%M%S")
            self._current_file = SAVE_DIR / f"{name}.txt"
        self._current_file.write_text(content, encoding="utf-8")
        self._update_status()
        if not silent:
            self.notify("saved.", timeout=2)

    def action_export_clipboard(self) -> None:
        import subprocess
        content = self.query_one("#editor", TextArea).text
        if content.strip():
            subprocess.run("pbcopy", input=content.encode("utf-8"), check=True)
            self.notify("copied to clipboard.", timeout=2)

    def action_open_list(self) -> None:
        def handle(path: str | None):
            if path:
                p = pathlib.Path(path)
                try:
                    content = p.read_text(encoding="utf-8")
                except Exception:
                    return
                self._current_file = p
                self.query_one("#editor", TextArea).load_text(content)
                self.query_one("#editor").focus()
                self._update_status()
        self.push_screen(FileListScreen(), handle)

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


if __name__ == "__main__":
    WriterApp().run()

def main():
    WriterApp().run()
