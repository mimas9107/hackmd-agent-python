---
name:          "CHANGELOG.md"
description:   "本專案的所有重要變更都會記錄在此檔案。"
created_date:  "2026/05/29 13:25:00"
modified_date: "2026/06/18 10:50:00"
project_version: "1.3.0"
document_version: "1.0.0"
agent_sign: ['human/mimas', 'gemini cli/gemini-cli']
---

# 更新日誌

本專案的所有重要變更都會記錄在此檔案。

格式基於 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.1.0/)，
並遵循 [語意化版本](https://semver.org/lang/zh-TW/spec/v2.0.0.html)。

## [未發布]

---

## [1.3.0] - 2026-03-22

### 新增
- **搜尋功能增強**：
  - `searchContent` 參數：支援搜尋筆記內容（而不僅是標題）
  - `fuzzy` 參數：支援模糊匹配，容許打字錯誤
  - `limit` 參數：限制回傳結果數量（預設 20，最大 100）
- **相關性排序**：搜尋結果依照相關程度排序
  - 100 分：完全匹配
  - 90 分：標題開頭匹配
  - 70 分：關鍵字包含在標題中
  - 60 分：任意單字匹配
- **快取機制**：
  - 筆記列表 60 秒記憶體快取
  - 建立、更新、刪除筆記後自動清除快取
  - 減少重複 API 呼叫，提升效能
- **重試與指數退避**：
  - 自動重試機制（預設最多 3 次）
  - 遇到 429 (速率限制) 或 5xx 錯誤時自動重試
  - 指數退避：1s → 2s → 4s，最大等待 32 秒
  - 支援 `Retry-After` header
- **AI Agent 透明度**：
  - 回應包含 `_meta` 欄位
  - 提供重試資訊 (`was_rate_limited`, `total_attempts`, `total_wait_seconds`)
  - 提供進度訊息陣列 (`progress_messages`)

### 技術細節
- 新增 `HackMDClient.search_notes()` API 方法
- 新增 `RetryInfo` 資料類別追蹤重試狀態
- 新增 `_request_with_retry()` 方法處理所有 API 請求
- MCP Server 和 tools.py 支援 progress callback
- 所有工具回應格式改為 `{"data": ..., "_meta": {...}}`

---

## [1.2.0] - 2024-02-01

### 變更
- **破壞性變更**：從 `google-generativeai` 遷移到新版 `google-genai` SDK (v1.0.0+)
- 更新 `process_message()` 接受 `genai.Client` 作為第一個參數
- 更新 `run_agent()` 接受 `genai.Client` 作為第一個參數
- 更新 `to_gemini_tools()` 使用與新 SDK 相容的 `parameters_json_schema` 格式

### 技術細節
- 使用 `google-genai>=1.0.0`
- 使用 `types.FunctionDeclaration` 定義工具
- 使用 `client.aio.chats.create` 進行非同步聊天

---

## [1.1.0] - 2024-02-01

### 變更
- **破壞性變更**：從 Anthropic Claude SDK 遷移到 Google Gemini API
  - 環境變數變更：`ANTHROPIC_API_KEY` → `GEMINI_API_KEY`
  - 預設模型變更：`claude-3-5-haiku-latest` → `gemini-2.0-flash`
- 更新 `run_agent()` 和 `process_message()` 函式簽名
  - 移除 `client` 參數（Gemini 使用 `genai.configure()`）
- 新增 `to_gemini_tools()` 函式
- 保留 `to_anthropic_tools()` 確保向後相容

### 新增
- Google Gemini 函式呼叫支援
- 免費方案支援（基本使用無需付費！）

### 技術細節
- 使用 `google-generativeai>=0.8.0` SDK
- 使用 `asyncio.to_thread()` 處理非同步 Gemini API 呼叫
- 支援 Gemini 原生函式回應格式

---

## [1.0.0] - 2024-02-01

### 新增
- 初始版本（從 Deno 版本移植）
- **核心工具：**
  - `hackmd_list_notes` - 列出所有筆記
  - `hackmd_read_note` - 依 ID 讀取筆記內容
  - `hackmd_create_note` - 建立新筆記
  - `hackmd_update_note` - 更新現有筆記
  - `hackmd_delete_note` - 刪除筆記
  - `hackmd_search_notes` - 依標題關鍵字搜尋
- **代理功能：**
  - 互動式 CLI 模式
  - 可程式化 `process_message()` 非同步 API
  - 可設定模型、對話長度上限和系統提示詞
  - 工具執行與錯誤處理

---

## 版本號說明

本專案使用語意化版本控制：

- **主版本號**：不相容的 API 變更
- **次版本號**：新增功能（向後相容）
- **修補版本號**：錯誤修復（向後相容）

---

## 相關連結

- [中文說明書](./README.md)
- [AGENTS.md](./AGENTS.md) - AI 代理整合指南
- [HackMD API 文檔](https://hackmd.io/@hackmd-api/developer-portal)
