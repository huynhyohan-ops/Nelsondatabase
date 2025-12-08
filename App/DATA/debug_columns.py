import pandas as pd

DATA_FILE = r"C:\Users\Nelson\OneDrive\Desktop\2. Areas\PricingSystem\App\DATA\Data.xlsx"

df = pd.read_excel(DATA_FILE, header=[0, 1])

print("\n=== Danh sách TÊN CỘT thực tế ===\n")
for col in df.columns:
    print(col)
