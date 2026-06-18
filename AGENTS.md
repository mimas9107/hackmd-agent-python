---
name:          "AGENTS.md"
description:   "HackMD AI Agent 整合指南 — MCP 工具集與操作準則"
created_date:  "2026/05/29 13:25:00"
modified_date: "2026/06/18 10:40:00"
project_version: "1.0.0"
document_version: "1.1.0"
agent_sign: ['human/mimas', 'gemini cli/gemini-cli']
---

# HackMD AI Agent 整合指南 (AGENTS.md)

本文件定義 HackMD Agent 的工具操作準則。Agent 必須同時遵循工作區全域規範 (`../AGENTS.md`)。

## 1. 專案定位 (Project Context)
- 本專案是一個 **MCP (Model Context Protocol) Server**，旨在為 AI 提供操作 HackMD 筆記的能力。
- 開發環境必須遵循全域規範中的 `uv` 與 `python3.10+` 約束。

## 2. 工具操作準則 (Tool Usage)
本專案提供 6 個核心工具，所有工具均為非同步 (async) 並回傳 JSON 字串。

### 查詢與讀取 (Discovery & Read)
- `hackmd_list_notes`: 獲取筆記列表。
- `hackmd_read_note`: 讀取特定筆記內容。修改前**必須**先執行讀取以確保上下文完整。

### 寫入與修改 (Write & Update)
- `hackmd_create_note`: 建立新筆記。
- `hackmd_update_note`: 更新既有筆記。建議在更新前先讀取，以避免意外覆蓋重要資訊。

### 安全操作
- `hackmd_delete_note`: 永久刪除。執行前**必須**取得使用者明確授權（遵循全域規範 Section 1）。

## 3. 最佳實踐 (Best Practices)
- **結構化輸出**：建立筆記時應使用標準 Markdown 標題結構。
- **錯誤處理**：若 API 回傳 401，請檢查 `.env` 中的 `HACKMD_API_TOKEN`。
- **報告同步**：重大修改後，應將執行結果同步回專案的 `CHANGELOG.md`。

---
*註：本文件專注於 HackMD 工具操作細節，通用環境指令請查閱全域規範。*
