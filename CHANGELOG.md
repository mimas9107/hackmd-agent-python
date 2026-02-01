# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- MCP (Model Context Protocol) server support
- OpenAI function calling format adapter
- Rate limiting and retry logic
- Batch operations support
- Async context manager for tool cleanup

---

## [1.1.0] - 2024-02-01

### Changed
- **BREAKING**: Migrated from Anthropic Claude SDK to Google Gemini API
  - Environment variable changed: `ANTHROPIC_API_KEY` → `GEMINI_API_KEY`
  - Default model changed: `claude-3-5-haiku-latest` → `gemini-2.0-flash`
- Updated `run_agent()` and `process_message()` function signatures
  - Removed `client` parameter (Gemini uses `genai.configure()` instead)
- Added `to_gemini_tools()` function for Gemini function calling format
- Kept `to_anthropic_tools()` for backward compatibility

### Added
- Google Gemini function calling support
- Free tier support (no API costs for basic usage!)

### Technical Details
- Uses `google-generativeai>=0.8.0` SDK
- Uses `asyncio.to_thread()` for async Gemini API calls
- Supports Gemini's native function response format

---

## [1.0.0] - 2024-02-01

### Added
- Initial release ported from Deno version (tiny-hackmd-agent)
- **Core Tools:**
  - `hackmd_list_notes` - List all notes from HackMD
  - `hackmd_read_note` - Read note content by ID
  - `hackmd_create_note` - Create new notes with title and content
  - `hackmd_update_note` - Update existing note content
  - `hackmd_delete_note` - Delete notes by ID
  - `hackmd_search_notes` - Search notes by title keyword (NEW)
- **Agent Features:**
  - Interactive CLI mode with emoji prompts
  - Programmatic `process_message()` async API for integration
  - Configurable model, max tokens, and system prompt
  - Tool execution with error handling
- **Developer Experience:**
  - Full type hints with Python 3.10+ syntax
  - pytest test suite with 11 tests
  - pytest-asyncio for async test support
  - mypy strict mode compatible
  - ruff for linting and formatting
  - Comprehensive README documentation

### Technical Details
- Python >= 3.10 required
- Native `HackMDClient` using `httpx` (no external HackMD SDK)
- Fully async implementation
- `dataclass` based Tool and ProcessResult types

### Changed (from Deno version)
- Migrated from Deno/TypeScript to Python
- Renamed tool prefixes from `list_notes` to `hackmd_list_notes` for clarity
- Added permission parameters (readPermission, writePermission) to create/update tools
- Implemented native HackMD API client instead of using external SDK

---

## Version Numbering

This project uses Semantic Versioning:

- **MAJOR** version for incompatible API changes
- **MINOR** version for new functionality (backwards compatible)
- **PATCH** version for bug fixes (backwards compatible)

## Links

- [README](./README.md)
- [AGENTS.md](./AGENTS.md) - AI Agent integration guide
- [HackMD API Documentation](https://hackmd.io/@hackmd-api/developer-portal)

[Unreleased]: https://github.com/user/hackmd-agent-python/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/user/hackmd-agent-python/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/user/hackmd-agent-python/releases/tag/v1.0.0
