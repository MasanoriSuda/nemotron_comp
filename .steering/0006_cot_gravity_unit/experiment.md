# 0006 - cot_gravity_unit (v81)

## 仮説
Gravitational Constant と Unit Conversion は決定論的ルールで解けるため、
明示的な計算手順（CoT）を学習データに含めることで 0% → 90%+ に改善できる。
CoT テンプレート:
- Gravity: `g = 2×d/t² → g_mean → d = 0.5×g_mean×t²`
- Unit: `ratio = out/in → ratio_mean → answer = target × ratio_mean`

## 設定

| パラメータ | 変更前(v76) | 変更後(v81) |
|-----------|------------|------------|
| Gravity/Unit 学習フォーマット | `\boxed{answer}` のみ | CoT + `\boxed{answer}` |
| CoT 生成 | なし | _make_gravity_cot / _make_unit_cot |
| FAST_ITER | False | True (3000 samples / 1 epoch) |
| 検証目的 | - | CoT データの学習可能性確認 |

## 結果 (v81 quick run)
- **Kaggle LB Score: 0.58**（v76=0.65 より悪化）
- train_loss: **0.4538**（v79/v80=1.86 から大幅改善 → CoT データは学習できている）
- Overall accuracy: 1.7% (1/60)
- boxed率: 1.7% (1/60)

| タイプ | 正解率 | boxed率 | FmtOK | Leak |
|--------|--------|---------|-------|------|
| Number Base Conversion | 12.5% (1/8) | 12.5% | 0% | 100% |
| Bit Manipulation | 0% (0/9) | 0% | 0% | 100% |
| Equation Transformation | 0% (0/13) | 0% | 0% | 100% |
| Gravitational Constant | 0% (0/10) | 0% | 0% | 100% |
| Text Encryption | 0% (0/11) | 0% | 0% | 100% |
| Unit Conversion | 0% (0/9) | 0% | 0% | 100% |
| **Overall** | **1.7%** | **1.7%** | **0%** | **100%** |

Sample errors:
- [Gravitational Constant] got="1) t=" (CoT を出力し途中で打ち切られている)
- [Number Base Conversion] got="55"（ローマ数字 "LV" が正解）

## 学び
1. **CoT データは学習できる**: loss が 1.86 → 0.45 と劇的に下がった
2. **1 epoch では format が固まらない**: reasoning_leakage=100% で boxed率も 1.7% のみ
3. **Critical tension**: CoT 学習するとモデルが推論を出力する癖がつく
   - SYSTEM_PROMPT「answer only」と矛盾
   - ただし競技 evaluator が独自に `\boxed{}` 指示を付加するため問題ない可能性
   - フル学習（2 epoch）で format が収束すれば loss 低下 + accuracy 向上が期待できる
4. **フル学習での期待値**:
   - v76 (no CoT): loss=0.694 → LB=0.65
   - v81 quick: loss=0.45 → 1 epoch で未収束
   - フル学習なら loss がさらに下がり Gravity/Unit が 90%+ になる可能性

## 次のアクション
- **FAST_ITER=False でフル学習（v82）で真価を確認**
  - v76 も quick run では format 未収束だった（2 epoch でフォーマットが固まる）
  - loss が 0.45 まで下がったので、フル学習では accuracy が大幅改善すると期待できる
  - reasoning_leakage=100% は 1 epoch 不足が原因であり、2 epoch フル学習で解消する可能性
  - もし v82 も 0.58 以下なら CoT アプローチ自体を見直す必要がある
