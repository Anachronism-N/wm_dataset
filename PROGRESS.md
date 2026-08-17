# 项目进展全记录

> 最后更新：2026-08-18

---

## 0、本轮推进记录（2026-08-18）

### 数据处理全部完成

14 个数据集全部完成转码/切分为 Wan2.2-TI2V 格式（1280×704/704×1280, 24fps, 4s clips, libopenh264）：

| 数据集 | clips | 状态 |
|---|---|---|
| MIRA | 2,073,297 | ✅ 无需转码（已有 caption_i2v） |
| Ego-Exo4D | 22,161 | ✅ 转码完成（50,383 视频 → 22,161 有效 clips） |
| CelebV-HQ | 1,277,996 | ✅ 转码完成（12,988 视频 → 1.28M clips） |
| HOIGen | 231,084 | ✅ |
| Charades | 73,603 | ✅ |
| NoXi | 41,744 | ✅ |
| VFHQ | 34,173 | ✅ |
| Seamless | 25,432 | ✅ |
| Direct (Project Aria) | 25,312 | ✅ |
| Matrix | 14,124 | ✅ |
| EasyCom | 3,920 | ✅ |
| DexYCB | 2,400 | ✅ |
| OpenVidHD | 1,317 | ✅ |
| H2O | 297 | ✅ |
| **合计** | **~3.83M clips** | |

### HF 上传进度

仓库 `NZC415/wan22-processed-clips`（已改为公开仓库，无存储限制）

| 数据集 | shards | 状态 |
|---|---|---|
| H2O | 1 | ✅ |
| OpenVidHD | 1 | ✅ |
| DexYCB | 1 | ✅ |
| EasyCom | 2 | ✅ |
| Matrix | 5 | ✅ |
| Direct | 8 | ✅ |
| Seamless | 4 | ✅ |
| VFHQ | 9 | ✅ |
| NoXi | 4 | ✅ |
| Charades | 14 | ✅ |
| HOIGen | 24/61 | 🔄 上传中 |
| Ego-Exo4D | ~3 | ⏳ |
| CelebV-HQ | ~160 | ⏳ |
| MIRA | ~1013 | ⏳ |
| **已上传** | **73 shards (~584GB)** | |

### Caption 进度

| 数据集 | clips | 已 caption | 状态 |
|---|---|---|---|
| MIRA | 2,073,297 | 1,216,449 | ✅ 已有 caption_i2v |
| HOIGen | 231,084 | 231,083 | ✅ |
| CelebV-HQ | 1,277,996 | 0 | ❌ 待 caption（queue 已就绪） |
| Charades | 73,603 | 73,601 | ✅ |
| NoXi | 41,744 | 41,744 | ✅ |
| VFHQ | 34,173 | 34,173 | ✅ |
| Seamless | 25,432 | 25,432 | ✅ |
| Direct | 25,312 | 25,310 | ✅ |
| Ego-Exo4D | 22,161 | 22,161 | ✅ |
| Matrix | 14,124 | 14,124 | ✅ |
| EasyCom | 3,920 | 3,913 | ✅ |
| DexYCB | 2,400 | 2,400 | ✅ |
| OpenVidHD | 1,317 | 1,317 | ✅ |
| H2O | 297 | 297 | ✅ |
| **合计** | **~3.83M** | **~1.69M (44%)** | |

### Caption Queue 文件

位置：`training_metadata/caption_queues/`

| 文件 | clips | 说明 |
|---|---|---|
| `celebvhq.jsonl` | 1,277,996 | 待 caption，最大批次 |
| `egoexo4d_full.jsonl` | 22,161 | 已完成 ✅ |
| `matrix_full.jsonl` | 14,124 | 已完成 ✅ |
| `caption_queue_all.jsonl` | 469,007 | 合并清单（不含 CelebV-HQ/MIRA） |

### 新增数据集（本轮）

| 数据集 | 来源 | clips | 说明 |
|---|---|---|---|
| CelebV-HQ | `NZC415/CelebV-HQ-archives` (HF) | 1,277,996 | 数字人脸视频 |
| VFHQ | `NZC415/VFHQ-videos-archives` (HF) | 34,173 | 人脸视频 |
| Direct (Project Aria) | `NZC415/direct-downloads-archives` (HF) | 25,312 | ADT/HOT3D/AEA 等第一人称 |

### 仍在进行

| 任务 | 状态 |
|---|---|
| HOIGen HF 上传 | 🔄 24/61 shards |
| HoloAssist 修复 | 39.7%（~33 天，不阻塞） |
| CelebV-HQ caption | ❌ 待 caption（128 万 clips） |

---

## 0、本轮推进记录（2026-08-12）

### 数据下载

#### 新增下载（从 HF 私有仓库）
| 数据集 | 体积 | 来源 | 状态 |
|---|---|---|---|
| **CelebV-HQ** | 303GB (38 tars) | `NZC415/CelebV-HQ-archives` | ✅ 下载完成，🔄 提取中 |
| **VFHQ** | 20GB (3 tars) | `NZC415/VFHQ-videos-archives` | ✅ 下载完成，🔄 提取中 (3,717 MP4) |
| **Direct-downloads** | 61GB (8 tars) | `NZC415/direct-downloads-archives` | ✅ 下载完成，🔄 提取中 |
| **Wan2.2-TI2V-5B** | 34GB | ModelScope | ✅ 下载完成 (825 tensors 校验通过) |
| **Qwen2.5-VL-7B** | 16GB | ModelScope | ✅ 下载完成 |

#### Direct-downloads 内容（之前 CDN 403 无法下载的 Project Aria 系列）
| 子数据集 | 文件数 | 类型 |
|---|---|---|
| Hot3DQuest | 226 | 手物交互（Quest 版） |
| ADT (Aria ADT) | 219 | 日常活动 |
| Hot3DAria | 192 | 手物交互（Aria 版） |
| AriaEverydayActivities | 129 | 日常行为 |
| 合计 | 768 | 第一人称视角 |

#### 下载/修复中
- **HoloAssist 修复**：ahat_depth 38.4%（230.8GB/601.8GB），~137KB/s
- **Matrix part_1000/1100**：ModelScope 上 0 字节文件，无法下载（2/39 缺失，可忽略）

### 数据处理（转码+切分为 Wan2.2 格式）

#### 已完成（11 个数据集，统一 manifest train 70,151 / val 7,783）
| 数据集 | clips | 格式 | manifest |
|---|---|---|---|
| MIRA | ~2,000,000 | 1280×704 24fps 4s | ✅ |
| HOIGen | 231,084 | 1280×704 24fps 4s | ✅ |
| Charades | 73,603 | 1280×704 24fps 4s | ✅ |
| NoXi | 41,744 | 1280×704 24fps 4s | ✅ |
| Seamless | 25,432 | 704×1280 24fps 4s (竖屏) | ✅ |
| Ego-Exo4D | ~15,600+ (🔄 增长中) | 1280×704 24fps 4s | ✅ |
| Matrix | 14,124 | 1280×704 24fps 4s | ✅ |
| EasyCom | 3,920 | 1280×704 24fps 4s | ✅ |
| DexYCB | 2,400 | 1280×704 24fps 2.5s | ✅ |
| OpenVidHD | 1,317 | 704×1280 24fps 4s (竖屏) | ✅ |
| H2O | 297 | 1280×704 24fps 4s | ✅ |

#### 处理中
| 任务 | 进度 | 预计完成 |
|---|---|---|
| Ego-Exo4D 转码 | 500/50,383 (1%), 38,925 clips | ~33h |
| VFHQ 提取 | 3,717 MP4 (3 tars) | ~10min |
| Direct-downloads 提取 | 153 MP4 (8 tars, 768 expected) | ~30min |
| CelebV-HQ 提取 | shard 1/38 | ~2h |
| HoloAssist 修复 | 38.4% | ~33 天 |

#### HF 上传
- 仓库 `NZC415/wm-dataset`（私有）已上传：
  - 统一 manifest（train 70,151 / val 7,783，JSONL + CSV）
  - 11 个数据集的 `*_wan22/manifest_wan22.jsonl`
  - 全部处理脚本
  - 训练配置 + 审计报告 + 文档

### Caption 进度

- **在其他节点进行**（用户自行部署）
- Node B: Qwen3-VL-235B-A22B-Instruct-FP8, TP=8
- Node A: Qwen2.5-VL-7B-Instruct, 8 副本
- 详见 `docs/29_Qwen3VL_235B_部署指南.md` 和 `docs/29_VLM_Caption_全量打标指南.md`
- 截至 2026-07-26：已完成 1,307,682 / 2,192,164（59.6%）

### 新增文档
- `docs/26_数据集收集与许可.md` — 全部数据集下载状态、许可分析、HF 策略
- `docs/27_数据预处理与训练格式适配.md` — Wan2.2 格式要求、帧采样逻辑、转码/切分方案
- `docs/28_数据总量与项目目标评估.md` — 数据总量、HF 上传可行性、项目目标覆盖度
- `docs/29_Qwen3VL_235B_部署指南.md` — 235B 模型 GPU 需求、vLLM 部署、caption 流程

### 新增脚本
- `scripts/transcode_and_clip.py` — 批量转码+切分（libopenh264, 多进程, 4s 段）
- `scripts/build_unified_manifest.py` — 11 数据集统一 manifest 构建
- `scripts/generate_wan22_manifest.py` — 为 *_wan22 目录生成 manifest
- `scripts/decode_audit.py` — 随机抽样解码+首帧审计
- `scripts/filter_existing_videos.py` — 全量路径存在性校验
- `scripts/caption_with_transformers.py` — Qwen2.5-VL transformers 直驱 caption
- `scripts/extract_matrix_zips.py` — 从 Matrix zip 抽样提取视频

### 关键技术决策
- **帧采样**：Wan2.2 从 frame 0 取 49 连续帧（~2s），无随机起始 → 段长设 4s（浪费最少）
- **编码器**：环境无 libx264（--disable-gpl），改用 libopenh264 + -b:v 5M
- **切分**：>5s 视频切为 4s 段；2-5s 不切分；<2s 自动降帧
- **分辨率**：首轮仅横屏（1280×704），竖屏（704×1280）后续加入
- **235B 部署**：最少 8× H20-96GB（bf16 TP=8）或 4× H20-96GB（FP8 TP=4）

---

## 0、本轮推进记录（2026-07-26）

### VLM Caption 全量打标（阶段二进行中）

详见 `docs/29_VLM_Caption_全量打标指南.md`

#### 双节点并行部署
- **Node B (29.127.33.93)**：Qwen3-VL-235B-A22B-Instruct-FP8，TP=8 单副本，vLLM 0.16.1
- **Node A (29.191.211.184)**：Qwen2.5-VL-7B-Instruct，8 副本 × TP=1，--enforce-eager（235B 因 FlashInfer AllReduce 硬件问题无法部署，改用 7B dense 模型）

#### Caption 进度（2026-07-26 17:00 更新）
| 数据集 | 总视频数 | 已完成 | 失败 | 状态 |
|---|---|---|---|---|
| easycom | 3,920 | 3,913 | 7 | ✅ 完成 |
| noxi | 41,744 | 41,744 | 0 | ✅ 完成 |
| charades | 73,603 | 73,601 | 2 | ✅ 完成 |
| mira | 2,073,297 | 1,188,624 | 37,642 | 🔄 57% 进行中，ETA ~1天11h |
| **总计** | **2,192,164** | **1,307,682** | 37,651 | — |

- Node A (7B): ok=765,287，8 副本全健康，GPU 利用率 100%
- Node B (235B): ok=261,169，HTTP 200
- 双节点合计速度：~7 vid/s

#### 已合并到 unified manifest
- easycom/noxi/charades 全量 caption 已合并回 `unified_train.jsonl` / `unified_val.jsonl`
- 旧 caption 保留在 `prompt_legacy` 字段
- unified_train: 51,044 行，5 空 prompt (0.01%)

#### 新增脚本
- `scripts/recaption_unified.py`：主 caption 脚本（多端点负载均衡、断点续传、空文件跳过）
- `scripts/merge_recaptioned.py`：合并新 caption 回 unified manifest
- `scripts/generate_dataset_manifest.py`：生成数据集完整 manifest
- `scripts/repair_mira_empty.py`：修复 MIRA 空文件（从 tar 重新提取+转码）
- `scripts/stage2_auto_caption.sh`：阶段二自动衔接（NoXi→Charades→MIRA）
- `gpu_guard_25min.sh`：GPU 占卡 25 分钟自动守护

#### 关键问题与解决
- Node A 235B 部署失败：FlashInfer AllReduce CUDA 错误 + GPU 5/3 崩溃 → 改用 7B
- vLLM MQ 连接问题：`VLLM_HOST_IP=127.0.0.1`
- MIRA 空文件 ~37K（1.8%）：集中在 2026-05-08T21-23 tar 包，脚本已加快速跳过

---

## 0、本轮推进记录（2026-07-22）

### Qwen3-VL-235B-A22B-Instruct-FP8 部署与全量 Caption 完成

详见 `docs/28_Qwen3-VL-235B_Caption完成报告.md`

#### 模型部署
- **Qwen3-VL-235B-A22B-Instruct-FP8** 下载完成：`models/Qwen3-VL-235B-A22B-Instruct-FP8/`（222GB，24 分片）
- **vLLM 部署**：单节点 8× H20-96GB，TP=8 单副本，FP8 + expert-parallel + async-scheduling
- **启动耗时**：~29 分钟（权重 16min + CUDA graph 编译 1min + DeepGEMM warmup 2min + graph 捕获 10min）

#### VLM Caption 生成（8,155 视频）
| 数据集 | 视频数 | 成功 | 失败 | Caption 来源 |
|---|---|---|---|---|
| DexYCB | 2,119 | 2,119 | 0 | qwen3-vl-235b-a22b-fp8 |
| H2O | 60 | 60 | 0 | qwen3-vl-235b-a22b-fp8 |
| OpenVidHD | 1,000 | 1,000 | 0 | qwen3-vl-235b-a22b-fp8 |
| Matrix | 5,000 | 4,976 | 24 | qwen3-vl-235b-a22b-fp8 |

#### 已有 Caption 合并（195,347 条）
| 数据集 | 合并数 | 来源 |
|---|---|---|
| HOIGen-1M | 171,775 | CSV caption_info |
| Charades | 73,603 | 官方标注 manifest.jsonl |
| NoXi | 41,744 | 官方标注 manifest.jsonl |
| Matrix | 14,074 | qwen3-vl-235b（本轮生成） |
| EasyCom | 3,920 | CSV caption |
| DexYCB | 2,400 | manifest_captioned.jsonl |
| H2O | 297 | manifest_captioned.jsonl |

#### Unified Manifest 最终状态
| 指标 | 本轮前 | 本轮后 |
|---|---|---|
| unified_train 行数 | 51,044 | 51,044 |
| 空 prompt | 42,072 (82.5%) | **5 (0.01%)** |
| 已填 prompt | 8,972 (17.5%) | **51,039 (99.99%)** |

分布：hoigen1m 35.2% / charades 17.6% / mira 17.6% / noxi 9.1% / matrix 8.8% / easycom 6.9% / dexycb 4.3% / h2o 0.5%

### 新增脚本
- `scripts/generate_openvidhd_manifest.py`：从文件名解析 OpenVidHD 视频，生成 manifest.jsonl
- `scripts/caption_with_vllm.py`：vLLM API 调用 caption，支持 4 数据集 + 断点续传 + PyAV 帧采样
- `scripts/merge_captions_to_wan22.py`：合并各类 caption 源到 wan22 manifest

### 修改脚本
- `deploy_qwen3vl.sh`：TP=4×2 副本 → TP=8×1 副本 + FP8 优化 flags
- `scripts/build_unified_manifest.py`：SOURCE_CONFIGS 已含 dexycb/h2o/matrix

### 环境实况（覆盖旧文档）
- vLLM 0.21.0+cu129 **已安装**（旧文档说"未安装"已过时）
- transformers 5.10.1 + torch 2.11.0
- ffmpeg/ffprobe **不在 PATH 中**，用 PyAV（`av` 13.1.0）替代
- Squid proxy `http://star-proxy.oa.com:3128` 需 `NO_PROXY=localhost` 绕过

---

## 一、Wan2.2 训练数据总览（2026-07-22 更新）

### Caption 状态总览

| 数据集 | 视频数 | Caption 来源 | 状态 |
|---|---|---|---|
| HOIGen-1M | 231,084 | CSV caption_info | ✅ 已合并 |
| MIRA | 1,918,956 | JSONL→LLM 模板 | ✅ 已修复 |
| Charades | 73,603 | 官方标注 | ✅ 已合并 |
| NoXi | 41,744 | 官方标注 | ✅ 已合并 |
| Matrix | 14,124 | qwen3-vl-235b | ✅ 已生成 |
| EasyCom | 3,920 | 官方标注 CSV | ✅ 已合并 |
| DexYCB | 2,400 | qwen3-vl-235b | ✅ 已生成 |
| OpenVidHD | 1,000 | qwen3-vl-235b | ✅ 已生成 |
| H2O | 297 | qwen3-vl-235b | ✅ 已生成 |

### 已转换为 720p/24fps MP4

| 数据集 | 视频数 | 大小 | Caption | 用途 |
|--------|--------|------|---------|------|
| **MIRA processed** | 2,041,279 | 5.4TB | JSONL→LLM (caption修复完成) | 游戏多视角交互 |
| Charades | 9,848 | 32GB | 官方标注→自然语言caption (已完成) | 日常居家活动 |
| EasyCom | 271 | 2.3GB | 对话文本(已有) | AR多人对话 |
| RAVDESS | 2,880 | 1GB | 低优先级 | 情感表达(已排除) |
| OpenVidHD | 1,000 | 1.1GB | →VLM (已完成 qwen3-vl-235b) | 通用高清视频 |
| DexYCB | 2,400 | ~? | →VLM (已完成 qwen3-vl-235b) | 手物抓取 |
| EPIC | 3 | 295MB | 暂缓 | 厨房HOI |

### 原始数据

| 数据集 | 大小 | 格式 | 说明 |
|--------|------|------|------|
| MIRA Rocket Science | 8.3TB | 4,797 tars, 2.1M MP4 | 游戏多视角，持续处理中 |
| OpenVidHD | 3.0TB | 14 zips, 300K+ MP4 | 通用高清视频 |
| H2O | 177GB | tar.gz, 183K img | 双手操作图片序列 (60/61序列已转MP4, 397MB) |
| DexYCB | 71GB | 3 subjects, 348K img | 手物抓取图片序列 (已转MP4: 2,400视频, 1280x704, 24fps) |
| EasyCom | 102GB | 3,421 files | AR对话(已提取) |
| EPIC-KITCHENS | 8.7GB | 28 MP4 | 厨房HOI |
| Charades | 31GB | 9,848 MP4 | 日常活动 |

### 新下载数据

| 数据集 | 大小 | 状态 | Caption | 类型 |
|--------|------|------|---------|------|
| **HOIGen-1M** | 234GB | 106,100视频已提取 | CSV自带 | 人-物交互 |
| **Seamless Interaction** | ~? | 476视频已提取 | 待检查 | 人人交互 |
| **Matrix Dataset** | ~890GB | 碎片整理完成, ~213GB释放 | qwen3-vl-235b (已完成) | 游戏场景(Forza+Cyberpunk) |
| Action100M (yt-dlp) | 278 videos | cookies过期 | 动作标签 | 人类动作 |
| CelebV-HQ (yt-dlp) | 76 videos | cookies过期 | 属性标注 | 数字人脸 |

---

## 二、下载管线状态

| 管线 | 状态 | 进度 |
|------|------|------|
| MIRA → Wan2.2 | 活跃 | 1,918,956 视频 |
| Matrix git clone | 完成 (碎片整理+去重) | ~890GB, 释放~213GB |
| yt-dlp Action100M | BLOCKED (cookies过期) | 278/60,000 |
| yt-dlp CelebV-HQ | BLOCKED (cookies过期) | 76/13,844 |
| OpenVidHD 补全 | 完成 | 33分片 (829.6GB) 从HF下载 |
| HoloAssist 修复 | 进行中 (wget --continue) | 3个tar修复, 889GB, ETA ~5天 |
| NoXi 下载 | 完成 (per-session zips, 4并行workers) | 已下载 |
| Ego-Exo4D 下载 | 进行中 | ~11TB |
| Assembly101 | BLOCKED | 需HuggingFace token |
| Nymeria | BLOCKED | Facebook CDN 403 |
| Inter-X | BLOCKED | 需Google Drive URLs (skeletons.zip, texts.zip) |
| Wan2.2 模型 | 完成 | 从ModelScope下载 (34GB) |
| Qwen3-VL-235B-FP8 | 完成 | 从ModelScope下载 (222GB) |
| HOI4D bypy | 已停 | 3.3GB |
| VFHQ bypy | 不可用 | 需百度客户端 |
| HOT3D/Aria | 不可用 | Facebook CDN 不可达 |

---

## 三、Caption 方案（2026-07-22 更新）

### VLM 部署

| 项 | 值 |
|---|---|
| 模型 | Qwen3-VL-235B-A22B-Instruct-FP8 |
| 部署 | vLLM 0.21.0+cu129, TP=8 单副本 |
| 硬件 | 8× H20-96GB |
| 量化 | FP8 (282GB) |
| 吞吐 | ~1-6 vid/s（取决于视频长度） |

### 已完成 Caption

| 数据集 | 视频数 | Caption 方式 | 状态 |
|--------|--------|-------------|------|
| HOIGen-1M | 231,084 | CSV 自带 | 已就绪 |
| MIRA | 1.9M | JSONL→LLM 模板 | 已修复 |
| Charades | 73,603 | 官方标注 | 已合并 |
| NoXi | 41,744 | 官方标注 | 已合并 |
| Matrix | 14,124 | qwen3-vl-235b-fp8 | 已完成 |
| EasyCom | 3,920 | 官方标注 CSV | 已合并 |
| DexYCB | 2,400 | qwen3-vl-235b-fp8 | 已完成 |
| OpenVidHD | 1,000 | qwen3-vl-235b-fp8 | 已完成 |
| H2O | 297 | qwen3-vl-235b-fp8 | 已完成 |

---

## 四、Wan2.2 训练基础设施

| 项目 | 状态 | 详情 |
|------|------|------|
| DiffSynth-Studio | 已部署 | 训练框架就绪 |
| 训练配置 | 已创建 | Wan2.2-TI2V-5B, LoRA rank 32 |
| Smoke test | 就绪 | 5,476 samples |
| Wan2.2 模型权重 | 完成 | 从ModelScope下载 (34GB) |
| Qwen3-VL-235B-FP8 | 完成 | 从ModelScope下载 (222GB) |
| Unified manifest | 就绪 | 51,044 train + 5,573 val, 99.99% 有 caption |
| 训练文档 | 已创建 | docs/25_Wan22_Training_Infra.md |

---

## 五、数据集全列表 (90个)

### 已下载 (14个)
MIRA, OpenVidHD, Charades (caption已完成), EasyCom, H2O (已转MP4), DexYCB (已转MP4), EPIC-KITCHENS, RAVDESS, CREMA-D, InterHuman, HoloAssist (tar修复中), Action100M, CRAMA-D, BEAT2

### 下载中 (5个)
HOIGen-1M (视频提取完成), Seamless Interaction (视频提取完成), Matrix Dataset (碎片整理完成), HoloAssist (tar修复), NoXi (下载完成)

### 下载中 (大型下载)
Ego-Exo4D (11TB)

### 已申请 (8个)
Ego4D, OpenHumanVid, Assembly101 (BLOCKED: HF token), Nymeria (BLOCKED: CDN 403), LRS2, LRS3, MultiMediate, UDIVA

### 额外阻塞项
Inter-X (BLOCKED: 需skeletons.zip/texts.zip URLs), yt-dlp (BLOCKED: 需新YouTube cookies)

### 已排除 (21个)
AMASS, Human3.6M, HumanML3D, Motion-X, AIST++, BEAT, TalkSHOW, Trinity, GRAB, CMU Panoptic, ARCTIC, Something-Something V2, ViCo, AgiBot World, CALVIN, LIBERO, Habitat, AI2-THOR, ALFRED, BEHAVIOR, VirtualHome, TEACh, RoboCasa365, CHiME-6

### 暂缓 (37个)
其余模拟器/机器人/评测/音频数据集
