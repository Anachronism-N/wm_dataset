# 项目进展全记录

> 最后更新：2026-07-16

---

## 一、Wan2.2 训练数据总览

### 已转换 (720p/24fps MP4)

| 数据集 | 视频数 | 大小 | Caption | 用途 |
|--------|--------|------|---------|------|
| **MIRA processed** | 2,041,279 | 5.4TB | JSONL(action)→LLM | 游戏多视角交互 |
| Charades | 9,848 | 32GB | 动作标签→VLM | 日常居家活动 |
| EasyCom | 271 | 2.3GB | 对话文本(已有) | AR多人对话 |
| RAVDESS | 2,880 | 1GB | 低优先级 | 情感表达(已排除) |
| OpenVidHD | 1,000 | 1.1GB | →VLM | 通用高清视频 |
| DexYCB | 40 | 19MB | →VLM | 手物抓取 |
| EPIC | 3 | 295MB | 暂缓 | 厨房HOI |
| **合计** | **~1,933,000** | **~5.1TB** | | |

### 原始数据

| 数据集 | 大小 | 格式 | 说明 |
|--------|------|------|------|
| MIRA Rocket Science | 8.3TB | 4,797 tars, 2.1M MP4 | 游戏多视角，持续处理中 |
| OpenVidHD | 3.0TB | 14 zips, 300K+ MP4 | 通用高清视频 |
| H2O | 177GB | tar.gz, 183K img | 双手操作图片序列 |
| DexYCB | 71GB | 3 subjects, 348K img | 手物抓取图片序列 |
| EasyCom | 102GB | 3,421 files | AR对话(已提取) |
| EPIC-KITCHENS | 8.7GB | 28 MP4 | 厨房HOI |
| Charades | 31GB | 9,848 MP4 | 日常活动 |

### 新下载数据

| 数据集 | 大小 | 状态 | Caption | 类型 |
|--------|------|------|---------|------|
| **HOIGen-1M** | 235GB | 10 zips 完成 | CSV自带 | 人-物交互 |
| **Seamless Interaction** | 50GB | 50 tars 完成 | 待检查 | 人人交互 |
| **Matrix Dataset** | ~1.1TB | git clone中 | 控制信号 | 游戏场景(Forza+Cyberpunk) |
| Action100M (yt-dlp) | 278 videos | cookies过期 | 动作标签 | 人类动作 |
| CelebV-HQ (yt-dlp) | 76 videos | cookies过期 | 属性标注 | 数字人脸 |

---

## 二、下载管线状态

| 管线 | 状态 | 进度 |
|------|------|------|
| MIRA → Wan2.2 | 活跃 | 1,918,956 视频 |
| Matrix git clone | 活跃 | ~1.1TB |
| yt-dlp Action100M | cookies过期 | 278/60,000 |
| yt-dlp CelebV-HQ | cookies过期 | 76/13,844 |
| HOI4D bypy | 已停 | 3.3GB |
| VFHQ bypy | 不可用 | 需百度客户端 |
| HOT3D/Aria/Nymeria | 不可用 | Facebook CDN 不可达 |

---

## 三、Caption 方案

### 已就绪 (有 Caption)

| 数据集 | Caption 来源 | 质量 |
|--------|------------|------|
| **HOIGen-1M** | CSV caption_info | 高质量自然语言描述 |
| EasyCom | 对话转录文本 | 可直接使用 |
| MIRA | JSONL action/physics | 需LLM模板转为自然语言 |

### 待打标 (需要 Qwen3-VL-235B)

| 数据集 | 视频数 | 帧采样 | 预计时间 |
|--------|--------|--------|---------|
| OpenVidHD | 300K+ | 8帧/视频 | ~1.7天 |
| Charades | 9,848 | 8帧/视频 | ~1.5小时 |
| DexYCB (→视频) | 348K img | 先处理 | 待定 |
| H2O (→视频) | 183K img | 先处理 | 待定 |

### 打标方案

```
方案 A: Qwen3-VL-235B-A22B (最高质量)
  8帧采样 → 自然语言描述
  8副本 → 80-120 videos/min

方案 B: HOIGen-1M CSV (直接使用)
  1M+ video-caption pairs 直接可用

方案 C: MIRA JSONL 模板
  action/physics数据 → LLM模板 → 自然语言caption
```

---

## 四、数据集全列表 (90个)

### 已下载 (14个)
MIRA, OpenVidHD, Charades, EasyCom, H2O, DexYCB, EPIC-KITCHENS, RAVDESS, CREMA-D, InterHuman, HoloAssist, Action100M, CRAMA-D, BEAT2

### 下载中 (8个)
HOIGen-1M, Seamless Interaction, Matrix Dataset, HOI4D, VFHQ, Inter-X, HOT3D, Aria ADT/AEA

### 已申请 (10个)
Ego4D, OpenHumanVid, Assembly101, Ego-Exo4D, Nymeria, LRS2, LRS3, NoXi, MultiMediate, UDIVA

### 已排除 (21个)
AMASS, Human3.6M, HumanML3D, Motion-X, AIST++, BEAT, TalkSHOW, Trinity, GRAB, CMU Panoptic, ARCTIC, Something-Something V2, ViCo, AgiBot World, CALVIN, LIBERO, Habitat, AI2-THOR, ALFRED, BEHAVIOR, VirtualHome, TEACh, RoboCasa365, CHiME-6

### 暂缓 (37个)
其余模拟器/机器人/评测/音频数据集
