from pathlib import Path
import pandas as pd

# Đường dẫn file Shipment
DATA_PATH = Path(
    r"C:\Users\Nelson\OneDrive\Desktop\2. Areas\PricingSystem\App\DATA\Shipments.xlsx"
)

def load_all_sheets():
    """
    Load tất cả các sheet từ file Excel Shipments.xlsx.
    Trả về dict dạng:
    {
        "Dec 2025": DataFrame,
        "Jan 2026": DataFrame,
        ...
    }
    """

    if not DATA_PATH.exists():
        raise FileNotFoundError(f"[ERROR] Không tìm thấy file Excel: {DATA_PATH}")

    xls = pd.ExcelFile(DATA_PATH)
    sheet_data = {}

    for sheet_name in xls.sheet_names:
        # Đọc sheet, parse ngày nhưng KHÔNG dùng dayfirst ở đây
        df = pd.read_excel(
            xls,
            sheet_name=sheet_name,
            parse_dates=["ETD", "ETA", "ATA"],   # parse thẳng
        )

        # Xử lý ngày theo DD/MM/YYYY (nếu cần)
        for col in ["ETD", "ETA", "ATA"]:
            df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce")

        # Thêm label tháng từ tên sheet
        df["Month"] = sheet_name

        # Chuẩn hóa lại cột margin
        if "Profit" in df.columns:
            df["margin"] = df["Profit"]
        else:
            df["margin"] = 0

        # Tạo period tháng để dùng cho KPI
        df["ETD_Month"] = df["ETD"].dt.to_period("M")

        sheet_data[sheet_name] = df

    return sheet_data
