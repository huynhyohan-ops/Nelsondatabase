
import pandas as pd
from pathlib import Path

# Cấu hình chung
DATA_PATH = Path(__file__).parent.parent / "DATA" / "Shipments.xlsx"

# Hàm đọc dữ liệu từ file Excel theo sheet name
def load_shipments(sheet_name):
    df = pd.read_excel(DATA_PATH, sheet_name=sheet_name)

    # Chuẩn hóa tên cột
    df.columns = df.columns.map(str).str.strip()

    # Loại bỏ các ký tự không cần thiết
    df.columns = df.columns.str.encode('ascii', 'ignore').str.decode('utf-8')

    # Bắt buộc các cột cần có
    required = {'ETD', 'ETA', 'ATA'}
    if not required.issubset(df.columns):
        raise ValueError(f"Missing required columns: {required - set(df.columns)}")

    return df

# Hàm lưu dữ liệu lại vào file (ghi đè sheet)
def save_shipments(sheet_name, df):
    # Ghi đè lên đúng sheet
    with pd.ExcelWriter(DATA_PATH, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)

# Hàm tính volume theo Container Type
def calc_volume(row):
    if pd.isna(row["Container Type"]) or pd.isna(row["Quantity"]):
        return 0
    ct = str(row["Container Type"]).upper()
    q = float(row["Quantity"])
    if ct in ["40GP", "40HQ", "40RF", "45", "40NOR"]:
        return 2 * q
    elif ct == "20GP":
        return 1 * q
    else:
        return 0

# Hàm tính profit
def calc_profit(row):
    try:
        return (float(row["Selling Rate"]) - float(row["Buying Rate"])) * float(row["Quantity"])
    except:
        return 0
def calculate_all_columns(df):
    df["Volume"] = df.apply(calc_volume, axis=1)
    df["Profit"] = df.apply(calc_profit, axis=1)
    return df

from openpyxl import load_workbook

def get_visible_sheets():
    wb = load_workbook(DATA_PATH, read_only=True)
    return [sheet.title for sheet in wb.worksheets if sheet.sheet_state == 'visible']

