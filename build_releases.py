import os
import zipfile

def _add_file(zipf, src_path, arcname):
    """Add a single file to the zip with the given archive name."""
    zipf.write(src_path, arcname)

def _add_item(zipf, item_path, arc_prefix=""):
    """Add a file or entire directory tree directly into the zip."""
    name = os.path.basename(item_path)
    if os.path.isdir(item_path):
        for root, dirs, files in os.walk(item_path):
            for file in files:
                abs_path = os.path.join(root, file)
                # Preserve directory structure inside zip
                rel = os.path.relpath(abs_path, os.path.dirname(item_path))
                arc = os.path.join(arc_prefix, rel) if arc_prefix else rel
                zipf.write(abs_path, arc)
    elif os.path.exists(item_path):
        arc = os.path.join(arc_prefix, name) if arc_prefix else name
        zipf.write(item_path, arc)

def create_zip_release(release_name, files_to_include):
    print(f"📦 Packaging {release_name}...")
    os.makedirs("releases", exist_ok=True)
    zip_path = os.path.join("releases", f"{release_name}.zip")

    # Write directly to zip — no staging directory, so no Windows file-lock issues
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for item in files_to_include:
            _add_item(zipf, item)

    print(f"  ✅ Built {zip_path}")

def main():
    print("🚀 Building Release Packages")
    print("----------------------------")

    # Common shared docs and demo files
    common_files = [
        "docs",
        "tests/demo1_dead_code.tri",
        "tests/demo2_strength_reduction.tri",
        "tests/demo4_array.tri",
    ]

    # Check executables exist
    if not os.path.exists("dist/trisynth.exe") or not os.path.exists("dist/trisynth"):
        print("⚠️  WARNING: Executables not found in dist/. Please run PyInstaller first!")
        return

    # Linux — include pre-built nasm (bin/linux/nasm) so trisynth works without compiling
    create_zip_release("Trisynth-Linux",
                       common_files + ["setup.sh", "dist/trisynth", "bin"])

    # Windows native
    create_zip_release("Trisynth-Windows-Native",
                       common_files + ["setup.bat", "dist/trisynth.exe"])

    # Windows WSL — same as Linux release; trisynth (Linux ELF) + pre-built nasm
    create_zip_release("Trisynth-Windows-WSL",
                       common_files + ["setup.sh", "dist/trisynth", "bin"])

if __name__ == "__main__":
    main()
