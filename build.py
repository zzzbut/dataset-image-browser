#!/usr/bin/env python
"""Build the Tkinter image browser with PyInstaller (CPU-only)."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _get_version() -> str:
    version_file = Path(__file__).parent / "src" / "tk_app.py"
    for line in version_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("VERSION"):
            return line.split('"')[1] if '"' in line else line.split("'")[1]
    return "unknown"


# 不需要的标准库模块（减小体积）
EXCLUDE_STDLIB = [
    "--exclude-module=unittest",
    "--exclude-module=test",
    "--exclude-module=tests",
    "--exclude-module=xmlrpc",
    "--exclude-module=pydoc",
    "--exclude-module=doctest",
    "--exclude-module=lib2to3",
    "--exclude-module=curses",
    "--exclude-module=msilib",
    "--exclude-module=asyncio",
    "--exclude-module=email",
    "--exclude-module=http",
    "--exclude-module=urllib",
    "--exclude-module=ftplib",
    "--exclude-module=smtplib",
    "--exclude-module=imaplib",
    "--exclude-module=nntplib",
    "--exclude-module=telnetlib",
    "--exclude-module=html",
    "--exclude-module=xml",
    "--exclude-module=xml.dom",
    "--exclude-module=xml.sax",
    "--exclude-module=pydoc",
]

# 不需要的第三方库
EXCLUDE_THIRDPARTY = [
    "--exclude-module=torch",
    "--exclude-module=torchvision",
    "--exclude-module=matplotlib",
    "--exclude-module=scipy",
    "--exclude-module=pandas",
    "--exclude-module=sympy",
    "--exclude-module=PyQt5",
    "--exclude-module=PyQt6",
    "--exclude-module=PySide2",
    "--exclude-module=PySide6",
    "--exclude-module=imagehash",
    "--exclude-module=IPython",
    "--exclude-module=notebook",
    "--exclude-module=jupyter",
]

# 不需要的 tkinter 子模块
EXCLUDE_TKINTER = [
    "--exclude-module=tkinter.test",
    "--exclude-module=tkinter.tix",
    "--exclude-module=tkinter.colorchooser",
    "--exclude-module=tkinter.dialog",
    "--exclude-module=tkinter.dnd",
    "--exclude-module=tkinter.scrolledtext",
]

# 不需要的 PIL 图像格式插件（项目仅支持 jpg/png/bmp/webp/tif）
EXCLUDE_PIL_PLUGINS = [
    "--exclude-module=PIL.MpegImagePlugin",
    "--exclude-module=PIL.SgiImagePlugin",
    "--exclude-module=PIL.FpxImagePlugin",
    "--exclude-module=PIL.MicImagePlugin",
    "--exclude-module=PIL.SpiderImagePlugin",
    "--exclude-module=PIL.XVThumbImagePlugin",
    "--exclude-module=PIL.BlpImagePlugin",
    "--exclude-module=PIL.BufrStubImagePlugin",
    "--exclude-module=PIL.DcxImagePlugin",
    "--exclude-module=PIL.EpsImagePlugin",
    "--exclude-module=PIL.GbrImagePlugin",
    "--exclude-module=PIL.GribStubImagePlugin",
    "--exclude-module=PIL.Hdf5StubImagePlugin",
    "--exclude-module=PIL.IcnsImagePlugin",
    "--exclude-module=PIL.ImImagePlugin",
    "--exclude-module=PIL.ImtImagePlugin",
    "--exclude-module=PIL.IptcImagePlugin",
    "--exclude-module=PIL.Jpeg2KImagePlugin",
    "--exclude-module=PIL.McIdasImagePlugin",
    "--exclude-module=PIL.MpoImagePlugin",
    "--exclude-module=PIL.PalmImagePlugin",
    "--exclude-module=PIL.PcdImagePlugin",
    "--exclude-module=PIL.PcxImagePlugin",
    "--exclude-module=PIL.PdfImagePlugin",
    "--exclude-module=PIL.PixarImagePlugin",
    "--exclude-module=PIL.PsdImagePlugin",
    "--exclude-module=PIL.SunImagePlugin",
    "--exclude-module=PIL.TgaImagePlugin",
    "--exclude-module=PIL.WmfImagePlugin",
    "--exclude-module=PIL.XbmImagePlugin",
    "--exclude-module=PIL.XpmImagePlugin",
    "--exclude-module=PIL.ImageCms",
    "--exclude-module=PIL.ImageFilter",
    "--exclude-module=PIL.ImageGrab",
    "--exclude-module=PIL.ImageQt",
    "--exclude-module=PIL.ImageWin",
    "--exclude-module=PIL.ImageStat",
    "--exclude-module=PIL.ImageSequence",
]

# 实际需要的隐式导入
HIDDEN_IMPORTS = [
    "--hidden-import=PIL._imaging",
    "--hidden-import=PIL.Image",
    "--hidden-import=PIL.ImageDraw",
    "--hidden-import=PIL.ImageFont",
    "--hidden-import=tkinter",
    "--hidden-import=cv2",
    "--hidden-import=numpy",
    "--hidden-import=numpy.core",
    "--hidden-import=numpy.core._multiarray_umath",
    "--hidden-import=decord",
    "--hidden-import=appdirs",
    "--hidden-import=pkg_resources.extern.appdirs",
    "--hidden-import=pkg_resources._vendor.appdirs",
]

# 需要收集全部文件的包（含编译扩展和原生库）
COLLECT_ALL = [
    "--collect-all=cv2",
    "--collect-all=PIL",
    "--collect-all=numpy",
    "--collect-all=decord",
]


def _pathsep(is_linux: bool) -> str:
    return ":" if is_linux else ";"


def _write_linux_launcher(app_dir: Path, exe_name: str) -> None:
    launcher = app_dir / f"run_{exe_name}.sh"
    launcher.write_text(
        "\n".join(
            [
                "#!/usr/bin/env sh",
                'APPDIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"',
                'export LD_LIBRARY_PATH="$APPDIR:$APPDIR/_internal:$APPDIR/lib:${LD_LIBRARY_PATH:-}"',
                'exec "$APPDIR/' + exe_name + '" "$@"',
                "",
            ]
        ),
        encoding="utf-8",
        newline="\n",
    )
    launcher.chmod(0o755)
    print(f"Launcher created: {launcher}")


def _print_linux_dependency_note(onefile: bool) -> None:
    if onefile:
        print("Linux one-file build bundles Python packages and extracts native libs at runtime.")
    else:
        print("Linux onedir build keeps bundled libraries next to the executable in _internal/.")
        print("Use run_*.sh if a target machine needs LD_LIBRARY_PATH pointed at the bundle.")
    print("System ABI libraries such as glibc are still provided by the OS.")


def build(console: bool = False, onefile: bool = True) -> None:
    root = Path(__file__).parent
    version = _get_version()
    is_linux = sys.platform.startswith("linux")

    suffix = f"_{version}_cpu"
    if console:
        suffix += "_console"
    if is_linux:
        suffix += "_linux"
    elif sys.platform == "darwin":
        suffix += "_macos"
    else:
        suffix += "_win"
    exe_name = f"ImageBrowser{suffix}"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        f"--name={exe_name}",
        "--onefile" if onefile else "--onedir",
        *([] if (is_linux or console) else ["--windowed"]),
        "--clean",
        "--noconfirm",
        f"--distpath={root / 'dist'}",
        f"--workpath={root / 'build'}",
        f"--specpath={root}",
        f"--add-data=src{_pathsep(is_linux)}src",
    ]

    # 排除不需要的模块（减小体积）
    cmd.extend(EXCLUDE_STDLIB)
    cmd.extend(EXCLUDE_THIRDPARTY)
    cmd.extend(EXCLUDE_TKINTER)
    cmd.extend(EXCLUDE_PIL_PLUGINS)

    # 隐式导入 + 收集原生库
    cmd.extend(HIDDEN_IMPORTS)
    cmd.extend(COLLECT_ALL)

    cmd.append(str(root / "main.py"))

    mode = "console" if console else "windowed"
    bundle_mode = "onefile" if onefile else "onedir"
    print(f"Building (CPU only) on {sys.platform} [{mode}, {bundle_mode}]...")
    print(" ".join(cmd[:12]) + " ...")

    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        print("\nBuild failed!")
        sys.exit(1)

    exe_filename = exe_name if is_linux else f"{exe_name}.exe"
    output_path = root / "dist" / exe_filename if onefile else root / "dist" / exe_name
    exe_path = output_path if onefile else output_path / exe_filename

    if exe_path.exists():
        if is_linux:
            exe_path.chmod(0o755)
        if output_path.is_file():
            size_mb = output_path.stat().st_size / 1024 / 1024
            print(f"\nBuild complete: {output_path}")
            print(f"File size: {size_mb:.1f} MB")
        else:
            print(f"\nBuild complete: {output_path}")
        if is_linux:
            if not onefile:
                _write_linux_launcher(output_path, exe_filename)
            _print_linux_dependency_note(onefile)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build ImageBrowser with PyInstaller (CPU only).")
    parser.add_argument("-c", "--console", action="store_true", help="keep a console window on Windows")
    parser.add_argument(
        "--onedir",
        action="store_true",
        help="build a portable directory with libraries beside the executable",
    )
    parser.add_argument(
        "--onefile",
        action="store_true",
        help="force a single-file executable; this is the default",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    onefile = True
    if args.onedir:
        onefile = False
    if args.onefile:
        onefile = True
    build(console=args.console, onefile=onefile)
