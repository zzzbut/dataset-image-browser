"""版本日志解析器。

从 VERSION_LOG.md 解析为结构化数据，供 GUI 和 CLI 使用。
支持标准 Markdown 格式（## 标题 + 粗体日期/作者 + ### 修改内容 + 列表项）。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class VersionEntry:
    version: str
    date: str
    author: str
    changes: list[str] = field(default_factory=list)


def _strip_md(s: str) -> str:
    """去除 Markdown 加粗标记。"""
    return re.sub(r"\*\*([^*]+)\*\*", r"\1", s).strip()


_VERSION_RE = re.compile(r"^##\s+(v[\d.]+(?:-[\w.]+)?)\s*$")
_DATE_RE = re.compile(r"\*\*日期\*\*[：:]\s*(\S+)")
_AUTHOR_RE = re.compile(r"\*\*作者\*\*[：:]\s*(\S+)")
_CHANGE_RE = re.compile(r"^[-*]\s+(.+)$")


def parse_version_log(md_path: str | Path) -> list[VersionEntry]:
    """解析 VERSION_LOG.md 文件为 VersionEntry 列表（按文件中顺序返回，最新在前）。"""
    md_path = Path(md_path)
    if not md_path.exists():
        return []
    try:
        text = md_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = md_path.read_text(encoding="gbk", errors="replace")

    entries: list[VersionEntry] = []
    current: VersionEntry | None = None
    in_changes = False

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        m = _VERSION_RE.match(line)
        if m:
            if current is not None:
                entries.append(current)
            current = VersionEntry(version=m.group(1), date="", author="")
            in_changes = False
            continue
        if current is None:
            continue
        if not current.date:
            m = _DATE_RE.search(line)
            if m:
                current.date = _strip_md(m.group(1))
                continue
        if not current.author:
            m = _AUTHOR_RE.search(line)
            if m:
                current.author = _strip_md(m.group(1))
                continue
        if line.strip().startswith("### "):
            in_changes = "修改内容" in line or "改动" in line or "更新" in line
            continue
        if in_changes:
            m = _CHANGE_RE.match(line.strip())
            if m:
                current.changes.append(m.group(1).strip())
    if current is not None:
        entries.append(current)
    return entries


def get_latest(md_path: str | Path) -> VersionEntry | None:
    """获取最新版本。"""
    entries = parse_version_log(md_path)
    return entries[0] if entries else None


def get_all(md_path: str | Path) -> list[VersionEntry]:
    """获取所有版本。"""
    return parse_version_log(md_path)


def find_version_log_file() -> Path | None:
    """查找 VERSION_LOG.md 文件位置（支持打包后访问）。"""
    import sys

    # 1. 当前工作目录
    cwd = Path.cwd() / "VERSION_LOG.md"
    if cwd.exists():
        return cwd

    # 2. main.py 所在目录
    try:
        main_dir = Path(__file__).parent / "VERSION_LOG.md"
        if main_dir.exists():
            return main_dir
    except NameError:
        pass

    # 3. 打包后 _MEIPASS 临时目录（PyInstaller 解压路径）
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        p = Path(meipass) / "VERSION_LOG.md"
        if p.exists():
            return p
        p2 = Path(meipass) / "src" / "VERSION_LOG.md"
        if p2.exists():
            return p2

    # 4. 可执行文件自身所在目录
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).parent / "VERSION_LOG.md"
        if exe_dir.exists():
            return exe_dir

    return None


if __name__ == "__main__":
    # 单元测试
    p = find_version_log_file()
    print(f"Found: {p}")
    if p:
        entries = parse_version_log(p)
        print(f"Total versions: {len(entries)}")
        for e in entries[:3]:
            print(f"  {e.version} ({e.date} · {e.author}) - {len(e.changes)} changes")
