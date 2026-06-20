# 程式碼片段 2：藥物特徵提取 (drug_database.py)
# 用途：論文 3.3 節 — RAG 檢索增強生成中的特徵提取

def get_drug_features_for_rag(self, sample_size=500):
    """取得藥物特徵列表用於 RAG 比對"""
    cursor.execute("""
        SELECT id, license_number, chinese_name, english_name,
               shape, color, special_dosage_form,
               label_front, label_back
        FROM drugs
        WHERE chinese_name IS NOT NULL AND length(chinese_name) > 0
        LIMIT ?
    """, (sample_size,))
    
    # 組織成精簡格式（減少 token 數量）
    # 格式: ID|標記正面/背面|中文名|形狀|顏色
    drug_list = []
    for drug in drugs:
        drug_id, license, cn_name, en_name, \
            shape, color, form, label_front, label_back = drug
        
        marks = ""
        if label_front and label_back:
            marks = f"{label_front}/{label_back}"
        elif label_front:
            marks = label_front
            
        parts = [str(drug_id), marks, cn_name or ""]
        if shape: parts.append(shape)
        if color: parts.append(color)
        drug_list.append("|".join(parts))
    
    return "\n".join(drug_list)
