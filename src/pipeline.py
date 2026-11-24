import base64
import io
import re
import unicodedata
from pathlib import Path

import joblib
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SAMPLE_PATH = DATA_DIR / "du_doan_cam_xuc_toan_bo_bai_dang.csv"
MODEL_PATH = DATA_DIR / "mo_hinh_phan_loai_cam_xuc.joblib"

SAMPLE_RAW_COLUMNS = ["post_id", "timestamp", "text", "category", "sentiment", "language", "has_link", "likes", "comments", "shares", "is_spam"]
LABEL_ORDER = ["Negative", "Neutral", "Positive"]
LABEL_ALIASES = {"pos": "positive", "neg": "negative", "neu": "neutral", "tich cuc": "positive", "tieu cuc": "negative", "trung lap": "neutral", "trung tinh": "neutral", "1": "positive", "0": "neutral", "-1": "negative"}
SENTIMENT_TOKENS = {"positive", "neutral", "negative", "pos", "neu", "neg", "tich cuc", "tieu cuc", "trung lap", "trung tinh"}
TEXT_PATTERN = r"^(text|content|message|caption|post|post.?(text|content|message)|noi.?dung|bai.?dang|van.?ban|clean.?text)$"
URL_PATTERN = re.compile(r"https?://\S+|www\.\S+")
MENTION_PATTERN = re.compile(r"@\w+")
ROLE_PATTERNS = {
    "category": r"categor|topic|danh.?muc|chu.?de|chuyen.?muc|phan.?loai|post.?type|page|group",
    "language": r"lang|ngon.?ngu",
    "time": r"time|date|created|ngay|thoi.?gian|thoi.?diem",
    "likes": r"like|thich",
    "comments": r"comment|binh.?luan",
    "shares": r"share|chia.?se",
}
OUTPUT_COLUMNS = ["Ma_bai", "Noi_dung", "Noi_dung_sach", "Danh_muc", "Ngon_ngu", "Thoi_gian", "Likes", "Comments", "Shares", "Cam_xuc_that", "Cam_xuc_du_doan", "Do_tin_cay"]

_model = None


def get_model():
    global _model
    if _model is None:
        _model = joblib.load(MODEL_PATH)
    return _model


def fold(value):
    text = unicodedata.normalize("NFD", str(value).lower().replace("đ", "d"))
    return "".join(ch for ch in text if unicodedata.category(ch) != "Mn").strip()


def normalize_text(value):
    text = str(value).lower()
    text = URL_PATTERN.sub(" ", text)
    text = MENTION_PATTERN.sub(" ", text)
    text = re.sub(r"[^\w\s]|_|\d+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_label(value):
    key = fold(value)
    label = LABEL_ALIASES.get(key, key).capitalize()
    return label if label in LABEL_ORDER else None


def find_column(df, pattern, exclude=()):
    for col in df.columns:
        if col not in exclude and re.search(pattern, fold(col)):
            return col
    return None


def detect_columns(df):
    label, best = None, 1
    for col in df.columns:
        if df[col].nunique(dropna=True) <= 10:
            values = {fold(v) for v in df[col].dropna().astype(str).unique()}
            score = len(values & SENTIMENT_TOKENS)
            if score > best:
                label, best = col, score
    text = find_column(df, TEXT_PATTERN, {label})
    if text is None or pd.api.types.is_numeric_dtype(df[text]):
        candidates = [c for c in df.columns if c != label and not pd.api.types.is_numeric_dtype(df[c])]
        text = max(candidates, key=lambda c: df[c].dropna().astype(str).str.len().mean()) if candidates else None
    taken = {label, text}
    mapping = {"text": text, "label": label}
    for role, pattern in ROLE_PATTERNS.items():
        col = find_column(df, pattern, taken)
        mapping[role] = col
        if col:
            taken.add(col)
    return mapping


def load_sample_raw():
    frame = pd.read_csv(SAMPLE_PATH)
    return frame[[c for c in SAMPLE_RAW_COLUMNS if c in frame.columns]]


def parse_upload(contents):
    _, content_string = contents.split(",", 1)
    decoded = base64.b64decode(content_string)
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            text = decoded.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    frame = pd.read_csv(io.StringIO(text))
    if frame.shape[1] == 1:
        frame = pd.read_csv(io.StringIO(text), sep=None, engine="python")
    frame.columns = [str(c).strip() for c in frame.columns]
    return frame


def pack_raw(df, source, name):
    mapping = detect_columns(df)
    head = df.head(6).astype(str).apply(lambda col: col.str.slice(0, 70))
    packed = {
        "source": source,
        "name": name,
        "rows": int(len(df)),
        "cols": int(df.shape[1]),
        "mapping": mapping,
        "preview": {"columns": list(head.columns), "rows": head.values.tolist()},
        "error": None if mapping["text"] else "no_text",
    }
    if not packed["error"]:
        packed["json"] = df.to_json(orient="split", force_ascii=False)
    return packed


def unpack_raw(packed):
    return pd.read_json(io.StringIO(packed["json"]), orient="split", dtype=False, convert_dates=False)


def pack_clean(df):
    return df.to_json(orient="split", date_format="iso", force_ascii=False)


def unpack_clean(payload):
    frame = pd.read_json(io.StringIO(payload), orient="split", dtype=False, convert_dates=False)
    frame["Thoi_gian"] = pd.to_datetime(frame["Thoi_gian"], errors="coerce")
    return frame


def refine(raw, mapping):
    text_col = mapping["text"]
    df = raw.copy()
    rows_in = len(df)
    duplicates = int(df.duplicated().sum())
    df = df.drop_duplicates()
    missing_text = int(df[text_col].isna().sum())
    df = df.dropna(subset=[text_col]).copy()
    df["Noi_dung"] = df[text_col].astype(str)
    df["Noi_dung_sach"] = df["Noi_dung"].map(normalize_text)
    empty = int((df["Noi_dung_sach"] == "").sum())
    df = df[df["Noi_dung_sach"] != ""].reset_index(drop=True)

    id_col = find_column(df, r"^(post.?id|id|ma.?bai)$")
    df["Ma_bai"] = df[id_col] if id_col else range(1, len(df) + 1)

    invalid_labels = 0
    if mapping["label"]:
        parsed = df[mapping["label"]].map(normalize_label)
        invalid_labels = int((parsed.isna() & df[mapping["label"]].notna()).sum())
        df["Cam_xuc_that"] = parsed
    else:
        df["Cam_xuc_that"] = None

    for role, name in (("likes", "Likes"), ("comments", "Comments"), ("shares", "Shares")):
        df[name] = pd.to_numeric(df[mapping[role]], errors="coerce").fillna(0) if mapping[role] else 0
    df["Danh_muc"] = df[mapping["category"]].fillna("Unknown").astype(str).str.strip() if mapping["category"] else "Unknown"
    df["Ngon_ngu"] = df[mapping["language"]].fillna("Unknown").astype(str).str.strip() if mapping["language"] else "Unknown"
    df["Thoi_gian"] = pd.to_datetime(df[mapping["time"]], errors="coerce") if mapping["time"] else pd.NaT

    model = get_model()
    df["Cam_xuc_du_doan"] = model.predict(df["Noi_dung_sach"])
    df["Do_tin_cay"] = model.predict_proba(df["Noi_dung_sach"]).max(axis=1).round(4)

    clean = df[OUTPUT_COLUMNS].copy()
    has_label = bool(mapping["label"])
    labelled = clean["Cam_xuc_that"].notna()
    agreement = float((clean.loc[labelled, "Cam_xuc_that"] == clean.loc[labelled, "Cam_xuc_du_doan"]).mean()) if has_label and labelled.any() else None
    samples = clean.sample(min(5, len(clean)), random_state=7)
    period = None
    if clean["Thoi_gian"].notna().any():
        period = [f"{clean['Thoi_gian'].min():%Y-%m-%d}", f"{clean['Thoi_gian'].max():%Y-%m-%d}"]
    report = {
        "rows_in": rows_in,
        "rows_out": int(len(clean)),
        "duplicates": duplicates,
        "missing_text": missing_text,
        "empty": empty,
        "invalid_labels": invalid_labels,
        "has_label": has_label,
        "has_engagement": all(mapping[k] for k in ("likes", "comments", "shares")),
        "n_categories": int(clean["Danh_muc"].nunique()),
        "n_languages": int(clean["Ngon_ngu"].nunique()),
        "period": period,
        "agreement": agreement,
        "mapping": mapping,
        "samples": [{"before": a[:120], "after": b[:120]} for a, b in zip(samples["Noi_dung"], samples["Noi_dung_sach"])],
    }
    return clean, report