# Nemotron Competition Project

## Project
NVIDIA Nemotron Model Reasoning Challenge (Kaggle).
Submit a **LoRA adapter** (r<=32) for **Nemotron-3-Nano-30B** (32B params, MoE with 3B active).
The host loads the adapter onto the base model and runs their benchmark. Direct answer submission is NOT the format.

## Competition Task
Few-shot reasoning puzzles: given N input->output examples, infer the hidden rule and apply it to a new input.

### Puzzle Types (6 types, by zero-shot difficulty)
- **Hard**: Bit Manipulation, Text Encryption, Equation Transformation
- **Medium**: Gravitational Constant, Unit Conversion
- **Easy**: Number Base Conversion

## Key Commands
```bash
# Push to Kaggle (PRO6000 GPU)
python push_kernel.py

# Push with different accelerator
python push_kernel.py --accelerator T4x2
```
Do NOT use Kaggle Python API for push - it ignores accelerator. Always use CLI via push_kernel.py.

## Notebook Structure (nvidia-competition/train_lora.ipynb)
| Cell | Section | Role |
|------|---------|------|
| 0 | Title | Markdown header |
| 1 | Deps | Install wheels, fix sys.path shadows (tilelang, array_api_compat) |
| 2 | Config | All hyperparams, FAST_ITER toggle, puzzle type definitions |
| 3 | Data | Load CSV, classify puzzle types, oversample hard/medium, build SFT records |
| 4 | Tokenizer | Load tokenizer, chat template, prompt formatting |
| 5 | Datasets | Tokenize train/valid datasets |
| 6 | Model+LoRA | Load base model (bf16 on PRO6000, 4-bit on 3090), attach LoRA, torch.compile |
| 7 | Train | HuggingFace Trainer with HeartbeatCallback -> train_log.csv |
| 8 | Save+Eval | Save adapter, create submission.zip, run per-type eval -> eval_results.json |
| 9 | Submission | Create submission.zip (redundant safety net) |

## Workflow
- **Day (quick iteration)**: `FAST_ITER=True` (default=True) -> 500 samples, 1 epoch, ~30min total with eval
- **Night (full training)**: Set `FAST_ITER=False` before push -> all samples, 2 epochs, ~7-8h
- To switch: edit Cell 2 `FAST_ITER = _env_flag("FAST_ITER", True/False)`

## Output Files (on Kaggle /kaggle/working)
- `train_log.csv` - per-step loss/lr logging
- `eval_results.json` - overall accuracy + per-type breakdown + per-sample details
- `submission.zip` - LoRA adapter for submission

## Known Constraints
- **LORA_R <= 32** (competition rule)
- **Kaggle 12h time limit** per kernel run
- **PRO6000 Blackwell** (102GB VRAM, sm_120) - bf16 full precision, no quantization needed
- **Local RTX 3090** (24GB VRAM) - too small for inference, use for code/data work only
- Mamba/causal-conv1d CUDA extensions need Blackwell-compatible wheels
- Output format: `\boxed{answer}` only (no "Rule:" prefix)
- Oversampling: hard 3x, medium 2x, easy 1x

## Data
- `train.csv`: ~9,500 samples (after 5% valid split -> ~9,025 train + ~475 valid)
- `test.csv`: 34 samples (tiny - not useful for local eval)
- After oversampling: ~21,000 training rows

## File Layout
```
nemotron_comp/
  CLAUDE.md              # This file
  push_kernel.py         # Kaggle kernel push script
  train.csv / test.csv   # Competition data (local copies)
  nvidia-competition/    # Kaggle kernel folder
    train_lora.ipynb     # Main training notebook
    kernel-metadata.json # Kaggle kernel config
  adapters/              # Saved adapter versions
  local_eval.py          # Local eval script (outdated, not used)
```
