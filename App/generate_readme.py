import os

def generate_readme(root_dir=".", output_file="README.md", ignore_dirs=None):
    if ignore_dirs is None:
        ignore_dirs = {".git", "__pycache__", "venv", ".venv", ".mypy_cache"}

    def list_dir(path, prefix=""):
        lines = []
        entries = sorted(os.listdir(path))
        entries = [e for e in entries if e not in ignore_dirs]
        files = [e for e in entries if os.path.isfile(os.path.join(path, e))]
        dirs = [e for e in entries if os.path.isdir(os.path.join(path, e))]

        for d in dirs:
            lines.append(f"{prefix}├── {d}/")
            lines.extend(list_dir(os.path.join(path, d), prefix + "│   "))

        for f in files:
            lines.append(f"{prefix}├── {f}")
        return lines

    structure = list_dir(root_dir)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# 📁 Project Structure\n\n")
        f.write("```\n")
        f.write(f"{os.path.basename(os.path.abspath(root_dir))}/\n")
        for line in structure:
            f.write(f"{line}\n")
        f.write("```\n")
    print(f"✅ README.md generated at: {os.path.abspath(output_file)}")

if __name__ == "__main__":
    generate_readme(root_dir=".", output_file="README.md")
