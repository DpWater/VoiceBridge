# VoiceBridge

本地优先的开发者语音指令工作台：**Speak → Transcribe → Refine → Review → Dispatch**。

这是一个可运行的 Phase 1 MVP。它会录制麦克风音频、调用本地 `faster-whisper` 转写、可选使用 OpenAI-compatible / DeepSeek API 进行忠实纠错，最后让用户编辑并确认后复制到剪贴板。它不会自动改代码、不会自动提交到任何 Coding Agent，也不会把“模拟 Enter”宣称为任务已送达。

## 当前功能

- PySide6 主窗口、悬浮录音状态条和系统托盘入口
- 内存中的 16 kHz 单声道 PCM 录音，录音结束即清空缓存
- `FasterWhisperProvider`：真实 API、模型惰性加载和临时 WAV 清理
- 可选 OpenAI-compatible / DeepSeek 忠实纠错（API Key 保存于系统钥匙串）
- 原始文本与可编辑结果对照、确认后安全复制
- 单任务状态机与后台模型工作线程，避免结果覆盖
- Provider / Target / Platform 明确接口，以及安全的预配置命令目标基础类

## 快速开始

需要 Python 3.11+；macOS 需要在系统设置中允许麦克风。首次运行 `faster-whisper` 可能下载模型，模型许可证及缓存由其上游管理，未包含在本仓库或安装包中。

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
voicebridge
```

点击 **Record** 开始，再点击 **Stop and transcribe**。完成识别后可编辑文字并点击 **Copy**。如要使用 LLM，请通过系统钥匙串写入 `VoiceBridge / openai-compatible` 的密钥，再在 `~/.voicebridge/settings.json` 设置 `use_enhancement: true`（图形设置页仍在开发）。

### 自动路由到 Cursor / Trae 当前聊天

此功能仅在 macOS 上的 **Accessibility** 权限已经授予后可用，并且不会自动按 Enter。先点击 Cursor 或 Trae **右侧聊天栏底部的输入框**，再通过全局快捷键开始录音；快捷键不会改变该输入焦点。审阅确认后 VoiceBridge 会返回该 IDE，并把文本粘贴到原本获得焦点的右侧聊天栏。手动点击 VoiceBridge 主窗口的 **Record** 会把 VoiceBridge 本身记录为前台应用，不能用于此路由。

在 `~/.voicebridge/settings.json` 中明确开启（默认关闭）：

```json
{
  "hotkey_enabled": true,
  "hotkey": "<cmd>+<ctrl>+<shift>+v",
  "default_target": "cursor-current",
  "gui_paste_enabled": true
}
```

对 Trae，将 `default_target` 改为 `trae-current`。如果当前前台应用与所选目标不符、无法恢复窗口，或未获得辅助功能权限，发送会失败并保留审阅内容。VoiceBridge 不读取 Cursor 或 Trae 桌面聊天记录；公开 CLI 会话与 IDE GUI 对话是不同能力。

默认快捷键为 `⌘⌃⇧V`，避免占用 IDE 常用的双修饰键快捷键；如果 VoiceBridge 成功注册该全局组合键，它会优先接收该组合键。

## 已验证与待验证

`pytest` 中的 mock 自动化测试验证了状态机、配置、WAV 写入和 ASR→LLM 调度逻辑。真实 PySide6 启动、麦克风权限、模型下载/推理、钥匙串、托盘和全局快捷键必须在目标 macOS/Windows 设备上手工验证；它们没有被标记为已通过。

## 当前限制与路线图

- 默认发送方式是复制到剪贴板。macOS 可显式启用 `gui_paste_enabled`，将文本粘贴到录音前已验证的 Cursor 或 Trae 活动窗口；不会按 Enter，也不会读取 GUI 对话历史。Codex/Cursor/Trae CLI 会话路由仍在开发。
- 配置中的快捷键字段已持久化；现有可选 `pynput` 后端只适用于切换式组合键。按住说话需要平台权限和按键释放实现，尚未接入 UI。
- 设置向导、模型下载进度、项目配置、SQLite 历史、多模型管理和 Windows 适配属于下一阶段。

详见 [架构](docs/architecture.md)、[ADR](docs/decisions.md)、[状态机](docs/workflow.md)、[权限说明](docs/platform-permissions.md) 与 [验收计划](docs/acceptance.md)。

## 安全与隐私

默认不保存音频。启用云端 LLM 时，转写文本与术语表将发送给你配置的服务；请先确认其隐私政策。切勿把 API Key 放进仓库、环境输出或 issue。

## License

MIT，见 [LICENSE](LICENSE)。第三方库和模型权重各自适用其上游许可证。
