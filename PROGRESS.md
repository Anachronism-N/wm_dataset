# 数据进展追踪 — 全数据集状态

> 最后更新：2026-07-12 23:15
> 目标：面向 Wan2.2 以人为中心的视频生成训练

---

## 一、概览

| 维度 | 状态 |
|------|------|
| Excel 编目数据集 | 90 个 |
| 调研新增 | 12 个（OpenHumanVid, EgoVid-5M 等） |
| 已下载 | **14 个**（有实际数据） |
| Wan2.2 就绪 | 12,999 视频（Charades 9,848 + RAVDESS 2,880 + EasyCom 271） |
| 不适合/已排除 | 21 个 |
| 待申请/下载中 | 10+ 个 |
| 总数据量 | ~11TB |
| 存储路径 | `/apdcephfs_gy2/share_302533218/cedricnie/wm_dataset/dataset/` |

---

## 二、90 数据集完整状态

### ✅ 已下载（14 个）

| 数据集 | 大小 | 格式 | 视频数 | 用途 | Wan2.2 |
|--------|------|------|--------|------|--------|
| **MIRA Rocket Science** | ~2.6TB | 328 tar, ~162K MP4 | ~162K | 游戏多视角 | 待处理 |
| **OpenVid-1M (OpenVidHD)** | 2.0TB | 14 zips, ~300K MP4 | ~300K+ | 通用高清视频 | 待处理 |
| **Charades** | 31GB | 9,848 MP4 | 9,848 | 日常活动 | 就绪 720p |
| **RAVDESS** | 26GB | 2,880 MP4 | 2,880 | 情感表达 | 就绪 720p |
| **EasyCom** | 66GB | 323 MP4 | 323 | AR 对话 | 就绪 720p |
| **H2O** | 177GB | 183K 图片(tar.gz) | ~183K img | 双手操作 | 图片→视频 |
| **DexYCB** | 71GB | 348K 图片 | 348K img | 手物抓取 | 图片→视频 |
| **EPIC-KITCHENS-100** | 8.6GB | 28 MP4 | 28 | 厨房 HOI | 场景单一 |
| **CREMA-D** | 7GB | 7,442 WAV | 0 | 情感音频 | 非视频 |
| **Action100M** | 37GB | Parquet | 0 | 动作元数据 | 非视频 |
| **BEAT2** | — | 待下载 | — | 动作捕捉 | 非视频 |
| **EgoExoLearn** | — | 待检查 | — | 技能学习 | 待检查 |
| **InterHuman** | 78MB | 代码 | 0 | 代码仓库 | 非视频 |
| **HoloAssist** | 25MB | repo | 0 | AR 协作 | 待下载数据 |

### ⏳ 下载中 / 待下载（10 个）

| 数据集 | 状态 | 备注 |
|--------|------|------|
| **VFHQ** | ⏳ bypy syncdown | 15K 文件夹，Python 脚本后台运行 |
| **HOI4D** | ⏳ bypy syncdown | RGB 视频分片兼容问题 |
| **Inter-X** | ⏳ gdown 限流 | 31GB，Google Drive |
| **Nymeria** | ❌ URL 过期 | Facebook CDN，1,100 视频 983GB |
| **ViCo** | ❌ 图像数据集 | 按 GitHub 说明为图片序列，已排除 |
| **LRS2** | ⏳ 需注册 | 牛津大学下载页面 |
| **CelebV-HQ** | ⏳ YouTube 脚本 | 类似 Action100M，需 yt-dlp |
| **HD-EPIC** | ⏳ 已排除 | 场景单一 |
| **Aria ADT/AEA** | ❌ URL 过期 | Facebook CDN |
| **HOT3D** | ❌ URL 过期 | Facebook CDN |

### 📨 已申请（等待回复）

| 数据集 | 优先级 | 状态 |
|--------|--------|------|
| **Ego4D** | P0 | 已申请 |
| **OpenHumanVid** | P0 | 已申请 |
| **Assembly101 (Google Drive)** | P0 | 已申请 |
| **Ego-Exo4D** | P0 | 已申请 |
| **NoXi** | P1 | 已申请 |
| **MultiMediate** | P1 | 已申请 |

### ❌ 已排除 — 不适合视频生成（21 个）

| 数据集 | 原因 |
|--------|------|
| AMASS | 纯 3D 动作库 |
| Human3.6M | 3D 关节姿态 |
| HumanML3D | 3D 动作向量 |
| Motion-X | 3D 运动向量 |
| AIST++ | SMPL 3D 参数 |
| BEAT/BEAT2 | MoCap 动作捕捉 |
| TalkSHOW | MoCap |
| Trinity Speech-Gesture | MoCap |
| GRAB | MoCap |
| CMU Panoptic | 3D 动捕 |
| ARCTIC | 仅手部，无环境 |
| Something-Something V2 | 画质过低 |
| ViCo | 图像数据集（非视频） |
| AgiBot World | 机器人关节向量 |
| CALVIN/LIBERO | 机器人模拟器 |
| Habitat | 导航模拟器 |
| AI2-THOR/ALFRED | 室内模拟器 |
| BEHAVIOR/OmniGibson | 物理模拟器 |
| VirtualHome/TEACh | 程序化模拟 |
| RoboCasa365 | 合成数据 |
| CHiME-6 | 仅音频 |

> 已清理：AgiBot(165GB) + Assembly101(490GB) = 655GB 释放

### 🔜 暂缓（55 个）

以下数据集因优先级较低、获取困难或与当前目标不完全匹配，暂未启动下载：

| 类别 | 数据集 | 数量 |
|------|--------|------|
| 大规模视频 URL | Panda-70M, HD-VILA-100M, InternVid, MiraData, WebVid-10M, OpenVid-1M | 6 |
| 人脸/说话人 | CelebV-HQ, CelebV-Text, TalkingHead-1KH, HDTF, VoxCeleb1/2, VoxBlink2, MEAD | 7 |
| 唇读/音视频 | LRS2, LRS3, AVSpeech | 3 |
| 对话/情感 | AMI, NoXi, CREMA-D, RAVDESS(已有), MultiMediate, UDIVA, F2F-JF, M3ED | 8 |
| 具身/机器人 | DROID, RH20T, BridgeData V2, Open X-Embodiment, MineRL, BEDD | 6 |
| 模拟器 | AI2-THOR, ALFRED, Habitat, CALVIN, BEHAVIOR, VirtualHome, TEACh, RoboCasa365, MineDojo, LIBERO | 10 |
| 游戏/合成 | PLAICraft, Matrix-Game 2.0, VPT数据 | 3 |
| 评测/基准 | OmniMMI, EgoSchema, Full-Duplex-Bench-v2, MBench, MIND, iWorld-Bench, NarraStream-Bench, VideoFDB | 8 |
| 其他 | EgoCom, Kinetics-700, AVA, SpeakerVid-5M, ResponseNet, TED Gesture, MM-Conv, H2O Handover, DexYCB(已有) | 9 |

---

## 三、Wan2.2 训练数据就绪度

| 数据集 | 视频数 | 格式 | 状态 |
|--------|--------|------|------|
| Charades | 9,848 | 720p/24fps MP4 | 可用 |
| RAVDESS | 2,880 | 720p/24fps MP4 | 可用 |
| EasyCom | 271 | 720p/24fps MP4 | 可用 |
| **小计** | **12,999** | | |
| MIRA | ~162K | 1280×720/20fps MP4 | 待解包转码 |
| OpenVidHD | ~300K+ | zip 中 MP4 | 待解压转码 |
| DexYCB | 348K img | 图片序列 | 方案已记录 |
| H2O | 183K img | 图片序列 | 待转换 |

---

## 四、大型通用视频数据策略

目前已下载 **OpenVidHD (2.0TB, ~300K+ 视频)** 作为通用高质量视频训练数据源。OpenVid-1M 还有更多 part 可在空间允许时继续下载。

其他大型通用视频数据集（Panda-70M, HD-VILA-100M, InternVid 等）主要提供 YouTube URL 元数据而非直接视频文件，需 yt-dlp 逐个下载，效率较低。

---

## 五、更新日志

| 日期 | 更新内容 |
|------|---------|
| 07-11 | 创建 docs, 下载 CRAMA-D, RAVDESS, Charades, EasyCom, EPIC, HoloAssist |
| 07-11 | MIRA(660GB), Assembly101(490GB), AgiBot(165GB) 下载 |
| 07-12 | 大规模下载：OpenVidHD, DexYCB, H2O, HOT3D/Aria URL |
| 07-12 | Wan2.2 转换：Charades 9,848, RAVDESS 2,880, EasyCom 271 |
| 07-12 | 清理 AgiBot(165GB), Assembly101(490GB)，排除 21 个不适合数据集 |
| 07-12 | VFHQ bypy 下载启动, Inter-X gdown 尝试, HoloAssist 直链下载 |
| 07-12 23:15 | **全 90 数据集状态文档完成** |
