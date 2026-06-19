"""
==============================================
FDA OpenData 藥品查詢 (fda_opendata_crawler.py)
==============================================

從 TFDA 食品藥物開放資料平臺下載「全部藥品許可證資料集」，
並在本地端搜尋藥物資訊。

資料集 API:
  https://data.fda.gov.tw/data/opendata/export/36/json
  (【9122】全部藥品許可證資料集)

【資料來源標註】
衛生福利部食品藥物管理署 食品藥物開放資料平臺

【作者】MUS2 團隊
【日期】2026
"""

import json
import logging
import os
import re
import time
import zipfile
import io
import requests

logger = logging.getLogger(__name__)

# 資料集 URL
DATASET_URL = "https://data.fda.gov.tw/data/opendata/export/36/json"
APPEARANCE_URL = "https://data.fda.gov.tw/data/opendata/export/42/json"

# 快取設定
_cache = {
    "data": None,
    "last_updated": 0,
}
_appearance_cache = {
    "data": None,
    "last_updated": 0,
}
CACHE_TTL = 3600  # 快取 1 小時


def _download_dataset() -> list:
    """下載並解壓 TFDA 全部藥品許可證資料集"""
    logger.info("正在下載 TFDA 藥品許可證資料集...")
    r = requests.get(DATASET_URL, timeout=120)
    r.raise_for_status()

    ct = r.headers.get("content-type", "")
    if "zip" in ct or r.content[:4] == b"PK\x03\x04":
        z = zipfile.ZipFile(io.BytesIO(r.content))
        for name in z.namelist():
            if name.endswith(".json"):
                with z.open(name) as f:
                    data = json.loads(f.read().decode("utf-8"))
                    logger.info(f"✓ TFDA 資料集下載完成: {len(data)} 筆藥品")
                    return data
        raise ValueError("ZIP 中未找到 JSON 檔案")
    else:
        data = r.json()
        logger.info(f"✓ TFDA 資料集下載完成: {len(data)} 筆藥品")
        return data


def _get_dataset() -> list:
    """取得資料集（帶快取）"""
    now = time.time()
    if _cache["data"] is not None and (now - _cache["last_updated"]) < CACHE_TTL:
        return _cache["data"]

    data = _download_dataset()
    _cache["data"] = data
    _cache["last_updated"] = now
    return data


def _download_appearance() -> dict:
    """下載藥品外觀資料集，回傳以許可證字號為 key 的 dict"""
    logger.info("正在下載 TFDA 藥品外觀資料集...")
    r = requests.get(APPEARANCE_URL, timeout=120)
    r.raise_for_status()

    ct = r.headers.get("content-type", "")
    if "zip" in ct or r.content[:4] == b"PK\x03\x04":
        z = zipfile.ZipFile(io.BytesIO(r.content))
        for name in z.namelist():
            if name.endswith(".json"):
                with z.open(name) as f:
                    data = json.loads(f.read().decode("utf-8"))
                    result = {}
                    for rec in data:
                        lic = rec.get("許可證字號", "")
                        if lic:
                            result[lic] = rec
                    logger.info(f"✓ TFDA 外觀資料集下載完成: {len(result)} 筆")
                    return result
        raise ValueError("ZIP 中未找到 JSON 檔案")
    else:
        data = r.json()
        result = {}
        for rec in data:
            lic = rec.get("許可證字號", "")
            if lic:
                result[lic] = rec
        logger.info(f"✓ TFDA 外觀資料集下載完成: {len(result)} 筆")
        return result


def _get_appearance() -> dict:
    """取得外觀資料集（帶快取）"""
    now = time.time()
    if _appearance_cache["data"] is not None and (now - _appearance_cache["last_updated"]) < CACHE_TTL:
        return _appearance_cache["data"]

    data = _download_appearance()
    _appearance_cache["data"] = data
    _appearance_cache["last_updated"] = now
    return data


def get_drug_image_url(license_number: str) -> str:
    """取得藥品外觀圖檔 URL"""
    try:
        appearance = _get_appearance()
        rec = appearance.get(license_number)
        if rec:
            return rec.get("外觀圖檔連結", "")
    except Exception as e:
        logger.warning(f"取得外觀圖檔失敗: {e}")
    return ""


def search_fda_drug(drug_name: str) -> dict:
    """
    從 TFDA 開放資料搜尋藥物。

    搜尋邏輯：
    1. 許可證字號精確比對
    2. 中文品名包含搜尋詞
    3. 英文品名包含搜尋詞（不分大小寫）

    Args:
        drug_name: 藥物名稱或許可證字號

    Returns:
        dict: {"status": "success", "details": {...}, "source": "fda_opendata"}
              或 {"status": "success", "results": [], "source": "fda_opendata"}
    """
    try:
        dataset = _get_dataset()
    except Exception as e:
        logger.error(f"✗ TFDA 資料集下載失敗: {e}")
        return {"status": "error", "error": str(e), "source": "fda_opendata"}

    keyword = drug_name.strip()
    keyword_upper = keyword.upper()

    # 正規化函數：去除引號、多餘標點和空格，用於模糊比對
    def normalize(s):
        """去除引號、句號(非小數點)、多餘空格，統一大寫"""
        s = s.upper()
        s = re.sub(r'["\'\u201c\u201d\u2018\u2019]', '', s)  # 去除各種引號
        s = re.sub(r'\s+', ' ', s).strip()
        return s

    def normalize_compact(s):
        """去除引號和所有空格，用於最寬鬆比對"""
        s = normalize(s)
        s = re.sub(r'\s+', '', s)
        return s

    keyword_normalized = normalize(keyword_upper)
    keyword_compact = normalize_compact(keyword_upper)

    # 常見藥品縮寫展開（用於模糊比對）
    ABBREV_MAP = {
        "CAP": "CAPSULES", "CAPS": "CAPSULES",
        "TAB": "TABLETS", "TABS": "TABLETS",
        "F.C.T": "F.C. TABLETS", "F.C. T": "F.C. TABLETS",
        "FCT": "F.C. TABLETS",
        "INJ": "INJECTION",
        "SOL": "SOLUTION",
        "SYR": "SYRUP",
        "SUSP": "SUSPENSION",
        "CR": "CREAM",
        "OINT": "OINTMENT",
        "SUPP": "SUPPOSITORIES",
        "AMP": "AMPOULES",
    }

    # 產生展開後的搜尋詞（用於英文名比對）
    expanded_keywords = [keyword_upper]
    words = keyword_upper.split()
    for abbr, full in ABBREV_MAP.items():
        if abbr in words:
            expanded = keyword_upper.replace(abbr, full, 1)
            expanded_keywords.append(expanded)
        if full in words:
            expanded = keyword_upper.replace(full, abbr, 1)
            expanded_keywords.append(expanded)

    # 也加入正規化版本
    expanded_normalized = [normalize(kw) for kw in expanded_keywords]

    # 分詞比對：將搜尋詞拆成個別單字（展開縮寫後），所有字都出現即匹配
    def _all_words_match(en_text_upper, search_words):
        """檢查所有搜尋單字是否都出現在英文品名中"""
        return all(w in en_text_upper for w in search_words if len(w) >= 2)

    # 產生展開後的分詞列表
    expanded_word_sets = []
    for kw in expanded_keywords:
        word_set = [w for w in kw.split() if len(w) >= 2]
        if word_set and word_set not in expanded_word_sets:
            expanded_word_sets.append(word_set)

    # 搜尋比對
    matches = []
    for record in dataset:
        license_num = record.get("許可證字號", "") or ""
        cn_name = record.get("中文品名", "") or ""
        en_name = record.get("英文品名", "") or ""
        is_cancelled = bool(record.get("註銷狀態"))

        # 許可證字號精確比對（不排除已註銷）
        if keyword == license_num:
            matches.insert(0, record)
            continue

        # 名稱搜尋：跳過已註銷藥品
        if is_cancelled:
            continue

        # 中文品名包含
        if keyword in cn_name:
            matches.append(record)
            continue

        # 英文品名包含（不分大小寫，含縮寫展開 + 正規化比對）
        en_upper = en_name.upper()
        en_normalized = normalize(en_upper)
        en_compact = normalize_compact(en_upper)
        if keyword_upper and (
            any(kw in en_upper for kw in expanded_keywords)
            or any(kw in en_normalized for kw in expanded_normalized)
            or keyword_compact in en_compact
            or any(_all_words_match(en_upper, ws) for ws in expanded_word_sets)
        ):
            matches.append(record)

    if not matches:
        return {"status": "success", "results": [], "source": "fda_opendata"}

    # 排序：優先完整子字串匹配 > 英文名較短（越接近搜尋詞越好）
    def _match_score(record):
        en = (record.get("英文品名", "") or "").upper()
        # 完整子字串匹配得高分
        exact_sub = any(kw in en for kw in expanded_keywords)
        return (
            0 if exact_sub else 1,  # 完整匹配優先
            len(en),                 # 英文名越短越好
        )

    matches.sort(key=_match_score)

    # 取最佳結果
    best = matches[0]

    details = {
        "source": "衛生福利部食品藥物管理署 開放資料",
        "source_url": "https://data.fda.gov.tw",
        "中文品名": best.get("中文品名", ""),
        "英文品名": best.get("英文品名", ""),
        "id": best.get("許可證字號", ""),
        "許可證字號": best.get("許可證字號", ""),
        "適應症": best.get("適應症", ""),
        "劑型": best.get("劑型", ""),
        "包裝": best.get("包裝", ""),
        "藥品類別": best.get("藥品類別", ""),
        "主成分略述": best.get("主成分略述", ""),
        "藥商名稱": best.get("申請商名稱", ""),
        "製造廠名稱": best.get("製造商名稱", ""),
        "有效日期": best.get("有效日期", ""),
        "管制藥品分類級別": best.get("管制藥品分類級別", ""),
        "用法用量": best.get("用法用量", ""),
        "search_results_count": len(matches),
    }

    # 移除空值
    details = {k: v for k, v in details.items() if v}

    # 嘗試取得外觀圖片 URL
    license_num = best.get("許可證字號", "")
    if license_num:
        img_url = get_drug_image_url(license_num)
        if img_url:
            details["image_url"] = img_url

    logger.info(
        f"✓ TFDA 開放資料搜尋成功: {drug_name} → {details.get('中文品名', '?')} "
        f"(共 {len(matches)} 筆結果)"
    )

    return {"status": "success", "details": details, "source": "fda_opendata"}
