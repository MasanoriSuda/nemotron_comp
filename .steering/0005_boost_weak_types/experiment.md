# 0005 - boost_weak_types

## 仮説
Bit Manipulation と Gravitational Constant のオーバーサンプリングを強化することで、
これら2タイプの accuracy を改善できる。
他の人の分析では Bit Manipulation 30%、Gravity 12% が達成可能なことが分かっている。
現状 v76 ではどちらもほぼ 0% なので、データ量の不足が原因の可能性がある。

## 設定

| パラメータ | 変更前 | 変更後 |
|-----------|--------|--------|
| Bit Manipulation オーバーサンプリング | 3x (HARD_TYPES) | 5x |
| Gravitational Constant オーバーサンプリング | 2x (MEDIUM_TYPES) | 5x |
| Text Encryption | 3x | 3x (変更なし) |
| Equation Transformation | 3x | 3x (変更なし) |
| Unit Conversion | 2x | 2x (変更なし) |
| Number Base Conversion | 1x | 1x (変更なし) |
| FAST_ITER | True | True (1時間検証) |
| MAX_TRAIN_SAMPLES | 3000 | 3000 |

実装: per-type `OVERSAMPLE_RATES` dict に変更（旧: hard/medium/easy の一括設定）

## 結果
- Kaggle Score:
- Overall accuracy:
- By type:

| タイプ | 正解率 | boxed率 |
|--------|--------|---------|
| Number Base Conversion | | |
| Bit Manipulation | | |
| Equation Transformation | | |
| Gravitational Constant | | |
| Text Encryption | | |
| Unit Conversion | | |
| **Overall** | | |

## 学び
<!-- 次に活かすこと -->
