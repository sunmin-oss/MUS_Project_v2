---
name: md-to-word
description: '將指定的 Markdown (.md) 檔案轉換為 Word (.docx) 格式。Use when: 使用者要求將 md 轉 word、markdown 轉 docx、匯出文件為 word、產生 word 檔案。'
argument-hint: '要轉換的 .md 檔案路徑'
---

# Markdown 轉 Word

將指定的 `.md` 檔案轉換為 `.docx` (Microsoft Word) 格式。

## 使用時機
- 使用者要求將 markdown 檔案轉為 Word
- 需要匯出 .md 為 .docx
- 產出可供列印或分享的 Word 文件

## 前置需求
- 系統需安裝 `pandoc`（若未安裝，使用 `brew install pandoc` 安裝）

## 執行步驟

1. **確認輸入檔案**：確認使用者指定的 `.md` 檔案存在
2. **確認 pandoc 已安裝**：執行 `which pandoc`，若未安裝則提示安裝
3. **執行轉換**：使用以下指令轉換檔案

```bash
pandoc "<輸入檔案.md>" -o "<輸出檔案.docx>" --from markdown --to docx
```

### 轉換選項

若使用者有特殊需求，可加入額外參數：

| 需求 | 參數 |
|------|------|
| 套用自訂樣式範本 | `--reference-doc=<template.docx>` |
| 包含目錄 (TOC) | `--toc` |
| 設定 TOC 層級深度 | `--toc-depth=3` |
| 支援表格延伸語法 | `--from markdown+pipe_tables+grid_tables` |
| 保留原始 HTML | `--from markdown+raw_html` |

### 預設行為

- 輸出檔案名稱：與輸入檔相同，副檔名改為 `.docx`
- 輸出位置：與輸入檔同目錄（除非使用者另外指定）
- 編碼：UTF-8

## 範例

將 `docs/專案報告_論文版.md` 轉為 Word：

```bash
pandoc "docs/專案報告_論文版.md" -o "docs/專案報告_論文版.docx" --from markdown --to docx --toc
```

## 錯誤處理

- 若 pandoc 未安裝：執行 `brew install pandoc` (macOS)
- 若檔案不存在：提示使用者確認路徑
- 若轉換失敗：檢查 markdown 語法是否有問題，並顯示 pandoc 錯誤訊息
