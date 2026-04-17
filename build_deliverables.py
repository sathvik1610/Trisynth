import os
import shutil

# Ensure directory exists
out_dir = r"docs\deliverables"
os.makedirs(out_dir, exist_ok=True)

# 1. Technical Documentation
tech_doc_path = os.path.join(out_dir, "Technical_Documentation.md")
with open("README.md", "r", encoding="utf-8") as f:
    readme_content = f.read()

# Split README to get everything from "## 4. Compiler Architecture"
if "## 4. Compiler Architecture" in readme_content:
    tech_part = "## 4. Compiler Architecture" + readme_content.split("## 4. Compiler Architecture", 1)[1]
else:
    tech_part = readme_content

with open(r"docs\technical_documentation\implementation_guide_backend.md", "r", encoding="utf-8") as f:
    backend_content = f.read()

with open(tech_doc_path, "w", encoding="utf-8") as f:
    f.write("# Trisynth Technical Documentation\n\n")
    f.write(tech_part)
    f.write("\n\n---\n\n")
    f.write(backend_content)

print("Created Technical_Documentation.md")

# 2. Language Manual
lang_doc_path = os.path.join(out_dir, "Language_Manual.md")
shutil.copyfile(r"docs\technical_documentation\language_manual.md", lang_doc_path)
print("Created Language_Manual.md")

# 3. Installation Manual
inst_doc_path = os.path.join(out_dir, "Installation_Manual.md")
with open("INSTALL.md", "r", encoding="utf-8") as f:
    install_c = f.read()
with open("SETUP.md", "r", encoding="utf-8") as f:
    setup_c = f.read()

with open(inst_doc_path, "w", encoding="utf-8") as f:
    f.write(install_c)
    f.write("\n\n---\n\n")
    f.write(setup_c)

print("Created Installation_Manual.md")

