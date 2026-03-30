"""
Local evaluation script for Nemotron LoRA adapter.
Runs on RTX 3090 (24GB) with 4-bit quantization.
Usage: python local_eval.py --adapter_dir <path_to_adapter>
"""
import argparse
import collections
import json
import re
import time

import pandas as pd
import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

# --- Config ---
DEFAULT_MODEL_DIR = "models/nemotron-3-nano-30b-a3b-bf16"
TRAIN_CSV = "train.csv"
VALID_FRAC = 0.02
SEED = 42
MAX_NEW_TOKENS = 64

SYSTEM_PROMPT = (
    "You are a precise puzzle solver. Given input-output examples showing a hidden rule, "
    "discover the rule and apply it to the new input. "
    "Output only the final answer inside \\boxed{}. Do not explain your reasoning."
)


# --- Puzzle type classifier ---
def classify_puzzle(prompt):
    p = prompt.lower()
    if re.search(r'numeral system|base[- ]?\d|number.*convert|radix|secret number', p):
        return 'Number Base Conversion'
    elif re.search(r'gravit|gravity|falling|free.?fall|acceleration due to', p):
        return 'Gravitational Constant'
    elif re.search(r'transformation rule|equation.*transform|secret.*rule.*equation|rule.*applied.*equation', p):
        return 'Equation Transformation'
    elif re.search(r'encrypt|cipher|secret.*code.*letter|coded.*message|secret.*text', p):
        return 'Text Encryption'
    elif re.search(r'bit.?manipul|binary|8.?bit|bitwise|bit.*transform', p):
        return 'Bit Manipulation'
    elif re.search(r'unit.?conver|measurement|becomes.*\d|secret.*conver.*measur', p):
        return 'Unit Conversion'
    return 'Unknown'


# --- Answer extraction ---
def extract_boxed(text):
    matches = re.findall(r'\\boxed\{([^}]*)\}', text)
    for match in reversed(matches):
        candidate = match.strip()
        if candidate:
            return candidate
    # Fallback: first non-empty line
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines[0] if lines else text.strip()


def build_prompt(tokenizer, user_prompt):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    if getattr(tokenizer, "chat_template", None):
        return tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
    # Fallback
    return f"<|im_start|>system\n{SYSTEM_PROMPT}<|im_end|>\n<|im_start|>user\n{user_prompt}<|im_end|>\n<|im_start|>assistant\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter_dir", required=True, help="Path to LoRA adapter directory")
    parser.add_argument("--model_dir", default=DEFAULT_MODEL_DIR, help="Path to base model")
    parser.add_argument("--max_samples", type=int, default=None, help="Limit valid samples for quick test")
    parser.add_argument("--max_new_tokens", type=int, default=MAX_NEW_TOKENS)
    args = parser.parse_args()

    # --- Prepare validation set (ID-based split, no leakage) ---
    print("Loading data...")
    df = pd.read_csv(TRAIN_CSV)
    df['puzzle_type'] = df['prompt'].apply(classify_puzzle)

    valid_size = max(1, int(round(len(df) * VALID_FRAC)))
    valid_df = df.sample(n=valid_size, random_state=SEED)
    train_ids = set(df.drop(valid_df.index)['id'].tolist())
    valid_ids = set(valid_df['id'].tolist())
    assert len(train_ids & valid_ids) == 0, "ID leakage!"

    if args.max_samples:
        valid_df = valid_df.head(args.max_samples)

    print(f"Valid set: {len(valid_df)} samples")
    print(valid_df['puzzle_type'].value_counts().to_string())

    # --- Load model (4-bit) ---
    print(f"\nLoading base model from {args.model_dir} (4-bit)...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(args.model_dir, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        args.model_dir,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
        low_cpu_mem_usage=True,
    )

    # --- Load LoRA adapter ---
    print(f"Loading LoRA adapter from {args.adapter_dir}...")
    model = PeftModel.from_pretrained(model, args.adapter_dir)
    model.eval()

    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Model loaded: {total_params/1e9:.1f}B params, {trainable_params/1e6:.1f}M trainable")

    # --- Inference + evaluation ---
    print(f"\n{'='*60}")
    print(f"Running evaluation on {len(valid_df)} samples...")
    print(f"{'='*60}\n")

    results = []
    start_time = time.time()

    for idx, (_, row) in enumerate(valid_df.iterrows()):
        prompt_text = build_prompt(tokenizer, row['prompt'])
        inputs = tokenizer(prompt_text, return_tensors="pt", add_special_tokens=False).to(model.device)

        with torch.no_grad():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=args.max_new_tokens,
                do_sample=False,
                use_cache=True,
                pad_token_id=tokenizer.pad_token_id,
            )

        new_tokens = output_ids[0][inputs["input_ids"].shape[1]:]
        raw = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()

        # Truncate after \boxed{...}
        boxed_start = raw.find("\\boxed{")
        if boxed_start >= 0:
            depth = 0
            for i in range(boxed_start + len("\\boxed{"), len(raw)):
                if raw[i] == '{':
                    depth += 1
                elif raw[i] == '}':
                    if depth == 0:
                        raw = raw[:i + 1]
                        break
                    depth -= 1

        extracted = extract_boxed(raw)
        target = str(row['answer']).strip()
        exact_match = (extracted == target)

        results.append({
            "puzzle_type": row['puzzle_type'],
            "exact_match": exact_match,
            "has_boxed": "\\boxed{" in raw,
            "extracted": extracted,
            "target": target,
            "raw": raw,
        })

        status = "OK" if exact_match else "MISS"
        elapsed = time.time() - start_time
        avg_time = elapsed / (idx + 1)
        remaining = avg_time * (len(valid_df) - idx - 1)
        print(f"[{idx+1}/{len(valid_df)}] {status} [{row['puzzle_type'][:15]:>15s}] "
              f"target=\"{target[:30]}\" got=\"{extracted[:30]}\" "
              f"({avg_time:.1f}s/sample, ~{remaining:.0f}s left)")

    # --- Summary ---
    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"EVALUATION COMPLETE ({elapsed:.0f}s)")
    print(f"{'='*60}")

    type_stats = collections.defaultdict(lambda: {"total": 0, "correct": 0, "boxed": 0})
    for r in results:
        pt = r["puzzle_type"]
        type_stats[pt]["total"] += 1
        type_stats[pt]["correct"] += int(r["exact_match"])
        type_stats[pt]["boxed"] += int(r["has_boxed"])

    total_correct = sum(r["exact_match"] for r in results)
    total_boxed = sum(r["has_boxed"] for r in results)
    total = len(results)

    print(f"\nOverall: {total_correct}/{total} correct ({100*total_correct/total:.1f}%), "
          f"{total_boxed}/{total} boxed ({100*total_boxed/total:.1f}%)")

    print(f"\n{'Type':<30s} {'Correct':>10s} {'Boxed':>10s}")
    print("-" * 55)
    for pt in sorted(type_stats.keys()):
        s = type_stats[pt]
        acc = 100 * s["correct"] / s["total"] if s["total"] > 0 else 0
        brate = 100 * s["boxed"] / s["total"] if s["total"] > 0 else 0
        print(f"{pt:<30s} {s['correct']:>3d}/{s['total']:<3d} ({acc:5.1f}%) "
              f"{s['boxed']:>3d}/{s['total']:<3d} ({brate:5.1f}%)")

    # Show errors
    wrong = [r for r in results if not r["exact_match"]]
    if wrong:
        print(f"\n--- Sample errors (up to 5) ---")
        for r in wrong[:5]:
            print(f"  [{r['puzzle_type']}]")
            print(f"    expected: \"{r['target']}\"")
            print(f"    got:      \"{r['extracted'][:80]}\"")
            print(f"    raw:      \"{r['raw'][:100]}\"")
            print()

    # Save results
    output_path = "eval_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Results saved to {output_path}")


if __name__ == "__main__":
    main()
