# EmoCue

把带情感标签的剧本，变成**分段 TTS 音频 + Cue 表 + Cubase 时间线标记**。

```text
[happy:0.8] 今天天气真好。
[whisper:0.9] 靠近一点，别出声。
[pause:0.6]
[sad:0.5] 可是我还是有点难过。
```

一条命令，得到 4 段不同情感/强度的音频、一条完整 `full.wav`、一份 `cues.csv`，以及一个导入 Cubase 就能对齐时间线的 `cues.mid`。

**一句话：它解决的是“多段配音在 DAW 里对轨太麻烦”这个问题。** 不训练模型、不打包权重，只做脚本、TTS 和 Cubase 之间的最后一公里。

## 解决什么问题

现在的 TTS 工具大多一次只生成一句、一种情感。做多情感对白、有声书或 ASMR 时，你要：

1. 手动把剧本切成一句一句
2. 逐句选情感、生成、试听、重生成
3. 记录每句的起止时间
4. 导进 DAW 再手动对轨

EmoCue 把第 1–3 步自动化，并给 DAW 一份可直接用的时间线标记。它不绑定某个模型：CosyVoice、GPT-SoVITS、Fish Audio S2 Pro，或你自己的 TTS 服务，都能接。

## 特性

- **情感标签**：`[happy]`、`[sad:0.6]`、`[whisper]`、`[laugh]`、`[sigh]`、`[cry]`
- **情感粘性**：`[sad:0.6]` 单独一行，后面几句自动继承，不用每句重写
- **停顿控制**：`[pause:0.5]`、`[pause:500ms]`
- **后端无关**：`sapi`（Windows 自带中文语音，零安装）、`mock`（测试音）、`http`（本地/远程 TTS 服务）、`command`（任意 TTS 命令行）
- **DAW 友好**：`cues.csv` 记录每段秒数；`cues.mid` 带 marker，Cubase 导入即对轨
- **ComfyUI 节点**：脚本 → 整轨音频 + Cue 表 + MIDI
- **纯标准库核心**：WAV 读写、拼接、MIDI 写入都不依赖 ffmpeg

## 快速开始（不需要显卡、不需要模型）

```bash
pip install -e .
python -m emocue demo --out demo_out
```

输出：

```text
full.wav     demo_out/full.wav
cues.csv     demo_out/cues.csv
cues.mid     demo_out/cues.mid
project.json demo_out/project.json
segments     5
duration     10.97s @ 22050 Hz
```

`sapi` 后端会用 Windows 自带的中文语音（Microsoft Huihui）直接生成真实中文语音；`--mock` 才用正弦波测试音。

## 脚本语法

```text
# 注释
[happy:0.8] 今天天气真好。
[whisper:0.9] 靠近一点，别出声。
[pause:0.6]
[sad] 可是我还是有点难过。
[laugh] 算了，不说了。
```

| 标签 | 含义 |
|---|---|
| `[happy]` | 情感，强度默认 0.5 |
| `[sad:0.6]` | 情感 + 强度（0–1） |
| `[whisper]` `[laugh]` `[sigh]` `[cry]` | 耳语/笑/叹气/哭腔 |
| `[pause:0.5]` `[pause:500ms]` | 静音段 |
| 单独一行的 `[sad:0.6]` | 设置后续句子的默认情感 |

支持的情感：`neutral`、`happy`、`sad`、`angry`、`surprised`、`fearful`、`whisper`、`laugh`、`sigh`、`cry`。  
别名：`joy` → `happy`，`anger` → `angry`，`fear` → `fearful`，`surprise` → `surprised`。

## 接真实 TTS

### 0. Windows SAPI（默认，零安装）

Windows 自带 `System.Speech`，不需要显卡、不需要下载模型：

```bash
python -m emocue render examples/asmr_script.txt --backend sapi --out out/
```

会用 `Microsoft Huihui Desktop`（zh-CN）生成真实中文语音。情感通过语速/音量近似：
`happy` 更快更亮，`sad` 更慢更轻，`whisper` 更轻，`laugh` 更快。
它不会真的笑/哭/叹气；要真实情感，接下面的 HTTP 后端。

### 1. HTTP 后端（推荐，接 CosyVoice / GPT-SoVITS）

EmoCue 会向 `--url` POST：

```json
{
  "text": "今天天气真好。",
  "emotion": "happy",
  "intensity": 0.8,
  "language": "ja",
  "sample_rate": 24000
}
```

返回以下任意一种：

- `Content-Type: audio/wav` 的 WAV 字节
- `{"audio_base64": "..."}` 或 `{"audio": "..."}`
- `{"audio_url": "https://..."}`

```bash
python -m emocue render examples/asmr_script.txt \
  --backend http \
  --url http://127.0.0.1:8000/tts \
  --out out/
```

你可以用 FastAPI/Flask 把 **CosyVoice 3**（Apache 2.0，支持日语与情感 instruct）或 **GPT-SoVITS**（MIT，支持日语克隆）包一层这个接口。

### 2. 命令行后端

适合已经有 TTS CLI 的情况：

```bash
python -m emocue render examples/asmr_script.txt \
  --backend command \
  --command "python my_tts.py --text {text} --emotion {emotion} --intensity {intensity} --out {out} --language {language}" \
  --out out/
```

占位符：`{text}`、`{emotion}`、`{intensity}`、`{out}`、`{language}`、`{sample_rate}`。

## 输出文件

```text
out/
├── full.wav              # 整轨，段间带 gap 静音
├── cues.csv              # 每段：起止秒数、情感、强度、文本、文件
├── cues.mid              # MIDI marker，Cubase 导入即得时间线标记
├── project.json          # 可复现参数与完整分段信息
└── segments/
    ├── 0001_whisper_0.90.wav
    ├── 0002_pause_0.60.wav
    └── ...
```

## ComfyUI

把 `comfyui_emotion_tts_cue` 复制到 `ComfyUI/custom_nodes/`，然后：

```bash
pip install -e .
```

重启 ComfyUI，搜索 **EmoCue Render (Emotion TTS + Cues)**。节点输出 `AUDIO`、`cues_csv`、`cues_mid`，可直接接 `Save Audio`。

详见 [comfyui_emotion_tts_cue/README.md](comfyui_emotion_tts_cue/README.md)。

## Cubase

1. 新建工程，把 `full.wav` 拖到第 1 小节、0 秒位置。
2. `File → Import → MIDI File`，选择 `cues.mid`。
3. 导入时保留 MIDI 的 tempo 事件（120 BPM），marker 就会和音频对齐。
4. 如果版本差异导致 marker 不显示，用 `cues.csv` 的 `start` 秒数手动放 marker。

详见 [cubase/README.md](cubase/README.md)。

## 为什么不是“又一个 TTS 节点”

EmoCue 不训练模型，也不打包权重。它解决的是**模型和 DAW 之间的最后一公里**：

```text
script.txt
   │  parser
   ▼
segments (emotion, intensity, pause)
   │  backend (mock / HTTP / command)
   ▼
segments/*.wav ──► full.wav
   │
   ├──► cues.csv
   └──► cues.mid ──► Cubase markers
```

模型可以换，流程不变；今天是 CosyVoice，明天换成别的，只要包一层 HTTP 或命令行。

## 许可证与模型

- **本仓库代码**：MIT，见 [LICENSE](LICENSE)。
- **不包含任何模型权重**。使用者需自行安装并遵守模型许可证：
  - CosyVoice：代码 Apache 2.0，权重以其 ModelScope 页面为准
  - GPT-SoVITS：MIT
  - Fish Audio S2 Pro：Fish Audio Community License（研究/非商业为主，商用需授权）
- **音色克隆**：只使用你本人的声音，或已获得明确授权的参考音频。不要克隆动漫角色、公众人物或他人声音。

## Roadmap

- [ ] CosyVoice 3 的即用 HTTP adapter 示例
- [ ] 360° ASMR 双耳渲染节点（HRTF）
- [ ] 情感 TTS 评测报告（MOS/CMOS/ABX + F0/能量/语速）
- [ ] Cubase 工程模板与分轨导出脚本

## 致谢

- 标签语法参考了 ASMR/有声书制作中常见的“脚本 + 情绪标记”工作流
- 情感 TTS 生态：CosyVoice、GPT-SoVITS、Fish Audio S2 Pro
- 灵感来自社区里的 Iroha TTS 展示；本项目不复用其代码或权重
