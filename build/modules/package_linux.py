#!/usr/bin/env python3
"""
Linux AppImage packaging module for BrowserOS
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional

from context import BuildContext
from utils import log_info, log_error, log_warning, log_success, run_command, safe_rmtree, join_paths


def prepare_appdir(ctx: BuildContext, appdir: Path) -> bool:
    """Prepare the AppDir structure for AppImage"""
    log_info("📁 Preparing AppDir structure...")
    
    # Create directory structure
    app_root = join_paths(appdir, "opt", "browseros")
    usr_share = join_paths(appdir, "usr", "share")
    icons_dir = join_paths(usr_share, "icons", "hicolor")
    
    # Create directories
    app_root.mkdir(parents=True, exist_ok=True)
    Path(join_paths(usr_share, "applications")).mkdir(parents=True, exist_ok=True)
    Path(join_paths(icons_dir, "256x256", "apps")).mkdir(parents=True, exist_ok=True)
    
    # Copy browser files from out/Default
    out_dir = ctx.out_dir
    
    # Essential files to copy
    files_to_copy = [
        "chrome",
        "chrome_crashpad_handler",
        "chrome_sandbox",
        "chromedriver",
        "libEGL.so",
        "libGLESv2.so",
        "libvk_swiftshader.so",
        "libvulkan.so.1",
        "vk_swiftshader_icd.json",
        "icudtl.dat",
        "snapshot_blob.bin",
        "v8_context_snapshot.bin",
        "chrome_100_percent.pak",
        "chrome_200_percent.pak",
        "resources.pak",
    ]
    
    # Copy files
    for file in files_to_copy:
        src = join_paths(out_dir, file)
        if Path(src).exists():
            shutil.copy2(src, join_paths(app_root, file))
            log_info(f"  ✓ Copied {file}")
        else:
            log_warning(f"  ⚠ File not found: {file}")
    
    # Copy directories
    dirs_to_copy = ["locales", "MEIPreload"]
    for dir_name in dirs_to_copy:
        src = join_paths(out_dir, dir_name)
        if Path(src).exists():
            shutil.copytree(src, join_paths(app_root, dir_name), dirs_exist_ok=True)
            log_info(f"  ✓ Copied {dir_name}/")
    
    # Set executable permissions
    Path(join_paths(app_root, "chrome")).chmod(0o755)
    Path(join_paths(app_root, "chrome_sandbox")).chmod(0o4755)  # SUID bit
    Path(join_paths(app_root, "chrome_crashpad_handler")).chmod(0o755)
    
    # Create desktop file
    desktop_content = f"""[Desktop Entry]
Version=1.0
Name=BrowserOS
GenericName=Web Browser
Comment=Browse the World Wide Web
Exec=/opt/browseros/chrome %U
Terminal=false
Type=Application
Categories=Network;WebBrowser;
MimeType=text/html;text/xml;application/xhtml+xml;application/xml;application/vnd.mozilla.xul+xml;application/rss+xml;application/rdf+xml;image/gif;image/jpeg;image/png;x-scheme-handler/http;x-scheme-handler/https;x-scheme-handler/ftp;x-scheme-handler/chrome;video/webm;application/x-xpinstall;
Icon=browseros
"""
    
    desktop_file = Path(join_paths(usr_share, "applications", "browseros.desktop"))
    desktop_file.write_text(desktop_content)
    log_info("  ✓ Created desktop file")
    
    # Copy icon from resources
    icon_src = Path(join_paths(ctx.root_dir, "resources", "icons", "product_logo.png"))
    if icon_src.exists():
        shutil.copy2(icon_src, join_paths(icons_dir, "256x256", "apps", "browseros.png"))
        log_info("  ✓ Copied icon")
    else:
        log_warning("  ⚠ Icon not found at resources/icons/product_logo.png")
    
    # Create AppRun script
    apprun_content = """#!/bin/bash

# BrowserOS AppRun script
HERE="$(dirname "$(readlink -f "${0}")")"

# Export paths
export PATH="${HERE}/opt/browseros:${PATH}"
export LD_LIBRARY_PATH="${HERE}/opt/browseros:${LD_LIBRARY_PATH}"

# Chrome flags for better compatibility
export CHROME_DESKTOP="browseros.desktop"

# Launch Chrome
exec "${HERE}/opt/browseros/chrome" "$@"
"""
    
    apprun_file = Path(join_paths(appdir, "AppRun"))
    apprun_file.write_text(apprun_content)
    apprun_file.chmod(0o755)
    log_info("  ✓ Created AppRun script")
    
    return True


def download_appimagetool(ctx: BuildContext) -> Optional[Path]:
    """Download appimagetool if not available"""
    tool_dir = Path(join_paths(ctx.root_dir, "build", "tools"))
    tool_dir.mkdir(exist_ok=True)
    
    tool_path = Path(join_paths(tool_dir, "appimagetool-x86_64.AppImage"))
    
    if tool_path.exists():
        log_info("✓ appimagetool already available")
        return tool_path
    
    log_info("📥 Downloading appimagetool...")
    url = "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    
    cmd = ["wget", "-O", str(tool_path), url]
    success, _ = run_command(cmd)
    
    if success:
        tool_path.chmod(0o755)
        log_success("✓ Downloaded appimagetool")
        return tool_path
    else:
        log_error("Failed to download appimagetool")
        return None


def create_appimage(ctx: BuildContext, appdir: Path, output_path: Path) -> bool:
    """Create AppImage from AppDir"""
    log_info("📦 Creating AppImage...")
    
    # Download appimagetool if needed
    appimagetool = download_appimagetool(ctx)
    if not appimagetool:
        return False
    
    # Set architecture
    arch = "x86_64" if ctx.architecture == "x64" else "aarch64"
    os.environ["ARCH"] = arch
    
    # Create AppImage
    cmd = [
        str(appimagetool),
        "--comp", "gzip",  # Use gzip compression
        str(appdir),
        str(output_path)
    ]
    
    success, _ = run_command(cmd)
    
    if success:
        log_success(f"✓ Created AppImage: {output_path}")
        # Make executable
        output_path.chmod(0o755)
        return True
    else:
        log_error("Failed to create AppImage")
        return False


def package(ctx: BuildContext) -> bool:
    """Package BrowserOS for Linux as AppImage"""
    log_info(f"📦 Packaging {ctx.NXTSCAPE_APP_BASE_NAME} {ctx.nxtscape_version} for Linux ({ctx.architecture})")
    
    # Create packaging directory
    package_dir = Path(join_paths(ctx.root_dir, "out", "package", ctx.architecture))
    package_dir.mkdir(parents=True, exist_ok=True)
    
    # Prepare AppDir
    appdir = Path(join_paths(package_dir, f"{ctx.NXTSCAPE_APP_BASE_NAME}.AppDir"))
    if appdir.exists():
        safe_rmtree(appdir)
    
    if not prepare_appdir(ctx, appdir):
        return False
    
    # Define output filename
    version = ctx.nxtscape_version.replace(" ", "_")
    arch_suffix = "x86_64" if ctx.architecture == "x64" else "arm64"
    filename = f"{ctx.NXTSCAPE_APP_BASE_NAME}-{version}-{arch_suffix}.AppImage"
    output_path = Path(join_paths(package_dir, filename))
    
    # Create AppImage
    if not create_appimage(ctx, appdir, output_path):
        return False
    
    # Clean up AppDir
    safe_rmtree(appdir)
    
    # Store package path in context for GCS upload
    ctx.package_path = output_path
    
    log_success(f"✅ AppImage created: {output_path}")
    log_info(f"   Size: {output_path.stat().st_size / 1024 / 1024:.1f} MB")
    
    return True


def package_universal(contexts: List[BuildContext]) -> bool:
    """Linux doesn't support universal binaries"""
    log_warning("Universal binaries are not supported on Linux")
    return False


def sign_binaries(ctx: BuildContext) -> bool:
    """Linux doesn't require code signing like macOS/Windows"""
    log_info("Code signing is not required for Linux AppImages")
    return True