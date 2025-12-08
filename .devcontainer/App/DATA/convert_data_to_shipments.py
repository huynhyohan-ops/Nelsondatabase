import pandas as pd
import os

# ⚙️ Đường dẫn cố định
BASE_PATH = r"C:\Users\Nelson\OneDrive\Desktop\2. Areas\PricingSystem\App\DATA"
DATA_FILE = os.path.join(BASE_PATH, "Data.xlsx")
SHIPMENTS_FILE = os.path.join(BASE_PATH, "Shipments.xlsx")

# 🎯 Map tên Volume trong file thật sang Container Type chuẩn
volume_col_map = {
    "AIR": "AIR",
    "LCL": "LCL",
    "20RF": "20RF",
    "20'": "20GP",
    "40'": "40GP",
    "HC": "40HQ",
    "40RF": "40RF",
    45: "45",
}

def get_volume_unit(container_type):
    if container_type in ["20GP", "20RF"]:
        return 1
    elif container_type in ["40GP", "40HQ", "45", "40NOR"]:
        return 2
    return 1

# 🧾 Đọc toàn bộ sheet trong Data.xlsx
xls = pd.ExcelFile(DATA_FILE)
records = []

for sheet_name in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet_name, header=[0, 1])
    print(f"🔄 Đang xử lý sheet: {sheet_name} với {len(df)} dòng")

    for i, row in df.iterrows():
        etd_raw = row.get(("ETD", "Unnamed: 4_level_1"), "")
        etd = pd.to_datetime(etd_raw, format="%d-%b-%y", errors='coerce')

        if pd.isna(etd):
            print(f"[⚠️ Warning] Bỏ qua dòng {i+2} (sheet {sheet_name}) vì ETD không hợp lệ: {etd_raw}")
            continue

        eta = pd.to_datetime(row.get(("ETA", "Unnamed: 5_level_1")), format="%d-%b-%y", errors='coerce')
        month_str = etd.strftime("%b %Y")

        for vol_key, container_type in volume_col_map.items():
            qty = row.get(("Volume ", vol_key))
            if pd.notna(qty) and qty > 0:
                record = {
                    "Customer": row.get(("SHIPPER/\nCONSIGNEE", "Unnamed: 1_level_1"), ""),
                    "Customer Type": "",
                    "Routing": f"{row.get(('POL/POD', 'Unnamed: 2_level_1'), '')}-{row.get(('FINAL DEST', 'Unnamed: 3_level_1'), '')}",
                    "Bkg No": "",
                    "Hbl No": row.get(("HBL", "Unnamed: 7_level_1"), ""),
                    "ETD": etd,
                    "ETA": eta,
                    "ATA": "",
                    "Container Type": container_type,
                    "Quantity": qty,
                    "Volume": qty * get_volume_unit(container_type),
                    "Status": "Confirmed",
                    "Selling Rate": row.get(("Selling", "Unnamed: 18_level_1"), 0),
                    "Buying Rate": row.get(("Buying ", "Unnamed: 17_level_1"), 0),
                    "Profit": row.get(("Net\nProfit", "Unnamed: 23_level_1"), 0),
                    "Si": "",
                    "Cy": "",
                    "Carrier": "",
                    "Hdl Fee Carrier": "",
                    "Status_Calc": "ON TIME",
                    "Month": month_str,
                    "Etd_Original": month_str,
                    "Delay_Log": "0",
                    "Progress ETA": "0",
                    "Sort_Order": "99",
                }
                records.append(record)

# 🧱 Tạo DataFrame chuyển đổi
df_converted = pd.DataFrame(records)

# 💾 Ghi sheet theo từng tháng
with pd.ExcelWriter(SHIPMENTS_FILE, engine="openpyxl", mode="a", if_sheet_exists="overlay") as writer:
    for month in df_converted["Month"].dropna().unique():
        df_month = df_converted[df_converted["Month"] == month]

        # Nếu sheet tồn tại thì ghép thêm, không thì tạo mới
        try:
            df_existing = pd.read_excel(SHIPMENTS_FILE, sheet_name=month)
            df_merged = pd.concat([df_existing, df_month], ignore_index=True)
        except ValueError:
            df_merged = df_month.copy()

        df_merged.to_excel(writer, sheet_name=month, index=False)

print("✅ Đã chuyển đổi thành công và ghi dữ liệu vào Shipments.xlsx.")
