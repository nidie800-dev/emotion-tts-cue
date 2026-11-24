# ComfyUI 安装

1. 把整个 `comfyui_emotion_tts_cue` 文件夹复制到：

   ```
   ComfyUI/custom_nodes/comfyui_emotion_tts_cue
   ```

2. 安装 EmoCue 核心包（在仓库根目录执行）：

   ```
   pip install -e .
   ```

3. 重启 ComfyUI，在节点搜索里找 **EmoCue Render (Emotion TTS + Cues)**，分类是 `audio/EmoCue`。

## 节点参数

| 参数 | 说明 |
|---|---|
| `script` | 带情感标签的脚本，例如 `[happy:0.8] 你好` |
| `backend` | `sapi` 用 Windows 自带中文语音（零安装）；`mock` 测试音；`http` 接本地/远程 TTS 服务；`command` 调任意 TTS 命令行 |
| `output_dir` | 输出目录，默认 `emocue`（位于 ComfyUI 的 `output/` 下） |
| `gap` | 段与段之间的静音秒数 |
| `sample_rate` | 期望采样率；真实后端应返回同样采样率 |
| `language` | 传给后端的语言代码，如 `ja`、`zh` |
| `api_url` | `http` 后端的地址，默认 `http://127.0.0.1:8000/tts` |
| `command_template` | `command` 后端的命令模板 |

## 输出

- `audio`：整轨音频，可直接接 ComfyUI 的 `Save Audio`
- `cues_csv`：每段的开始/结束、情感、强度、文本、文件名
- `cues_mid`：带标记的 MIDI，导入 Cubase 后自动生成时间线标记

## HTTP 后端契约

节点会向 `api_url` POST：

```json
{"text": "...", "emotion": "happy", "intensity": 0.8,
 "language": "ja", "sample_rate": 24000}
```

返回 `audio/wav` 字节，或 JSON `{"audio_base64": "..."}` / `{"audio_url": "..."}`。
CosyVoice、GPT-SoVITS 或你自己的服务都可以包一层这个接口。
