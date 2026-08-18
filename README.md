# Full-Duplex Multimodal Interactive World Model

本项目旨在构建一个以人为中心的全双工多模态交互世界模型，面向游戏、虚拟场景、数字人及简单具身交互环境，实现人与 NPC、人物、物体和环境之间的连续交互。

系统采用“大脑 + 渲染器”的分层架构：由视觉语言模型或多模态大模型负责理解视频、音频、文本和动作输入，识别用户意图，维护人物、物体与场景状态，并生成结构化交互计划；由视频 Diffusion/DiT 模型根据文本、参考图像、历史视频、动作条件和记忆信息生成相应的视频反馈。

项目计划首先基于 5B 级视频生成模型完成快速验证，训练高质量双向非流式 Teacher，并进一步蒸馏为因果、自回归或流式 Student，最终支持持续生成、在线条件更新、用户打断和长期状态保持。

当前阶段重点围绕高质量人类中心交互数据构建、VLM 驱动的状态与意图建模、动作结果一致性、流式视频生成和长期记忆展开，目标是在可控的研究周期内完成一个可运行的交互式 Demo，并形成具有论文价值的技术方案与实验结果。

## 下一阶段训练入口

截至 2026-08-18，14 个数据集已完成转码/切分，但全量 caption 覆盖率约为 44%。下一步采用“冻结可用高质量子集 -> 256 条 smoke -> 约 4 万条 landscape pilot -> 对照实验 -> 有门槛扩量”的顺序，详见 [下一阶段训练实验计划](docs/30_下一阶段训练实验计划.md)；数据硬过滤、caption 复核、任务均衡、质量评分与采样权重见 [训练数据筛选与均衡方案](docs/31_训练数据筛选与均衡方案.md)。

```bash
export WM_DATA_ROOT=/path/to/wm_dataset
python scripts/build_unified_manifest.py \
  --config training_metadata/experiment_sources.example.json \
  --phase smoke --check-files

python scripts/audit_experiment_manifest.py \
  --train training_metadata/generated/unified_smoke_train.jsonl \
  --val training_metadata/generated/unified_smoke_val.jsonl \
  --base-path "$WM_DATA_ROOT" --check-files

export DIFFSYNTH_ROOT=/path/to/DiffSynth-Studio
bash scripts/smoke_test_wan22.sh
```

`scripts/train_wan22.sh` 默认锁定已核验的 DiffSynth-Studio 提交，使用官方 Wan2.2-TI2V-5B LoRA 模块、49 帧和首帧 `input_image` 条件。W&B 默认关闭，TensorBoard 默认开启。
