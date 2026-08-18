#!/usr/bin/env bash
set -euo pipefail

# Reproducible Wan2.2-TI2V-5B LoRA launcher for DiffSynth-Studio.
# Usage: DIFFSYNTH_ROOT=/path/to/DiffSynth-Studio WM_DATA_ROOT=/path/to/wm_dataset \
#        bash scripts/train_wan22.sh smoke

MODE="${1:-smoke}"
case "$MODE" in
  smoke|pilot|scale) ;;
  *) echo "mode must be smoke, pilot, or scale" >&2; exit 2 ;;
esac

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
: "${DIFFSYNTH_ROOT:?Set DIFFSYNTH_ROOT to a DiffSynth-Studio checkout}"
: "${WM_DATA_ROOT:?Set WM_DATA_ROOT to the dataset base path used by the manifest builder}"

EXPECTED_DIFFSYNTH_COMMIT="${EXPECTED_DIFFSYNTH_COMMIT:-89ceaa660b936cd065373ee1f33527ed215f64dd}"
if git -C "$DIFFSYNTH_ROOT" rev-parse HEAD >/dev/null 2>&1; then
  ACTUAL_DIFFSYNTH_COMMIT="$(git -C "$DIFFSYNTH_ROOT" rev-parse HEAD)"
  if [[ "$ACTUAL_DIFFSYNTH_COMMIT" != "$EXPECTED_DIFFSYNTH_COMMIT" && "${ALLOW_UNPINNED:-0}" != "1" ]]; then
    echo "DiffSynth-Studio commit mismatch." >&2
    echo "expected: $EXPECTED_DIFFSYNTH_COMMIT" >&2
    echo "actual:   $ACTUAL_DIFFSYNTH_COMMIT" >&2
    echo "Check out the expected commit or set ALLOW_UNPINNED=1 after review." >&2
    exit 2
  fi
fi

TRAIN_SCRIPT="$DIFFSYNTH_ROOT/examples/wanvideo/model_training/train.py"
[[ -f "$TRAIN_SCRIPT" ]] || { echo "training entrypoint not found: $TRAIN_SCRIPT" >&2; exit 2; }

MANIFEST="${MANIFEST:-$PROJECT_ROOT/training_metadata/generated/unified_${MODE}_train.csv}"
[[ -f "$MANIFEST" ]] || { echo "training manifest not found: $MANIFEST" >&2; exit 2; }
IFS=, read -r FIRST_COLUMN SECOND_COLUMN _ < "$MANIFEST"
FIRST_COLUMN="${FIRST_COLUMN#$'\xef\xbb\xbf'}"
[[ "$FIRST_COLUMN" == "video" && "$SECOND_COLUMN" == $'prompt\r' || "$FIRST_COLUMN" == "video" && "$SECOND_COLUMN" == "prompt" ]] || {
  echo "manifest header must be video,prompt: $MANIFEST" >&2
  exit 2
}

NUM_PROCESSES="${NUM_PROCESSES:-8}"
GRADIENT_ACCUMULATION_STEPS="${GRADIENT_ACCUMULATION_STEPS:-1}"
DATASET_NUM_WORKERS="${DATASET_NUM_WORKERS:-4}"
LORA_RANK="${LORA_RANK:-32}"
LEARNING_RATE="${LEARNING_RATE:-1e-4}"
NUM_EPOCHS="${NUM_EPOCHS:-1}"
WAN_MODEL_ID="${WAN_MODEL_ID:-Wan-AI/Wan2.2-TI2V-5B}"
MODEL_PATHS="${WAN_MODEL_ID}:diffusion_pytorch_model*.safetensors,${WAN_MODEL_ID}:models_t5_umt5-xxl-enc-bf16.pth,${WAN_MODEL_ID}:Wan2.2_VAE.pth"
OUTPUT_PATH="${OUTPUT_PATH:-$PROJECT_ROOT/runs/wan22_${MODE}_$(date -u +%Y%m%dT%H%M%SZ)}"

case "$MODE" in
  smoke)
    HEIGHT="${HEIGHT:-480}"
    WIDTH="${WIDTH:-832}"
    SAVE_STEPS="${SAVE_STEPS:-100}"
    ;;
  pilot)
    HEIGHT="${HEIGHT:-704}"
    WIDTH="${WIDTH:-1280}"
    SAVE_STEPS="${SAVE_STEPS:-500}"
    ;;
  scale)
    HEIGHT="${HEIGHT:-704}"
    WIDTH="${WIDTH:-1280}"
    SAVE_STEPS="${SAVE_STEPS:-1000}"
    ;;
esac

if [[ -z "${DATASET_REPEAT:-}" ]]; then
  if [[ "$MODE" == "smoke" ]]; then
    TRAIN_ROWS="$(awk 'END {print NR-1}' "$MANIFEST")"
    TARGET_UPDATES="${TARGET_UPDATES:-200}"
    MICRO_BATCHES=$((TARGET_UPDATES * NUM_PROCESSES * GRADIENT_ACCUMULATION_STEPS))
    DATASET_REPEAT=$(((MICRO_BATCHES + TRAIN_ROWS - 1) / TRAIN_ROWS))
    ((DATASET_REPEAT < 1)) && DATASET_REPEAT=1
  else
    DATASET_REPEAT=1
  fi
fi

mkdir -p "$OUTPUT_PATH"

COMMAND=(
  accelerate launch
  --num_processes "$NUM_PROCESSES"
  --mixed_precision bf16
  "$TRAIN_SCRIPT"
  --dataset_base_path "$WM_DATA_ROOT"
  --dataset_metadata_path "$MANIFEST"
  --data_file_keys video
  --height "$HEIGHT"
  --width "$WIDTH"
  --num_frames 49
  --dataset_repeat "$DATASET_REPEAT"
  --dataset_num_workers "$DATASET_NUM_WORKERS"
  --model_id_with_origin_paths "$MODEL_PATHS"
  --learning_rate "$LEARNING_RATE"
  --num_epochs "$NUM_EPOCHS"
  --save_steps "$SAVE_STEPS"
  --remove_prefix_in_ckpt pipe.dit.
  --output_path "$OUTPUT_PATH"
  --lora_base_model dit
  --lora_target_modules q,k,v,o,ffn.0,ffn.2
  --lora_rank "$LORA_RANK"
  --extra_inputs input_image
  --gradient_accumulation_steps "$GRADIENT_ACCUMULATION_STEPS"
  --use_gradient_checkpointing
)

[[ "${ENABLE_TENSORBOARD:-1}" == "1" ]] && COMMAND+=(--enable_tensorboard_log)
[[ "${ENABLE_WANDB:-0}" == "1" ]] && COMMAND+=(--enable_wandb_log --wandb_project "${WANDB_PROJECT:-wm_dataset_wan22}")
[[ "${GRADIENT_CHECKPOINTING_OFFLOAD:-0}" == "1" ]] && COMMAND+=(--use_gradient_checkpointing_offload)
[[ "${MODEL_CPU_OFFLOAD:-0}" == "1" ]] && COMMAND+=(--enable_model_cpu_offload)
[[ -n "${LORA_CHECKPOINT:-}" ]] && COMMAND+=(--lora_checkpoint "$LORA_CHECKPOINT")

printf 'Launching mode=%s rows=%s repeat=%s processes=%s resolution=%sx%s\n' \
  "$MODE" "$(awk 'END {print NR-1}' "$MANIFEST")" "$DATASET_REPEAT" "$NUM_PROCESSES" "$WIDTH" "$HEIGHT"
printf 'Output: %s\n' "$OUTPUT_PATH"
printf 'Command:'
printf ' %q' "${COMMAND[@]}"
printf '\n'

[[ "${DRY_RUN:-0}" == "1" ]] || "${COMMAND[@]}"
