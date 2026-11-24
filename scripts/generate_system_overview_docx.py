from docx import Document
from docx.shared import Cm, Pt
from docx.oxml.ns import qn

def set_run_font(run, name='標楷體', size=14):
    run.font.name = name
    r = run._element
    r.rPr.rFonts.set(qn('w:eastAsia'), name)
    run.font.size = Pt(size)

def create_document(path):
    doc = Document()
    section = doc.sections[0]
    # A4 default; set margins
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2)
    section.left_margin = Cm(2)
    section.right_margin = Cm(2)
    # 裝訂邊
    try:
        section.gutter = Cm(1)
    except Exception:
        pass

    # Title
    title = doc.add_paragraph()
    r = title.add_run('基於 RAG 技術之智慧藥物辨識與用藥管理系統')
    r.bold = True
    set_run_font(r, size=14)
    doc.add_paragraph()

    # Sections required by the competition
    sections = {
        '一、前言': (
            '本系統旨在透過 Retrieval-Augmented Generation (RAG) 結合影像辨識與知識庫檢索，'
            '提供民眾與醫療人員快速、正確之藥物辨識與用藥管理建議。團隊鼓勵使用開源平台，'
            '本專案於 GitHub 託管原始碼，並採用 Hugging Face 開放模型與開源向量庫實作檢索功能。'
        ),
        '二、創意描述': (
            '系統結合手機拍照上傳之藥品影像辨識；辨識結果會以向量檢索於本地/雲端知識庫中找出藥品標示、使用說明、禁忌與相互作用，再由生成式模型整合成可讀的用藥建議。'
            '此 RAG 流程可減少模型產生不實資訊的風險，並提供來源引用，提升臨床/使用上之信賴度。'
        ),
        '三、系統功能簡介': (
            '- 圖像辨識：透過深度學習模型(如 ResNet/輕量化 MobileNet)識別藥品外觀。\n- RAG 檢索：以句向量及 FAISS/Annoy 等向量索引執行相似度檢索。\n- 生成回覆：使用小型或雲端 LLM（支援本地/雲端切換）將檢索到之證據整合成說明。\n- 用藥管理：用戶可建立用藥清單、提醒服藥、記錄副作用。\n- 審核與溯源：每次建議附上檢索來源與相似度分數，便於專業人員審核。'
        ),
        '四、系統特色': (
            '- 可解釋性：使用 RAG 使生成內容可回溯至來源文本。\n- 邊緣/雲端混合：影像前處理與初步分類可在裝置端執行，敏感資料可留存本地，降低隱私風險。\n- 開源導向：程式碼與模型權重（若許可）註明來源並放置於 GitHub，鼓勵社群回饋與延伸。\n- 支援無障礙：介面及說明支援大字、語音輸出，縮短數位落差。'
        ),
        '五、系統開發工具與技術': (
            '開發工具與平台：GitHub（原始碼管理）、Hugging Face（模型與資料集）、Python、Flask/Django 作為後端框架；'
            '向量檢索：FAISS / Annoy；影像模型：PyTorch 或 TensorFlow；RAG 整合：LangChain-like 流程與自製檢索模組；'
            '部署：Docker 與可選之邊緣部署方案（如在 Android/iOS 上以 ONNX Runtime 或 TensorFlow Lite 運行模型）。\n\n- 使用之 AI 工具與範疇：\n  - 影像辨識：使用訓練/微調之卷積神經網路於藥袋/藥錠影像分類。\n  - 向量檢索：以 Sentence-BERT 類別模型產生 embedding，並以 FAISS 做相似度檢索。\n  - 生成模型：採用開源 LLM（如 Llama-family 或 Hugging Face 上可用模型）或商用 API 針對證據整合與回覆生成。\n  - 系統整合：LangChain-like RAG 管線負責檢索、提示模板與回覆合成。'
        ),
        '六、系統使用對象': (
            '一般民眾、家庭照護者、藥師與初級照護醫師；亦可作為社福機構、長照中心之輔助工具，降低對專業人力的依賴，縮短偏鄉等地區之醫療資訊落差。'
        ),
        '七、系統使用環境': (
            '支援智慧型手機（iOS / Android）以及 Web 平台。伺服器可部署於雲端或院內私有伺服器；可依需求將影像預處理與部分推論置於裝置端以降低延遲與隱私風險。'
        ),
        '八、結語': (
            '本系統以 RAG 為核心架構，強調「可追溯的生成式回覆」與「邊緣/雲端混合部署」，並以開源工具鏈（GitHub、Hugging Face）為基礎實作，期望能在智慧醫療與社會服務場域中，提升藥品辨識的可及性與用藥安全，並縮短數位落差。'
        ),
    }

    for heading, text in sections.items():
        p = doc.add_paragraph(heading)
        run = p.runs[0]
        run.bold = True
        set_run_font(run)
        para = doc.add_paragraph()
        # preserve newlines in text
        for line in text.split('\n'):
            run2 = para.add_run(line)
            set_run_font(run2)
            para.add_run('\n')
        para_format = para.paragraph_format
        para_format.line_spacing = 1
        para_format.space_before = Pt(3)
        para_format.space_after = Pt(3)

    doc.save(path)

if __name__ == '__main__':
    out_path = '論文/附件1-1_系統概述.docx'
    create_document(out_path)
    print(f'Generated: {out_path}')
