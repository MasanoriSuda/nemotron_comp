# 弱点分析・仮説・実験計画

## 現状スコア
- **Best: v76 = 0.65** (フル学習, 9000件×2epoch, loss=0.694)
- **v81 quick**: loss=0.45（CoT データ追加、1 epoch）→ **LB=0.58**（悪化、leakage=100%）
- **v82 full**: loss=0.03（CoT + 全件2epoch）→ **LB=0.60**（悪化、過学習）
- nemotron-sft-baseline LB = 0.66 (参考)
- 理論上限（ルールベース完全習得）: ~0.85+

---

## タイプ別構造分析（EDA より）

| タイプ | 件数 | 理論上限 | 解法構造 | 我々の現状 |
|--------|------|---------|----------|-----------|
| Number Base (Roman) | 1,576 | **100%** | 決定論的（ローマ数字） | 高め |
| Gravitational Constant | 1,597 | **99.4%** | 決定論的（g = 2d/t²） | ~0% ← 最優先 |
| Unit Conversion | 1,594 | **99.4%** | 決定論的（ratio抽出） | 不明 ← 要確認 |
| Text Encryption | 1,576 | ~38% | 部分的（文字対応表） | 0% |
| Bit Manipulation | 1,602 | 50-80% | LLM推論が必要 | ~0% |
| Equation Transformation | 1,555 | 50-70% | LLM推論が必要 | ~0% |

**重要**: Gravity と Unit Conversion は「能力問題」ではなく「計算手順の問題」。
この2タイプだけで全問題の **33%** を占める。ここを解決すれば大幅スコアアップが見込める。

---

## タイプ別弱点と根本原因仮説

### Gravitational Constant（~0% 我々、理論上限 99.4%）← 最優先

**解法**: 例から g を抽出 → d = 0.5 × g × t² で計算

| 仮説 | 優先度 | 検証方法 |
|------|--------|----------|
| H1: 公式で計算せず「推定」している（"probably", "approximately" 等を出力） | ★★★ | raw 出力を確認 |
| H2: CoT で明示的な計算手順を学習させれば 90%+ 達成可能 | ★★★ | CoT 付き合成データで検証 |

**CoT テンプレート**:
```
g = 2 × 14.92 / 1.37² = 15.92
g = 2 × 144.96 / 4.27² = 15.90
...
g_mean = 15.91
d = 0.5 × 15.91 × 4.41² = 154.62
\boxed{154.62}
```

### Unit Conversion（不明、理論上限 99.4%）← 優先度高

**解法**: 例から ratio = output/input を抽出 → target × ratio

| 仮説 | 優先度 | 検証方法 |
|------|--------|----------|
| H1: 比率を抽出・計算せず「推定」している | ★★★ | raw 出力を確認 |
| H2: CoT で ratio 計算を明示すれば 90%+ 達成可能 | ★★★ | CoT 付き合成データで検証 |

**CoT テンプレート**:
```
ratio = 6.69 / 10.08 = 0.6637
ratio = 11.83 / 17.83 = 0.6635
...
ratio_mean = 0.6636
answer = 25.09 × 0.6636 = 16.65
\boxed{16.65}
```

### Bit Manipulation（~0% 我々、30% 他者、理論上限 50-80%）

| 仮説 | 優先度 | 検証方法 |
|------|--------|----------|
| H1: 出力が10進数になっている（採点ロジック変更で厳密一致必要） | ★★★ | eval の raw 出力を見る |
| H2: ビット演算ルールを例から推論できない（能力問題） | ★★ | CoT 付きデータで改善するか |
| H3: lucian kucera のデータセット（公開予定）で改善できる | ★★ | データセット公開後に追加 |

### Text Encryption（0% 全員、理論上限 ~38%）← 後回し

| 仮説 | 優先度 | 検証方法 |
|------|--------|----------|
| H1: 文字対応表を例から再現できない（部分的に構造的限界） | ★★ | CoT でどこまで改善するか |
| H2: ルールベースで 38% は取れるが残りは本質的に難しい | ★ | - |

### Equation Transformation（~0% 我々、6% 他者）← 後回し

| 仮説 | 優先度 | 検証方法 |
|------|--------|----------|
| H1: データ品質問題（一意に決まらない問題あり） | ★★ | 問題を手動確認 |
| H2: 記号変換ルールが複雑すぎる | ★ | - |

### Number Base Conversion（高め、ただし不安定）

| 仮説 | 優先度 | 検証方法 |
|------|--------|----------|
| H1: 他タイプの学習が強すぎて崩れている | ★★ | 均衡学習で改善するか |

---

## 切り分け順（GPU 回復後の実験キュー）

各ステップは quick run（~1h）。前のステップの結果を受けて次を判断する。

| Step | 実験 | 変更点 | 判定基準 |
|------|------|--------|---------|
| S1 | v83 | eval generation prompt に `enable_thinking=False` を明示（train 側は変わらない） | eval leakage が下がるか確認。train 本命修正は S2 |
| S2 | v84 | CoT を `reasoning_content` に移動、`content` は `\boxed{}` のみ | Gravity/Unit accuracy が上がるか |
| S3 | v85 | **Blackwell 上で** S2 の adapter を使い fast_path ON/OFF × use_cache ON/OFF を 2×2 eval | Mamba 実行経路の差異を確認（ローカル 3090 では不可） |
| S4 | v86 | S2 + `torch.compile=OFF` | compile が悪影響か確認 |
| S5 | v87 | S2 + LoRA target: `in_proj\|out_proj` のみ | MoE 除外の効果 |
| S6 | v88 | S5 + `q_proj\|o_proj` 追加 | Attention 追加の効果 |

`q_proj|v_proj` は S6 の後に検討。

## 最有力仮説（S3/S4 完了前は未確定）

**thinking チャネル不整合（v81/v82 悪化の最有力仮説）**

chat_template の挙動：
- `reasoning_content` なし → `<think></think>{content}`
- `reasoning_content` あり → `<think>{reasoning}</think>{content}`

現在の `to_record()` は CoT を `content` に直書き：
```
学習済みフォーマット: <think></think>g = 2×d/t²...\boxed{154.62}  ← CoT が think の外
正しいフォーマット:   <think>\ng = 2×d/t²...\n</think>\n\boxed{154.62}
```

**修正コード（S2 で適用）**：
```python
{"role": "assistant", "reasoning_content": "g = 2×d/t²...", "content": "\\boxed{154.62}"}
```

**その他の仮説（未切り分け）**

- train `use_cache=False` / eval `use_cache=True` → Mamba 実行経路が不一致（S3 で切り分け）
- `enable_thinking` 未指定 → eval generation prompt 側は S1 で修正、train 側の本命修正は S2
- LoRA trainable 880M（うち 862M が MoE エキスパート）→ v76 も同じなので直接原因ではないが最適ではない（S5/S6 で比較）
- MAX_SEQ_LEN=1024: CoT 付きでも最大 412 token → **問題なし**

## GPU 時間制約

- 週 30h / quick run ~1h → 週 ~25 本（バッファ込み）
- medium run（1 epoch 全件）= ~5h → S2 が良ければ medium run で LB 確認
- フル学習（2 epoch 全件）= 12h 超 → **Kaggle タイムアウト、使用不可**

## スコア試算

| 状態 | Gravity | Unit | Bit | 他 | 予想スコア |
|------|---------|------|-----|-----|----------|
| v76（現 best） | 不明 | 不明 | ~0% | 中程度 | 0.65 |
| S2 後（CoT 正常化） | 90%+ | 90%+ | ~0% | 同 | **~0.72+** |
| S6 後（LoRA 最適化） | 90%+ | 90%+ | ~0% | 改善 | **~0.75+** |
