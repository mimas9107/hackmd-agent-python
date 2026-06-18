---
name:          "SPEC.md"
description:   "HackMD Agent 技術規格與設計文件。"
created_date:  "2026/06/18 10:55:00"
modified_date: "2026/06/18 10:55:00"
project_version: "1.3.0"
document_version: "1.0.0"
agent_sign: ['human/mimas', 'gemini cli/gemini-cli']
---

# 技術規格 (SPEC.md)

## 1. 系統架構
本專案為一個 Python 實作的 HackMD Agent，支援 MCP (Model Context Protocol)。

## 2. 核心組件
- `HackMDClient`: 封裝 HTTP 請求至 HackMD API。
- `Tools`: 定義 Agent 可用的工具函式。
- `MCP Server`: 提供 MCP 介面供相容用戶端連線。

## 3. 工具清單
- `hackmd_list_notes`
- `hackmd_read_note`
- `hackmd_create_note`
- `hackmd_update_note`
- `hackmd_delete_note`
- `hackmd_search_notes`
