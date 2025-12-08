# fix_indent.py
from pathlib import Path

file_path = Path("pricing_quote_page.py")  # Không cần cả đường dẫn
new_lines = []

with file_path.open(encoding="utf-8") as f:
    for line in f:
        new_lines.append(line.replace('\t', '    '))  # Thay tab bằng 4 space

file_path.write_text(''.join(new_lines), encoding="utf-8")
print("✅ Đã chuyển TAB → 4 spaces thành công.")
