#!/usr/bin/env bash
# purple-soul 一键发布：build → PyPI → git tag → GitHub Release
# 用法：先在 pyproject.toml 改好 version，commit，然后 ./release.sh

set -euo pipefail
cd "$(dirname "$0")"

VERSION=$(grep -E '^version\s*=' pyproject.toml | sed -E 's/.*"([^"]+)".*/\1/')
TAG="v${VERSION}"
WHL="dist/purple_soul-${VERSION}-py3-none-any.whl"
TAR="dist/purple_soul-${VERSION}.tar.gz"

echo "→ 发布 ${TAG}"

# 1. 工作树必须干净（dist/ 不算）
if ! git diff --quiet ':!dist' || ! git diff --cached --quiet ':!dist'; then
  echo "✗ 有未提交改动，先 commit"; exit 1
fi

# 2. tag 不能已存在
if git rev-parse "${TAG}" >/dev/null 2>&1; then
  echo "✗ tag ${TAG} 已存在"; exit 1
fi

# 3. build
rm -f "${WHL}" "${TAR}"
python3 -m build

# 4. PyPI
twine upload "${WHL}" "${TAR}"

# 5. tag + push（origin + 03备份盘 mirror）
git tag -a "${TAG}" -m "${TAG}"
git push origin "${TAG}"
if [ -d /Volumes/03备份/purple-soul.git ]; then
  git push backup --all
  git push backup --tags
  echo "→ 已同步到 03备份盘"
else
  echo "⚠ 03备份盘未挂载，跳过备份同步"
fi

# 6. GitHub Release（用 commit message 自动生成 notes）
gh release create "${TAG}" \
  --title "${TAG}" \
  --generate-notes \
  "${WHL}" "${TAR}"

echo "✓ ${TAG} 发布完成"
echo "  PyPI:    https://pypi.org/project/purple-soul/${VERSION}/"
echo "  Release: https://github.com/thatgameapple/purple-soul/releases/tag/${TAG}"
