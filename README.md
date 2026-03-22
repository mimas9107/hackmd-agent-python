# HackMD Agent for Python

[![版本](https://img.shields.io/badge/version-1.3.0-blue.svg)](./CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue.svg)](https://www.python.org/)
[![授權](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)

專為 AI 代理設計的 HackMD 工具庫，相容於 Google Gemini 函式呼叫格式，並支援 MCP (Model Context Protocol)。

> 由 [tiny-hackmd-agent](https://github.com/user/tiny-hackmd-agent)（Deno 版本）移植而來

## 目錄

- [功能特色](#功能特色)
- [需求環境](#需求環境)
- [安裝方式](#安裝方式)
- [快速開始](#快速開始)
- [使用方式](#使用方式)
  - [CLI 模式](#cli-模式)
  - [MCP 伺服器模式](#mcp-伺服器模式)
  - [程式化使用](#程式化使用)
  - [與其他 AI 提供者整合](#與其他-ai-提供者整合)
- [API 參考](#api-參考)
- [可用工具](#可用工具)
- [搜尋功能說明](#搜尋功能說明)
- [開發指南](#開發指南)
- [授權](#授權)

## 功能特色

- **6 個 HackMD 工具**：
  - `hackmd_list_notes` - 列出所有筆記
  - `hackmd_read_note` - 讀取筆記內容
  - `hackmd_create_note` - 建立新筆記
  - `hackmd_update_note` - 更新現有筆記
  - `hackmd_delete_note` - 刪除筆記
  - `hackmd_search_notes` - 搜尋筆記（支援標題/內容、相關性排序、模糊匹配）

- **增強的搜尋功能**：
  - 支援標題和內容搜尋
  - 依照相關性排序結果
  - 模糊匹配容許打字錯誤
  - 60 秒快取減少 API 呼叫

- **智慧重試機制**：
  - 自動重試遇到速率限制（429）或伺服器錯誤（5xx）
  - 指數退避避免過度衝擊 API
  - AI Agent 透明化：回應包含重試狀態和進度訊息

- **互動式 CLI**：測試和手動操作
- **非同步 API**：高效能整合
- **完整型別提示**：良好的 IDE 支援
- **原生 HackMD 客戶端**：使用 httpx（無外部 SDK 依賴）
- **支援新版 Google Gen AI SDK**：`google-genai`

## 需求環境

- Python >= 3.10
- [uv](https://github.com/astral-sh/uv)（推薦）或 pip
- [HackMD API Token](https://hackmd.io/settings#api)
- [Google Gemini API Key](https://aistudio.google.com/app/apikey)（有免費方案！）

## 安裝方式

### 使用 uv（推薦）

```bash
# 複製或下載專案
cd hackmd-agent-python

# 建立虛擬環境並安裝
uv venv
source .venv/bin/activate  # Windows 上：.venv\Scripts\activate
uv pip install -e .

# 安裝開發依賴
uv pip install -e ".[dev]"
```

### 使用 pip

```bash
cd hackmd-agent-python
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## 快速開始

```bash
# 設定環境變數
export HACKMD_API_TOKEN=<YOUR_HACKMD_TOKEN>
export GEMINI_API_KEY=<YOUR_GEMINI_KEY>

# 執行代理
hackmd-agent
```

## 使用方式

### CLI 模式

與 HackMD 代理互動式聊天：

```bash
export HACKMD_API_TOKEN=xxx
export GEMINI_API_KEY=xxx

hackmd-agent
```

對話範例：
```
與 HackMD 代理聊天（按 ctrl-c 結束）

😂: 列出我的筆記
🔧 使用：hackmd_list_notes...
🤖: 這是您的筆記：
1. 會議記錄 (id: abc123)
2. 專案計畫 (id: def456)

😂: 建立一個標題為"待辦事項"的筆記，內容為"# 我的任務\n- 任務 1\n- 任務 2"
🔧 使用：hackmd_create_note...
🤖: 已建立筆記"待辦事項"。您可以在 https://hackmd.io/xyz789 存取
```

### MCP 伺服器模式

本代理包含 MCP（Model Context Protocol）伺服器，可供 Claude Desktop、Cursor、OpenCode 等 MCP 相容用戶端直接使用。

**前置要求：**
- 必須設定 `HACKMD_API_TOKEN` 環境變數

**啟動伺服器：**

```bash
# 使用已安裝的指令碼
hackmd-mcp

# 或使用 fastmcp CLI（開發用）
uv run fastmcp run src/hackmd_agent/mcp_server.py:mcp
```

**以 SSE 伺服器執行（遠端模式）：**

如果您的用戶端（如 OpenCode）需要遠端連線：

```bash
# 在連接埠 8000 啟動 SSE 伺服器
uv run fastmcp run src/hackmd_agent/mcp_server.py:mcp --transport sse --port 8000
```

SSE 端點位置：`http://127.0.0.1:8000/sse`

**Claude Desktop 設定（本機 Stdio）：**

在 `claude_desktop_config.json` 中新增：

```json
{
  "mcpServers": {
    "hackmd": {
      "command": "uv",
      "args": [
        "run",
        "--with",
        "hackmd-agent-python",
        "hackmd-mcp"
      ],
      "env": {
        "HACKMD_API_TOKEN": "YOUR_TOKEN_HERE"
      }
    }
  }
}
```

**OpenCode 設定（遠端 SSE）：**

OpenCode 需要遠端連線，請先以 SSE 模式啟動伺服器（見上），然後設定 OpenCode 連線至 `http://127.0.0.1:8000/sse`。

```json
{
  "mcpServers": {
    "hackmd": {
      "url": "http://127.0.0.1:8000/sse"
    }
  }
}
```

### 程式化使用

```python
import asyncio
import os
from google import genai
from hackmd_agent import create_hackmd_tools, process_message

async def main():
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    tools = create_hackmd_tools(os.environ["HACKMD_API_TOKEN"])

    # 處理單一訊息
    result = await process_message(
        client,
        tools,
        "建立一個標題為'會議記錄'的筆記，內容為'# 今日會議\n\n- 討論路線圖'"
    )

    print("回應：", result.response)
    print("使用的工具：", result.tools_used)

asyncio.run(main())
```

### 與其他 AI 提供者整合

工具設計為框架無關：

```python
import asyncio
from hackmd_agent import create_hackmd_tools, to_gemini_tools, execute_tool

async def main():
    # 建立工具
    tools = create_hackmd_tools("your-token")

    # 取得工具定義（Gemini 函式呼叫格式）
    tool_definitions = to_gemini_tools(tools)

    # 手動執行工具
    result = await execute_tool(tools, "hackmd_create_note", {
        "title": "新筆記",
        "content": "# 你好世界"
    })

    import json
    print(json.loads(result))

asyncio.run(main())
```

## API 參考

### `create_hackmd_tools(api_token, base_url=None) -> list[Tool]`

建立 AI 代理用的 HackMD 工具。

| 參數 | 型別 | 必要 | 說明 |
|------|------|------|------|
| `api_token` | `str` | 是 | 您的 HackMD API token |
| `base_url` | `str` | 否 | 自訂 API 基礎 URL |

**回傳：** `Tool` 物件列表

---

### `run_agent(client, tools, config=None) -> None`

執行互動式 CLI 代理。

| 參數 | 型別 | 必要 | 說明 |
|------|------|------|------|
| `client` | `genai.Client` | 是 | Google Gen AI 客戶端 |
| `tools` | `list[Tool]` | 是 | 工具列表 |
| `config` | `AgentConfig` | 否 | 代理設定 |

**AgentConfig：**
| 屬性 | 型別 | 預設值 | 說明 |
|------|------|--------|------|
| `model` | `str` | `"gemini-2.5-flash"` | 使用的 LLM 模型 |
| `max_tokens` | `int` | `4096` | 回應的最大 token 數 |
| `system_prompt` | `str` | `"You are a helpful agent..."` | 系統提示詞 |

---

### `process_message(client, tools, message, conversation=None, config=None) -> ProcessResult`

以程式化方式處理單一訊息。

**回傳：** `ProcessResult` 資料類別：
```python
@dataclass
class ProcessResult:
    response: str              # AI 的文字回應
    conversation: list[dict]   # 更新後的對話歷史
    tools_used: list[str]     # 使用過的工具名稱列表
```

---

### `to_gemini_tools(tools) -> list[dict]`

將 Tool 列表轉換為 Gemini 函式宣告格式。

---

### `execute_tool(tools, name, input_data) -> str`

依名稱尋找並執行工具。回傳 JSON 字串。

## 可用工具

| 工具名稱 | 說明 | 必要參數 |
|---------|------|---------|
| `hackmd_list_notes` | 列出 HackMD 所有筆記 | 無 |
| `hackmd_read_note` | 依 ID 讀取筆記內容 | `noteId: str` |
| `hackmd_create_note` | 建立新筆記 | `title: str`, `content: str` |
| `hackmd_update_note` | 更新現有筆記 | `noteId: str`, `content: str` |
| `hackmd_delete_note` | 刪除筆記 | `noteId: str` |
| `hackmd_search_notes` | 搜尋筆記 | `keyword: str` |

### 建立/更新工具的選用參數

| 參數 | 型別 | 允許值 | 說明 |
|------|------|--------|------|
| `readPermission` | `str` | `"owner"`, `"signed_in"`, `"guest"` | 誰可以閱讀 |
| `writePermission` | `str` | `"owner"`, `"signed_in"`, `"guest"` | 誰可以寫入 |

## 搜尋功能說明

`hackmd_search_notes` 工具支援多種進階功能：

### 參數

| 參數 | 型別 | 預設值 | 說明 |
|------|------|--------|------|
| `keyword` | `str` | - | 搜尋關鍵字（必要） |
| `searchContent` | `bool` | `false` | 是否搜尋筆記內容（較慢） |
| `fuzzy` | `bool` | `false` | 啟用模糊匹配容許打字錯誤 |
| `limit` | `int` | `20` | 最大回傳結果數量（最大 100） |

### 相關性排序

搜尋結果會依相關程度排序：

| 分數 | 條件 |
|------|------|
| 100 | 標題完全匹配 |
| 90 | 標題開頭匹配 |
| 70 | 關鍵字包含在標題中 |
| 60 | 任意單字匹配 |

### 使用範例

**基本搜尋：**
```json
{
  "name": "hackmd_search_notes",
  "input": {
    "keyword": "會議"
  }
}
```

**內容搜尋：**
```json
{
  "name": "hackmd_search_notes",
  "input": {
    "keyword": "API",
    "searchContent": true,
    "limit": 10
  }
}
```

**模糊匹配（容許打字錯誤）：**
```json
{
  "name": "hackmd_search_notes",
  "input": {
    "keyword": "projct plan",
    "fuzzy": true
  }
}
```

## 重試機制與 AI Agent 透明度

所有工具回應都包含 `_meta` 欄位，提供 API 互動的透明資訊：

```json
{
  "data": [...],
  "_meta": {
    "retry_info": {
      "was_rate_limited": true,
      "total_attempts": 3,
      "total_wait_seconds": 3.5
    },
    "progress_messages": [
      "Rate limited. Waiting 1.0s... (attempt 1/3)",
      "Rate limited. Waiting 2.0s... (attempt 2/3)"
    ]
  }
}
```

### `_meta` 欄位說明

| 欄位 | 說明 |
|------|------|
| `was_rate_limited` | 是否遇到速率限制 |
| `total_attempts` | 總嘗試次數 |
| `total_wait_seconds` | 總等待時間（秒） |
| `progress_messages` | 詳細進度訊息陣列 |

### 重試策略

- **最大重試次數**：3 次
- **退避策略**：指數退避（1s → 2s → 4s）
- **最大等待**：32 秒
- **支援 Retry-After header**：優先使用伺服器指定的等待時間

這樣 AI Agent 可以清楚知道工具正在等待 API 回應，而不是誤判為無回應。

## 開發指南

```bash
# 安裝開發依賴
uv pip install -e ".[dev]"

# 執行測試
pytest

# 執行測試並顯示覆蓋率
pytest --cov=hackmd_agent

# 型別檢查
mypy src/

# 程式碼檢查
ruff check src/

# 格式化程式碼
ruff format src/
```

### 專案結構

```
hackmd-agent-python/
├── src/hackmd_agent/
│   ├── __init__.py       # 主要匯出
│   ├── types.py          # 工具介面定義
│   ├── hackmd_client.py  # 原生 HackMD API 客戶端
│   ├── tools.py          # HackMD 工具實作
│   ├── mcp_server.py     # MCP 伺服器（含快取和搜尋優化）
│   ├── agent.py          # 代理邏輯（CLI 和程式化）
│   └── cli.py            # CLI 入口點
├── tests/
│   ├── test_types.py
│   └── test_tools.py
├── pyproject.toml
├── CHANGELOG.md
├── AGENTS.md
└── README.md
```

## 授權

MIT 授權 - 詳見 [LICENSE](./LICENSE)

## 致謝

- 原始 Deno 版本：[tiny-hackmd-agent](https://hackmd.io/@EastSun5566/building-a-tiny-hackmd-agent)
- HackMD API：[HackMD 開發者入口](https://hackmd.io/@hackmd-api/developer-portal)
