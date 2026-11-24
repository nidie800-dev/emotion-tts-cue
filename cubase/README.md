# 在 Cubase 里使用 EmoCue

EmoCue 生成两样对轨素材：

- `full.wav`：整轨音频
- `cues.mid`：每个分段起点一个 MIDI marker

## 步骤

1. 新建工程，tempo 设为 **120 BPM**（与 `cues.mid` 内的 tempo 事件一致）。
2. 把 `full.wav` 拖到第 1 小节、时间轴 0 秒处。
3. `File → Import → MIDI File`，选择 `cues.mid`。
4. 在 Marker 窗口确认 marker 已出现；名字格式为 `01 happy 0.8`。
5. 用 marker 快速定位每一句，按需做 EQ、压缩、混响和自动化。

> 如果 marker 位置有偏移，先在 Cubase 里确认工程 tempo 是 120 BPM；仍不对就用 `cues.csv` 的 `start` 秒数手动放 marker。`cues.csv` 是绝对秒数，不受 tempo 影响。

## 推荐轨道布局

```text
Voice      ── 主对白/演唱
Whisper    ── 耳语、近场气声
SFX        ── 笑声、叹气、哭声、环境
Music      ── 配乐
Reverb Bus ── 空间统一
```

## ASMR 后期建议

- 耳语段落单独一条轨道，做低切 + 轻微饱和 + 近场混响
- 用 `cues.csv` 的 `emotion` 列批量筛选需要处理的段落
- 360° 双耳渲染在 Roadmap 里，当前版本先做普通立体声

## 为什么用 MIDI marker 而不是 CSV

Cubase 不原生导入 CSV marker，但会读取 MIDI 文件里的 marker meta 事件。`cues.mid` 就是为此生成的：一个 Type-0 MIDI，120 BPM，480 PPQ，每个分段起点一个 marker。
