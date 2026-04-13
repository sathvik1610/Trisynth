import os
import shutil
import zipfile

def create_zip_release(release_name, files_to_include):
    print(f"📦 Packaging {release_name}...")
    release_dir = os.path.join("releases", release_name)
    
    # 1. Create clean layout directory
    if os.path.exists(release_dir):
        shutil.rmtree(release_dir)
    os.makedirs(release_dir)
    
    # 2. Copy requested codebase assets
    for item in files_to_include:
        src_path = item
        dst_path = os.path.join(release_dir, os.path.basename(item))
        if os.path.isdir(src_path):
            shutil.copytree(src_path, dst_path)
        elif os.path.exists(src_path):
            shutil.copy2(src_path, dst_path)
            
    # 3. Zip it all up
    zip_path = f"releases/{release_name}.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(release_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, release_dir)
                zipf.write(file_path, arcname)
                
    # 4. Clean up the staging dir so we only keep the zip
    shutil.rmtree(release_dir)
    
    print(f"  ✅ Built {zip_path}")
    
def main():
    if not os.path.exists("releases"):
        os.makedirs("releases")
        
    print("🚀 Building Release Packages")
    print("----------------------------")
    # Common shared docs and tests
    common_files = [
        "INSTALL.md",
        "tests/demo1_dead_code.tri",
        "tests/demo2_strength_reduction.tri",
        "tests/demo4_array.tri"
    ]
    
    # Check if user built the executables
    if not os.path.exists("dist/trisynth.exe") or not os.path.exists("dist/trisynth"):
        print("⚠️  WARNING: Executables not found in dist/. Please run PyInstaller first!")
        return

    # Linux native version
    create_zip_release("Trisynth-Linux", common_files + ["setup.sh", "dist/trisynth"])
    
    # Windows native version
    create_zip_release("Trisynth-Windows-Native", common_files + ["setup.bat", "dist/trisynth.exe"])
    
    # Windows WSL version
    create_zip_release("Trisynth-Windows-WSL", common_files + ["setup.sh", "dist/trisynth"])

if __name__ == "__main__":
    main()
