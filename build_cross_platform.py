#!/usr/bin/env python3
"""
Clip Assassin - Cross-Platform Build Script
Builds .dmg for macOS and .exe + installer for Windows
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path

BASE_DIR = Path(__file__).parent.absolute()
DIST_DIR = BASE_DIR / "dist"
BUILD_DIR = BASE_DIR / "build"
FRONTEND_DIR = BASE_DIR / "frontend"
APP_NAME = "Clip Assassin"
VERSION = "2.1.1"

def check_system():
    """Check current system platform"""
    system = platform.system()
    print(f"🖥️  Building on: {system} ({platform.machine()})")
    return system

def build_frontend():
    """Build React frontend"""
    print("\n" + "="*60)
    print("📦 Step 1: Building React Frontend...")
    print("="*60)
    
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    
    # Install dependencies if node_modules doesn't exist
    if not (FRONTEND_DIR / "node_modules").exists():
        print("📥 Installing npm dependencies...")
        subprocess.run([npm_cmd, "install"], cwd=FRONTEND_DIR, check=True)
    
    # Build frontend
    result = subprocess.run([npm_cmd, "run", "build"], cwd=FRONTEND_DIR)
    if result.returncode != 0:
        print("❌ Frontend build failed!")
        sys.exit(1)
    
    print("✅ Frontend built successfully!")
    return True

def clean_build_artifacts():
    """Clean previous build artifacts"""
    print("\n🧹 Cleaning previous build artifacts...")
    
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR, ignore_errors=True)
        print(f"   Removed {BUILD_DIR}")
    
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR, ignore_errors=True)
        print(f"   Removed {DIST_DIR}")
    
    # Keep the checked-in PyInstaller spec; only generated build outputs are disposable.

def get_icon_path():
    """Get appropriate icon for platform"""
    system = platform.system()
    
    if system == "Darwin":
        icon_path = BASE_DIR / "app_icon.icns"
    elif system == "Windows":
        icon_path = BASE_DIR / "icon.ico"
    else:
        icon_path = BASE_DIR / "app_icon.png"
    
    if icon_path.exists():
        return str(icon_path)
    return None

def build_pyinstaller(system):
    """Run PyInstaller to create executable"""
    print("\n" + "="*60)
    print("⚙️  Step 2: Running PyInstaller...")
    print("="*60)
    
    sep = ";" if system == "Windows" else ":"
    
    # Base PyInstaller command
    pyinstaller_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        f"--name={APP_NAME}",
        f"--add-data=frontend/dist{sep}frontend/dist",
        f"--add-data=presets{sep}presets",
        f"--add-data=templates{sep}templates",
        "--collect-all=webview",
        "--collect-all=keyring",
        "--collect-all=uvicorn",
        "--collect-all=fastapi",
        "--hidden-import=modules.master_ingest",
        "--hidden-import=modules.audio_tools",
        "--hidden-import=modules.export_tools",
        "--hidden-import=modules.magic_tools",
        "--hidden-import=modules.timeline_tools",
        "--hidden-import=modules.utility_tools",
        "--hidden-import=modules.badwords_tools",
        "--hidden-import=resolve_core",
        "--hidden-import=db",
        "--hidden-import=config",
        "--hidden-import=logger",
        "--hidden-import=exceptions",
        "--hidden-import=task_queue",
        "--hidden-import=ai_integration",
        "--hidden-import=plugin_system",
    ]
    
    # Add icon if available
    icon_path = get_icon_path()
    if icon_path:
        pyinstaller_cmd.extend(["--icon", icon_path])
    
    # Platform-specific options
    if system == "Darwin":
        pyinstaller_cmd.extend([
            "--osx-bundle-identifier=com.zabidstudio.clipassassin",
            "--target-architecture=universal2"
        ])
    elif system == "Windows":
        pyinstaller_cmd.extend([
            "--add-binary=C:\\Windows\\System32\\msvcp140.dll;.",
            "--version-file=version_info.txt"
        ])
    
    # Add main script
    pyinstaller_cmd.append("desktop_app.py")
    
    print(f"🔨 Running: {' '.join(pyinstaller_cmd[:5])}...")
    result = subprocess.run(pyinstaller_cmd, cwd=BASE_DIR)
    
    if result.returncode != 0:
        print("❌ PyInstaller build failed!")
        return False
    
    print("✅ PyInstaller build completed!")
    return True

def create_macos_dmg():
    """Create macOS DMG installer"""
    print("\n" + "="*60)
    print("🍎 Step 3: Creating macOS DMG...")
    print("="*60)
    
    app_path = DIST_DIR / f"{APP_NAME}.app"
    dmg_path = DIST_DIR / f"{APP_NAME}_v{VERSION}.dmg"
    
    if not app_path.exists():
        print(f"❌ App not found at {app_path}")
        return False
    
    # Remove quarantine attributes
    print("🔏 Clearing quarantine attributes...")
    subprocess.run(["xattr", "-cr", str(app_path)], check=False)
    
    # Ad-hoc codesign
    print("🔐 Codesigning application...")
    subprocess.run([
        "codesign", "--force", "--deep", "--sign", "-", 
        str(app_path)
    ], check=False)
    
    # Create DMG using hdiutil
    print("💿 Creating DMG file...")
    
    # Create temporary directory for DMG contents
    dmg_contents = DIST_DIR / "dmg_contents"
    if dmg_contents.exists():
        shutil.rmtree(dmg_contents)
    dmg_contents.mkdir()
    
    # Copy app to DMG contents
    shutil.copytree(app_path, dmg_contents / f"{APP_NAME}.app")
    
    # Create Applications symlink
    os.symlink("/Applications", dmg_contents / "Applications")
    
    # Create background folder (optional)
    bg_folder = dmg_contents / ".background"
    bg_folder.mkdir(exist_ok=True)
    
    # Create DMG
    temp_dmg = DIST_DIR / "temp.dmg"
    subprocess.run([
        "hdiutil", "create", "-volname", APP_NAME,
        "-srcfolder", str(dmg_contents),
        "-ov", "-format", "UDRO", str(temp_dmg)
    ], check=True)
    
    # Convert to compressed DMG
    subprocess.run([
        "hdiutil", "convert", str(temp_dmg),
        "-format", "UDZO", "-imagekey", "zlib-level=9",
        "-o", str(dmg_path)
    ], check=True)
    
    # Clean up
    temp_dmg.unlink(missing_ok=True)
    shutil.rmtree(dmg_contents, ignore_errors=True)
    
    if dmg_path.exists():
        print(f"✅ DMG created: {dmg_path}")
        print(f"   Size: {dmg_path.stat().st_size / (1024*1024):.2f} MB")
        return True
    else:
        print("❌ DMG creation failed!")
        return False

def create_windows_installer():
    """Create Windows installer using Inno Setup or NSIS"""
    print("\n" + "="*60)
    print("🪟 Step 3: Creating Windows Installer...")
    print("="*60)
    
    exe_path = DIST_DIR / APP_NAME / f"{APP_NAME}.exe"
    
    if not exe_path.exists():
        print(f"❌ Executable not found at {exe_path}")
        return False
    
    # Create ISS file for Inno Setup
    iss_content = f"""
[Setup]
AppId={{{generate_guid()}}}
AppName={APP_NAME}
AppVersion={VERSION}
AppPublisher=ZabidStudio
DefaultDirName={{autopf}}\\{APP_NAME}
DefaultGroupName={APP_NAME}
OutputDir={DIST_DIR.absolute()}
OutputBaseFilename={APP_NAME}_v{VERSION}_Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
SetupIconFile={BASE_DIR / 'icon.ico'}
UninstallDisplayIcon={{app}}\\{APP_NAME}.exe

[Files]
Source: "{exe_path}"; DestDir: "{{app}}"
Source: "{DIST_DIR / APP_NAME / '_internal\\*'}"; DestDir: "{{app}}\\_internal"; Flags: recursesubdirs
Source: "{BASE_DIR / 'frontend/dist\\*'}"; DestDir: "{{app}}\\frontend/dist"; Flags: recursesubdirs
Source: "{BASE_DIR / 'presets\\*'}"; DestDir: "{{app}}\\presets"; Flags: recursesubdirs
Source: "{BASE_DIR / 'templates\\*'}"; DestDir: "{{app}}\\templates"; Flags: recursesubdirs

[Icons]
Name: "{{group}}\\{APP_NAME}"; Filename: "{{app}}\\{APP_NAME}.exe"
Name: "{{autodesktop}}\\{APP_NAME}"; Filename: "{{app}}\\{APP_NAME}.exe"

[Run]
Filename: "{{app}}\\{APP_NAME}.exe"; Description: "{{cm:LaunchProgram,{APP_NAME}}}"; Flags: nowait postinstall skipifsilent
"""
    
    iss_file = BASE_DIR / "clip_assassin_installer.iss"
    with open(iss_file, "w", encoding="utf-8") as f:
        f.write(iss_content)
    
    print(f"📝 Created Inno Setup script: {iss_file}")
    print("💡 To build the installer, run:")
    print(f'   iscc.exe "{iss_file}"')
    print("\n   Or use the GUI: Open '{iss_file}' in Inno Setup Compiler")
    
    return True

def generate_guid():
    """Generate a simple GUID for Inno Setup"""
    import uuid
    return str(uuid.uuid4()).upper()

def verify_build(system):
    """Verify the build outputs"""
    print("\n" + "="*60)
    print("✅ Step 4: Verifying Build...")
    print("="*60)
    
    success = True
    
    if system == "Darwin":
        app_path = DIST_DIR / f"{APP_NAME}.app"
        dmg_path = DIST_DIR / f"{APP_NAME}_v{VERSION}.dmg"
        
        if app_path.exists():
            print(f"✅ App bundle exists: {app_path}")
            size = sum(f.stat().st_size for f in app_path.rglob('*') if f.is_file())
            print(f"   Size: {size / (1024*1024):.2f} MB")
        else:
            print(f"❌ App bundle missing: {app_path}")
            success = False
        
        if dmg_path.exists():
            print(f"✅ DMG exists: {dmg_path}")
            print(f"   Size: {dmg_path.stat().st_size / (1024*1024):.2f} MB")
        else:
            print(f"⚠️  DMG not created (optional)")
    
    elif system == "Windows":
        exe_path = DIST_DIR / APP_NAME / f"{APP_NAME}.exe"
        
        if exe_path.exists():
            print(f"✅ Executable exists: {exe_path}")
            print(f"   Size: {exe_path.stat().st_size / (1024*1024):.2f} MB")
        else:
            print(f"❌ Executable missing: {exe_path}")
            success = False
    
    return success

def create_readme():
    """Create build README"""
    readme = f"""# {APP_NAME} v{VERSION} - Build Outputs

## Build Information
- **Build Date**: {subprocess.getoutput('date')}
- **Platform**: {platform.system()} ({platform.machine()})
- **Python Version**: {sys.version}

## Files Included

### macOS
- `{APP_NAME}_v{VERSION}.dmg` - Drag-and-drop installer

### Windows
- `{APP_NAME}/` - Portable executable folder
- `{APP_NAME}_v{VERSION}_Setup.exe` - Inno Setup installer (requires separate build)

## Installation

### macOS
1. Open `{APP_NAME}_v{VERSION}.dmg`
2. Drag `{APP_NAME}` to Applications folder
3. Launch from Applications

### Windows
1. Run `{APP_NAME}_v{VERSION}_Setup.exe`
2. Follow installation wizard
3. Launch from Start Menu or Desktop

## System Requirements

### macOS
- macOS 10.15 (Catalina) or later
- DaVinci Resolve 17+ installed
- Python 3.8+ (included)

### Windows
- Windows 10 or later
- DaVinci Resolve 17+ installed
- Visual C++ Redistributable (included)
- Python 3.8+ (included)

## Troubleshooting

If the app doesn't launch:
- macOS: Right-click → Open to bypass Gatekeeper
- Windows: Run as Administrator
- Ensure DaVinci Resolve is installed and running
"""
    
    readme_path = DIST_DIR / "BUILD_README.md"
    with open(readme_path, "w") as f:
        f.write(readme)
    
    print(f"📄 Created build README: {readme_path}")

def main():
    print("="*60)
    print(f"🚀 {APP_NAME} v{VERSION} - Cross-Platform Build Script")
    print("="*60)
    
    # Check system
    system = check_system()
    
    # Build frontend
    build_frontend()
    
    # Clean previous builds
    clean_build_artifacts()
    
    # Run PyInstaller
    if not build_pyinstaller(system):
        sys.exit(1)
    
    # Platform-specific packaging
    if system == "Darwin":
        create_macos_dmg()
    elif system == "Windows":
        create_windows_installer()
    else:
        print(f"\n⚠️  Platform {system} not fully supported yet")
        print("   Linux build creates portable executable only")
    
    # Verify build
    verify_build(system)
    
    # Create README
    create_readme()
    
    print("\n" + "="*60)
    print("🎉 BUILD COMPLETE!")
    print("="*60)
    print(f"\n📁 Output directory: {DIST_DIR}")
    print("\nNext steps:")
    if system == "Darwin":
        print("1. Test the DMG on a clean macOS system")
        print("2. Notarize the app with Apple Developer ID")
        print("3. Upload to GitHub Releases")
    elif system == "Windows":
        print("1. Compile the .iss file with Inno Setup")
        print("2. Test the installer on a clean Windows system")
        print("3. Sign the executable with code signing certificate")
        print("4. Upload to GitHub Releases")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
