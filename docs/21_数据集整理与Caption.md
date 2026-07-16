# Wan2.2 训练数据集整理与 Caption 状态

> 最后更新：2026-07-16

---

## 一、Wan2.2 已转换数据

| 数据集 | 视频数 | 大小 | Caption | 方案 |
|--------|--------|------|---------|------|
| **MIRA** | ~1.3M | ~3T | JSONL action | LLM 将 action→自然语言 |
| **Charades** | 9,848 | 32G | 动作标签 | **需 VLM 打 caption** |
| **EasyCom** | 271 | 2.3G | 对话文本 | 已有 |
| **RAVDESS** | 2,880 | 1G | 情感标签 | 已删除/低优先级 |
| **DexYCB** | 40 | 19M | ❌ | **需 VLM 打 caption** |
| **EPIC** | 3 | 295M | 动作标注 | 场景单一/暂缓 |
| **H2O** | 0 | — | ❌ | 图片序列处理失败 |

---

## 二、原始数据待处理

| 数据集 | 大小 | 格式 | Caption | 方案 |
|--------|------|------|---------|------|
| **OpenVidHD** | 3.0T | 14 zips, 300K+ MP4 | ❌ | **需 VLM 打 caption** |
| **H2O** | 177G | 183K img | ❌ | 先图片→视频，再 caption |
| **DexYCB** | 71G | 348K img | ❌ | 先图片→视频，再 caption |
| **HOI4D** | 3.3G | 下载中 | 标注存在 | 视频含 3D 标注 |
| **EPIC-KITCHENS** | 8.7G | 28 MP4 | 动作标注 | 场景单一/暂缓 |
| **EasyCom** | 102G | 已提取 | 对话文本 | 已有 |

---

## 三、新下载数据（待处理）

| 数据集 | 大小 | Caption | 方案 |
|--------|------|---------|------|
| **HOIGen-1M** | 235G, 10 zips | CSV caption | 已有！直接可用 |
| **Seamless Interaction** | 50G, 50 tars | 待确认 | 需检查 tar 内容 |
| **Matrix Dataset** | 下载中 | 游戏控制信号 | 控制信号→通用 caption |
| **CelebV-HQ** | 76 videos | 属性标注 | 属性→自然语言 |
| **Action100M** | 278 videos | 动作标签 | 标签→自然语言 |

---

## 四、Caption 需求总结

| 需打 Caption | 视频数 | 打标方式 |
|-------------|--------|---------|
| **OpenVidHD** | 300K+ | VLM (InternVL/Qwen-VL) |
| **MIRA** | 1.3M | 用 JSONL action 模板生成 |
| **Charades** | 9,848 | VLM |
| **DexYCB** | 348K img | VLM（先转视频） |
| **H2O** | 183K img | VLM（先转视频） |

| 已有 Caption | 视频数 | 说明 |
|-------------|--------|------|
| **HOIGen-1M** | 1M+ | CSV caption 直接可用 |
| **EasyCom** | 323 | 对话文本 |
| **RAVDESS** | 2,880 | 情感标签（低优先级） |

---

## 五、打 Caption 方案

1. **VLM 方案**：用 InternVL/Qwen-VL 对视频帧采样生成自然语言描述
2. **MIRA 模板方案**：JSONL 含 action/physics → 用 LLM 模板转为自然语言
3. **HOIGen-1M**：直接使用 CSV caption，无需额外处理
