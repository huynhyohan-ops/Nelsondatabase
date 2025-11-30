import os
import pandas as pd
from openpyxl.styles import PatternFill

# === Cấu hình ===
base_dir = r"C:\Users\Nelson\OneDrive\Desktop\2. Areas\PricingSystem"

raw_dir = os.path.join(base_dir, "Raw")
data_dir = os.path.join(base_dir, "Data")

# MASTER FILE BÂY GIỜ LƯU TRONG THƯ MỤC Data
master_file = os.path.join(data_dir, "Master_FullPricing.xlsx")

# File PUC_SOC.xlsx nằm trong thư mục Data
puc_file = os.path.join(data_dir, "PUC_SOC.xlsx")

os.makedirs(raw_dir, exist_ok=True)
os.makedirs(data_dir, exist_ok=True)

# Các hãng áp dụng PUC cho giá SOC
SOC_CARRIERS = ["CMA", "ONE", "YML"]


# ========= HÀM TIỆN ÍCH =========
def read_excel_safe(filepath, sheet_name="RATE", **kwargs):
    """
    Đọc Excel, ưu tiên sheet 'RATE'. Nếu không có thì đọc sheet đầu tiên (index 0).
    """
    try:
        return pd.read_excel(filepath, sheet_name=sheet_name, **kwargs)
    except ValueError:
        return pd.read_excel(filepath, sheet_name=0, **kwargs)


def get_col_safe(df, idx):
    """Lấy cột theo index, nếu không có thì trả None."""
    if idx is None:
        return None
    if idx < 0 or idx >= df.shape[1]:
        return None
    return df.iloc[:, idx]


def clean_amount_series(s):
    """Chuẩn hóa chuỗi Amount về số (bỏ dấu phẩy)."""
    if s is None:
        return None
    s = (
        s.astype(str)
        .str.replace(",", "", regex=False)  # bỏ thousand separator
        .str.strip()
    )
    return pd.to_numeric(s, errors="coerce")


def format_short_date(series):
    """
    Chuẩn hóa ngày về dạng '14-MAR' (DD-MMM, viết hoa, không năm, không giờ).
    Nếu không đọc được ngày → NaT -> trả về NaN.
    """
    dt = pd.to_datetime(series, errors="coerce")
    return dt.dt.strftime("%d-%b").str.upper()


def normalize_container(cont: str) -> str:
    """
    Map các dạng cont về nhóm chính:
    20GP ~ 20DC, 20DV
    40HQ ~ 40HC
    40GP ~ 40DV, 40DC
    """
    if pd.isna(cont):
        return ""
    c = str(cont).strip().upper().replace(" ", "").replace("'", "")
    if c in ["20", "20FT", "20DC", "20DV", "20GP"]:
        return "20GP"
    if c in ["40", "40FT", "40DC", "40DV", "40GP"]:
        return "40GP"
    if c in ["40HC", "40HQ", "40HCFT", "40HQFT"]:
        return "40HQ"
    return c


# ========= PARSER CHO FAK & ONE_SPECIAL RATE =========
def parse_fak_or_fix(raw_df, rate_type, source_file):
    """
    Cấu trúc FAK & ONE_SPECIAL RATE theo mapping:
    A1–A2 (col 0): POL
    B1–B2 (col 1): POD
    C1–C2 (col 2): PlaceOfDelivery
    D1–D2 (col 3): Routing note -> Keep (phân biệt hợp đồng)
    E1–E2 (col 4): ROUTING -> Ignore
    F1–F2 (col 5): Carrier
    G1–G2 (col 6): Effective Date
    H1–H2 (col 7): Expiration Date
    I1–I2 (col 8): Group rate / Service note
    J1–J2 (col 9): Commodity (chỉ FAK dùng)
    K1–K2 (col 10): Transit time / Group code -> Ignore
    L1–L2 (col 11): Contract Identifier
    M1–Q2 (col 12–16): ALL-IN-COST 20GP, 40GP, 40HQ, 45HQ, 40NOR

    *** PSS/PUC ***
    AM1–AP2 (col 38–41):
      - Hàng 1: "PSS/PUC"
      - Hàng 2: 20GP, 40GP, 40HQ, 45'HQ
    → Đây là các cột PUC/PSS input. Ta dùng để tự TRỪ PUC cũ khỏi ALL-IN
      cho các dòng SOC của CMA/ONE/YML, thay cho việc phải xoá tay trong FAK_RAW.

    LƯU Ý: 45'HQ KHÔNG TRỪ PUC (theo yêu cầu mới).
    """
    if raw_df.shape[0] < 3:
        return pd.DataFrame()

    # Bỏ 2 hàng header, dữ liệu bắt đầu từ dòng 3
    df = raw_df.iloc[2:].reset_index(drop=True)

    POL = get_col_safe(df, 0)
    POD = get_col_safe(df, 1)

    Place = get_col_safe(df, 2)
    if Place is not None:
        Place = Place.astype(str).str.strip()

    RoutingNote = get_col_safe(df, 3)
    Carrier = get_col_safe(df, 5)
    Eff = get_col_safe(df, 6)
    Exp = get_col_safe(df, 7)
    Commodity = get_col_safe(df, 9) if rate_type == "FAK" else None
    Contract = get_col_safe(df, 11)

    # ALL-IN hiện tại (còn đang bao gồm PUC "sai" trong file FAK gốc)
    c20 = get_col_safe(df, 12)
    c40 = get_col_safe(df, 13)
    c40hq = get_col_safe(df, 14)
    c45 = get_col_safe(df, 15)
    c40nor = get_col_safe(df, 16)

    # PSS/PUC input (AM–AP: col 38–41)
    puc20_raw = get_col_safe(df, 38)  # 20GP
    puc40_raw = get_col_safe(df, 39)  # 40GP
    puc40hq_raw = get_col_safe(df, 40)  # 40HQ
    puc45_raw = get_col_safe(df, 41)  # 45HQ (KHÔNG DÙNG ĐỂ TRỪ)

    # Chuẩn hóa về số cho ALL-IN
    c20 = clean_amount_series(c20)
    c40 = clean_amount_series(c40)
    c40hq = clean_amount_series(c40hq)
    c45 = clean_amount_series(c45)
    c40nor = clean_amount_series(c40nor)

    # Chuẩn hóa về số cho PUC
    puc20 = clean_amount_series(puc20_raw)
    puc40 = clean_amount_series(puc40_raw)
    puc40hq = clean_amount_series(puc40hq_raw)
    puc45 = clean_amount_series(puc45_raw)  # vẫn đọc, nhưng KHÔNG trừ vào 45HQ

    price_df = pd.DataFrame(
        {
            "POL": POL,
            "POD": POD,
            "PlaceOfDelivery": Place,
            "RoutingNote": RoutingNote,
            "Carrier": Carrier,
            "EffectiveDate": Eff,
            "ExpirationDate": Exp,
            "ContractIdentifier": Contract,
            "CommodityType": Commodity,
            "20GP": c20,
            "40GP": c40,
            "40HQ": c40hq,
            "45HQ": c45,
            "40NOR": c40nor,
        }
    )

    # --------- TỰ ĐỘNG TRỪ PUC TRONG FAK_RAW (CMA/ONE/YML - SOC) ---------
    # Gán PUC series vào price_df để cùng index
    price_df["PUC20"] = puc20 if puc20 is not None else 0
    price_df["PUC40"] = puc40 if puc40 is not None else 0
    price_df["PUC40HQ"] = puc40hq if puc40hq is not None else 0
    price_df["PUC45"] = puc45 if puc45 is not None else 0  # KHÔNG TRỪ VÀO 45HQ

    # Chỉ áp dụng cho các carrier trong list SOC_CARRIERS và RoutingNote có chữ "SOC"
    mask_carrier = price_df["Carrier"].astype(str).str.upper().isin(
        [c.upper() for c in SOC_CARRIERS]
    )
    mask_soc_note = price_df["RoutingNote"].astype(str).str.upper().str.contains(
        "SOC", na=False
    )
    mask_apply_puc = mask_carrier & mask_soc_note

    if mask_apply_puc.any():
        # TRỪ PUC CHỈ CHO 20GP, 40GP, 40HQ
        for cont_col, puc_col in [
            ("20GP", "PUC20"),
            ("40GP", "PUC40"),
            ("40HQ", "PUC40HQ"),
        ]:
            if cont_col in price_df.columns:
                price_df.loc[mask_apply_puc, cont_col] = (
                    price_df.loc[mask_apply_puc, cont_col].fillna(0)
                    - price_df.loc[mask_apply_puc, puc_col].fillna(0)
                )

    # Xoá cột PUC helper để không đi theo xuống dưới
    price_df = price_df.drop(
        columns=["PUC20", "PUC40", "PUC40HQ", "PUC45"], errors="ignore"
    )
    # ----------------------------------------------------------------------

    value_cols = ["20GP", "40GP", "40HQ", "45HQ", "40NOR"]
    value_cols = [c for c in value_cols if c in price_df.columns]

    df_out = (
        price_df.melt(
            id_vars=[
                "POL",
                "POD",
                "PlaceOfDelivery",
                "RoutingNote",
                "Carrier",
                "EffectiveDate",
                "ExpirationDate",
                "ContractIdentifier",
                "CommodityType",
            ],
            value_vars=value_cols,
            var_name="ContainerType",
            value_name="Amount",
        )
        .dropna(subset=["Amount"])
    )

    # ONE_SPECIAL RATE: gán CommodityType cố định
    if rate_type == "ONE_SPECIAL RATE":
        df_out["CommodityType"] = "FIX RATE"

    # Rút gọn / gom CommodityType cho ONE
    mask_one = df_out["Carrier"].astype(str).str.upper().str.contains("ONE", na=False)
    if mask_one.any():
        comm = df_out.loc[mask_one, "CommodityType"].astype(str)

        # GARMENT -> FAK Straight
        m_gar = comm.str.contains("GARMENT", case=False, na=False)
        comm.loc[m_gar] = "FAK: TPE1 - FAK Straight"

        # FAK: TPE1 - FAK STRAIGHT (.) -> FAK: TPE1 - FAK Straight
        m1 = comm.str.contains("FAK: TPE1 - FAK STRAIGHT", case=False, na=False)
        comm.loc[m1] = "FAK: TPE1 - FAK Straight"

        # REEFER FAK (NOT VALID FOR SEASONAL.) -> REEFER FAK
        m2 = comm.str.contains("REEFER FAK", case=False, na=False)
        comm.loc[m2] = "REEFER FAK"

        # SHORT TERM GDSM (GENERAL DEPARTMENT STORE MERCHANDISE)
        m3 = comm.str.contains("SHORT TERM GDSM", case=False, na=False)
        comm.loc[m3] = "SHORT TERM GDSM"

        # S1– TPE9 – Group SOC: .
        m4 = comm.str.contains("TPE9", case=False, na=False) & comm.str.contains(
            "GROUP SOC", case=False, na=False
        )
        comm.loc[m4] = "S1– TPE9 – Group SOC"

        df_out.loc[mask_one, "CommodityType"] = comm

    # KHÔNG map REEFER sang 20RF / 40RF

    df_out["Amount"] = clean_amount_series(df_out["Amount"])
    df_out["RateType"] = rate_type
    df_out["SourceFile"] = source_file
    df_out = df_out.drop_duplicates()

    final_cols = [
        "POL",
        "POD",
        "PlaceOfDelivery",
        "RoutingNote",
        "Carrier",
        "EffectiveDate",
        "ExpirationDate",
        "ContractIdentifier",
        "ContainerType",
        "Amount",
        "CommodityType",
        "RateType",
        "SourceFile",
    ]
    return df_out[final_cols]


# ========= PARSER CHO HPL_SCFI =========
def parse_scfi(raw_df, source_file):
    """
    HPL_SCFI:
    A: POL
    B: POD
    C: PlaceOfDelivery
    D: Effective
    E: Expiration
    F–H: 20, 40, 40HC (map 20GP, 40GP, 40HQ)
    """
    if raw_df.shape[0] < 3:
        return pd.DataFrame()

    df = raw_df.iloc[2:].reset_index(drop=True)

    POL = get_col_safe(df, 0)
    POD = get_col_safe(df, 1)

    Place = get_col_safe(df, 2)
    if Place is not None:
        Place = Place.astype(str).str.strip()

    Eff = get_col_safe(df, 3)
    Exp = get_col_safe(df, 4)
    c20 = get_col_safe(df, 5)
    c40 = get_col_safe(df, 6)
    c40hq = get_col_safe(df, 7)

    price_df = pd.DataFrame(
        {
            "POL": POL,
            "POD": POD,
            "PlaceOfDelivery": Place,
            "RoutingNote": None,
            "Carrier": "HPL",
            "EffectiveDate": Eff,
            "ExpirationDate": Exp,
            "ContractIdentifier": None,
            "CommodityType": None,
            "20GP": c20,
            "40GP": c40,
            "40HQ": c40hq,
        }
    )

    df_out = (
        price_df.melt(
            id_vars=[
                "POL",
                "POD",
                "PlaceOfDelivery",
                "RoutingNote",
                "Carrier",
                "EffectiveDate",
                "ExpirationDate",
                "ContractIdentifier",
                "CommodityType",
            ],
            value_vars=["20GP", "40GP", "40HQ"],
            var_name="ContainerType",
            value_name="Amount",
        )
        .dropna(subset=["Amount"])
    )

    df_out["Amount"] = clean_amount_series(df_out["Amount"])
    df_out["RateType"] = "HPL_SCFI"
    df_out["SourceFile"] = source_file

    final_cols = [
        "POL",
        "POD",
        "PlaceOfDelivery",
        "RoutingNote",
        "Carrier",
        "EffectiveDate",
        "ExpirationDate",
        "ContractIdentifier",
        "ContainerType",
        "Amount",
        "CommodityType",
        "RateType",
        "SourceFile",
    ]
    return df_out[final_cols]


# ========= XÁC ĐỊNH RATE TYPE TỪ TÊN FILE =========
def detect_rate_type_from_name(fname: str) -> str | None:
    """Xác định RateType từ tên file, ONE_SPECIAL RATE thay thế ONE_FIX."""
    name_upper = fname.upper()

    if "SCFI" in name_upper:
        return "HPL_SCFI"
    if "FAK" in name_upper:
        return "FAK"

    # Nhận diện ONE_SPECIAL RATE (tên file mới)
    if "ONE_SPECIAL RATE" in name_upper:
        return "ONE_SPECIAL RATE"
    if "ONE_SPECIAL" in name_upper and "RATE" in name_upper:
        return "ONE_SPECIAL RATE"

    # Backward-compatible: các file cũ có chữ FIX/ONE_FIX vẫn map về ONE_SPECIAL RATE
    if "ONE_FIX" in name_upper:
        return "ONE_SPECIAL RATE"
    if "ONE FIX" in name_upper:
        return "ONE_SPECIAL RATE"
    if "ONE-FIX" in name_upper:
        return "ONE_SPECIAL RATE"
    if "FIX" in name_upper and "ONE" in name_upper:
        return "ONE_SPECIAL RATE"
    if "FIX" in name_upper:
        return "ONE_SPECIAL RATE"

    return None


# ========= LOAD PUC =========
def load_puc():
    if not os.path.exists(puc_file):
        print(f"[!] Không tìm thấy file PUC_SOC.xlsx tại: {puc_file} -> bỏ qua bước PUC.")
        return None

    df = pd.read_excel(puc_file, sheet_name="PUC_SOC")
    df.columns = [str(c).strip() for c in df.columns]

    required = ["PlaceOfDelivery", "20DC", "40HC"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"PUC_SOC.xlsx thiếu cột: {missing}")

    for col in ["20DC", "40HC"]:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.strip()
            .replace({"": pd.NA, "TBA": pd.NA, "N/A": pd.NA})
            .astype(float)
        )

    df["CityKey"] = df["PlaceOfDelivery"].astype(str).str.upper().str.strip()
    return df


def build_city_key_for_master(pod: str, puc_cities_upper: list[str]) -> str:
    """
    Ưu tiên:
    1. Nếu POD chứa tên city PUC nào -> lấy city đó
    2. Ngược lại -> phần trước '(' rồi trước ',' làm city
    """
    if pd.isna(pod):
        return ""
    up = str(pod).upper()
    matches = [city for city in puc_cities_upper if city in up]
    if matches:
        return sorted(matches, key=len, reverse=True)[0]
    base = up.split("(")[0]
    base = base.split(",")[0].strip()
    return base


def apply_puc_to_df(df_master: pd.DataFrame) -> pd.DataFrame:
    """
    Cộng PUC trực tiếp vào Amount cho CMA/ONE/YML SOC.
    Không tạo thêm cột trong output. Chỉ sửa Amount.
    KHÔNG CỘNG PUC CHO 45HQ (do mapping chỉ cho 20GP & 40GP/40HQ).
    """
    puc_df = load_puc()
    if puc_df is None:
        return df_master

    df = df_master.copy()
    df["ContainerNorm"] = df["ContainerType"].apply(normalize_container)

    if "PlaceOfDelivery" not in df.columns:
        raise ValueError("Master không có cột PlaceOfDelivery")

    puc_cities_upper = puc_df["CityKey"].dropna().unique().tolist()
    df["CityKey"] = df["PlaceOfDelivery"].apply(
        lambda x: build_city_key_for_master(x, puc_cities_upper)
    )

    df = df.merge(
        puc_df[["CityKey", "20DC", "40HC"]],
        on="CityKey",
        how="left",
        suffixes=("", "_PUC"),
    )

    def pick_puc(row):
        c = row["ContainerNorm"]
        if c == "20GP":
            return row["20DC"]
        if c in ["40GP", "40HQ"]:
            return row["40HC"]
        return None  # 45HQ, 40NOR,... -> không cộng PUC

    df["PUC_selected"] = df.apply(pick_puc, axis=1)

    mask_carrier = df["Carrier"].astype(str).str.upper().isin(
        [c.upper() for c in SOC_CARRIERS]
    )
    mask_soc_note = df["RoutingNote"].astype(str).str.upper().str.contains(
        "SOC", na=False
    )
    mask_apply = mask_carrier & mask_soc_note

    puc_series = df.loc[mask_apply, "PUC_selected"].fillna(0)
    df.loc[mask_apply, "Amount"] = df.loc[mask_apply, "Amount"] + puc_series

    df = df.drop(
        columns=[
            c
            for c in ["ContainerNorm", "CityKey", "20DC", "40HC", "PUC_selected"]
            if c in df.columns
        ]
    )

    return df


# ========= CHUẨN HÓA COMMODITY THEO HÃNG =========
def normalize_commodity(df_master: pd.DataFrame) -> pd.DataFrame:
    """
    Chuẩn hóa CommodityType theo từng hãng:
    - COSCO
      FAK (Excluding Garment) => FAK
      Garments/Textile/Consol => GARMENT
      REEFER => giữ nguyên
    - EMC
      RATE 1 - GENERAL CARGO ... => RATE 1
    - HPL
      FAK INCLUDING GARMENT => FAK
      FAK => giữ nguyên
    - YML
      FAK (NON-HAZ, EXCLUDING REEFER/ SHIPS/ BOATS/ VEHICLES/ CARS) => FAK
      GROUP A : FAK (NON-HAZ, EXCLUDING REEFER/ SHIPS/ BOATS/ VEHICLES/ CARS) => GROUP A
    """
    if "CommodityType" not in df_master.columns or "Carrier" not in df_master.columns:
        return df_master

    df = df_master.copy()

    carrier_upper = df["Carrier"].astype(str).str.upper()
    comm = df["CommodityType"].astype(str)

    # --- COSCO ---
    mask_cosco = carrier_upper.str.contains("COSCO", na=False)

    # FAK (Excluding Garment) => FAK
    # (dùng regex=False vì có dấu ngoặc)
    mask_cosco_fak_ex = mask_cosco & comm.str.contains(
        "FAK (Excluding Garment)", case=False, na=False, regex=False
    )
    df.loc[mask_cosco_fak_ex, "CommodityType"] = "FAK"

    # Garments/Textile/Consol => GARMENT  (cái này anh nói đã OK rồi, giữ nguyên)
    mask_cosco_gar = mask_cosco & comm.str.contains(
        "Garments/Textile/Consol", case=False, na=False
    )
    df.loc[mask_cosco_gar, "CommodityType"] = "GARMENT"

    # --- EMC ---
    mask_emc = carrier_upper.str.contains("EMC", na=False)
    mask_emc_rate1 = mask_emc & comm.str.contains(
        "RATE 1 - GENERAL CARGO", case=False, na=False
    )
    df.loc[mask_emc_rate1, "CommodityType"] = "RATE 1"

    # --- HPL ---
    mask_hpl = carrier_upper.str.contains("HPL", na=False)

    # FAK INCLUDING GARMENT => FAK
    mask_hpl_fak_inc = mask_hpl & comm.str.contains(
        "FAK INCLUDING GARMENT", case=False, na=False
    )
    df.loc[mask_hpl_fak_inc, "CommodityType"] = "FAK"

    # --- YML ---
    mask_yml = carrier_upper.str.contains("YML", na=False)
    # pattern có ngoặc + dấu / nên cũng cần regex=False
    pattern_yml_fak = "FAK (NON-HAZ, EXCLUDING REEFER/ SHIPS/ BOATS/ VEHICLES/ CARS)"

    # GROUP A : FAK (...) => GROUP A
    mask_yml_groupA = (
        mask_yml
        & comm.str.contains("GROUP A", case=False, na=False)
        & comm.str.contains(pattern_yml_fak, case=False, na=False, regex=False)
    )
    df.loc[mask_yml_groupA, "CommodityType"] = "GROUP A"

    # FAK (...) => FAK (chỉ khi không nằm trong GROUP A)
    mask_yml_fak = (
        mask_yml
        & comm.str.contains(pattern_yml_fak, case=False, na=False, regex=False)
        & ~mask_yml_groupA
    )
    df.loc[mask_yml_fak, "CommodityType"] = "FAK"

    return df



# ========= XOAY DỌC -> NGANG =========
def make_horizontal_output(df_long: pd.DataFrame) -> pd.DataFrame:
    """
    Dạng dọc (ContainerType/Amount) -> dạng ngang (20GP, 40GP, 40HQ, 45HQ, 40NOR).
    Gộp theo bộ key cố định bao gồm CommodityType & RoutingNote, ...
    Quan trọng: fillna("") cho các key để KHÔNG bỏ các dòng có RoutingNote trống.
    """
    if df_long.empty:
        return df_long.copy()

    df_long = df_long.copy()

    wanted_keys = [
        "POL",
        "POD",
        "PlaceOfDelivery",
        "RoutingNote",
        "Carrier",
        "EffectiveDate",
        "ExpirationDate",
        "ContractIdentifier",
        "CommodityType",
        "RateType",
    ]
    index_cols = [c for c in wanted_keys if c in df_long.columns]

    extra_keys = [
        c
        for c in df_long.columns
        if c not in index_cols and c not in ["ContainerType", "Amount"]
    ]
    index_cols = index_cols + extra_keys

    # Fill NaN trong key để pivot không drop group
    for col in index_cols:
        df_long[col] = df_long[col].fillna("")

    wide = (
        df_long.pivot_table(
            index=index_cols,
            columns="ContainerType",
            values="Amount",
            aggfunc="first",
        )
        .reset_index()
    )

    if wide.columns.name:
        wide.columns.name = None

    cont_order = ["20GP", "40GP", "40HQ", "45HQ", "40NOR"]
    key_cols = [c for c in wide.columns if c not in cont_order]
    other = [c for c in wide.columns if c not in key_cols and c not in cont_order]

    final_cols = key_cols + [c for c in cont_order if c in wide.columns] + other
    return wide[final_cols]


# ========= HÀM SET WIDTH CHO SHEET MASTER =========
def pixels_to_width(pixels: int) -> float:
    """
    Xấp xỉ convert pixel -> Excel column width (Calibri 11).
    Công thức gần đúng: width ≈ (pixels - 5) / 7.
    """
    return max((pixels - 5) / 7.0, 0.0)


def set_master_column_widths(ws):
    """
    Set width cho các cột A.O trên sheet Master theo yêu cầu:
    A = 80 px
    B = 141 px
    C = 141 px
    D = 125 px
    E = 85 px
    F, G = 112 px
    H = 146 px
    I = 150 px
    J, K, L, M, N, O = 80 px
    """
    pixel_map = {
        "A": 80,
        "B": 141,
        "C": 141,
        "D": 125,
        "E": 85,
        "F": 112,
        "G": 112,
        "H": 146,
        "I": 150,
        "J": 80,
        "K": 80,
        "L": 80,
        "M": 80,
        "N": 80,
        "O": 80,
    }

    for col, px in pixel_map.items():
        ws.column_dimensions[col].width = pixels_to_width(px)


# ========= CHUẨN HÓA 1 FILE (KHÔNG GHI EXCEL TRUNG GIAN) =========
def normalize_file(filepath):
    fname = os.path.basename(filepath)
    print(f"\n[+] Đang xử lý RAW: {fname}")

    rate_type = detect_rate_type_from_name(fname)
    if rate_type is None:
        print("    -> Không xác định được RateType từ tên file, bỏ qua.")
        return pd.DataFrame()

    raw_df = read_excel_safe(filepath, header=None)
    if raw_df.empty:
        print("    -> File rỗng, bỏ qua.")
        return pd.DataFrame()

    if rate_type in ["FAK", "ONE_SPECIAL RATE"]:
        df_out = parse_fak_or_fix(raw_df, rate_type, fname)
    else:
        df_out = parse_scfi(raw_df, fname)

    if df_out.empty:
        print("    -> Không trích được dữ liệu hợp lệ.")
        return pd.DataFrame()

    print(f"    -> Đã chuẩn hóa (dạng dọc): {len(df_out)} dòng.")
    return df_out


# ========= GỘP MASTER + ÁP PUC (KHÔNG CẮT EXP) =========
def combine_all(list_df):
    if not list_df:
        print("Không có dữ liệu hợp lệ để gộp!")
        return

    master = pd.concat(list_df, ignore_index=True)

    print("\n[THỐNG KÊ] Số dòng theo RateType (FULL, chưa cắt Exp):")
    print(master["RateType"].value_counts())

    # KHÔNG cắt ngày Expiration, giữ FULL lịch sử
    filtered = master.copy()

    # Áp PUC (chuẩn) từ file PUC_SOC.xlsx
    filtered = apply_puc_to_df(filtered)

    # Chuẩn hóa ngày về dạng ngắn
    filtered["EffectiveDate"] = format_short_date(filtered["EffectiveDate"])
    filtered["ExpirationDate"] = format_short_date(filtered["ExpirationDate"])

    # Chuẩn hóa PlaceOfDelivery (bỏ space)
    filtered["PlaceOfDelivery"] = (
        filtered["PlaceOfDelivery"].astype(str).str.strip()
    )

    # CHUẨN HÓA COMMODITY THEO HÃNG (COSCO, EMC, HPL, YML)
    filtered = normalize_commodity(filtered)

    # Bỏ SourceFile khỏi output chính
    filtered_no_src = filtered.drop(columns=["SourceFile"], errors="ignore")

    # MASTER PRICING: XOAY DỌC -> NGANG
    master_wide = make_horizontal_output(filtered_no_src)

    with pd.ExcelWriter(master_file, engine="openpyxl") as writer:
        # Sheet Master (ngang)
        master_wide.to_excel(writer, index=False, sheet_name="Master")
        ws = writer.sheets["Master"]

        # Tô màu header
        header_fill = PatternFill(
            start_color="CCFFCC",
            end_color="CCFFCC",
            fill_type="solid",
        )
        for cell in ws[1]:
            cell.fill = header_fill

        # Set width các cột A.O theo yêu cầu
        set_master_column_widths(ws)

        # Sheet Master_Long (dọc, full data – FULL lịch sử Exp + PUC + commodity chuẩn)
        filtered_no_src.to_excel(writer, index=False, sheet_name="Master_Long")

    print(f"\n[HOÀN TẤT] MASTER FILE: {master_file}")
    print(
        f"    -> Tổng số dòng Master_Long (FULL Exp + PUC + chuẩn commodity): {len(filtered_no_src)}"
    )


# ========= MAIN =========
def main():
    if not os.path.isdir(raw_dir):
        print(f"Thư mục Raw không tồn tại: {raw_dir}")
        return

    files = [f for f in os.listdir(raw_dir) if f.lower().endswith(".xlsx")]
    if not files:
        print("Không tìm thấy file trong thư mục Raw.")
        return

    all_normalized = []

    for f in files:
        df_norm = normalize_file(os.path.join(raw_dir, f))
        if not df_norm.empty:
            all_normalized.append(df_norm)

    combine_all(all_normalized)


if __name__ == "__main__":
    main()
