#!/usr/bin/env bash
# purple-soul 独立版打包：PyInstaller --onefile 出自包含单文件，
# 拷到任何 Apple Silicon Mac（含 ExFAT 移动盘）双击即用，文稿跟盘走、
# 自带独立文稿库（跟 pipx 命令行版互不共享）。
#
# 为什么是 --onefile 而不是 --onedir（踩坑记录）：
#   · onedir 包一旦被 cp/ditto 复制，adhoc 代码签名 + framework 结构被破坏，
#     arm64 的 AMFI 校验失败 → 进程被静默 SIGKILL（无输出、不报错）。重签名救不回。
#   · textual 几百个 dylib 在 ExFAT（剪辑盘）上加载时签名校验失败，onedir 原地都跑不起来。
#   · onefile 是单个文件：复制不破坏内部结构；运行时自解压到系统临时目录（APFS）再加载，
#     两个坑同时绕开。代价：每次启动要解压约 15-20 秒。
#
# 重要：仅在内置盘(APFS)可靠。ExFAT 移动盘上 onefile 时好时坏(arm64+ExFAT 系统病)，
# 所以使用说明里要求拷到电脑硬盘运行。详见 memory feedback_pyinstaller_textual_portable。
#
# 依赖：python3.11（需已 pip 装好 textual 与 pyinstaller）。
set -euo pipefail
cd "$(dirname "$0")"

DEST="/Volumes/剪辑/thatgameapple工具集/剪辑系列/purple-soul_独立版_macos"
PY=python3.11

echo "→ onefile 打包"
"$PY" -m PyInstaller \
  --name purple-soul --collect-all textual --console --onefile --noconfirm \
  --distpath ./packaging/onefile --workpath ./packaging/build --specpath ./packaging \
  purple_soul.py

echo "→ 组装成品到 $DEST"
mkdir -p "$DEST"
rm -f "$DEST/purple-soul"
cp ./packaging/onefile/purple-soul "$DEST/purple-soul"
chmod +x "$DEST/purple-soul"

cat > "$DEST/启动.command" <<'CMD'
#!/bin/zsh
cd "$(dirname "$0")"
echo ""
echo "  purple soul 正在启动……约 15-20 秒，请稍候。"
echo ""
exec "./purple-soul"
CMD
chmod +x "$DEST/启动.command"

echo "✓ 完成：$DEST"
echo "  注意：使用说明.txt 为手工维护文案，本脚本不覆盖；如缺失请手动补。"
