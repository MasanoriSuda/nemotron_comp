# 0001 - baseline_v65

## 仮説
初期アダプタ。フォーマット・オーバーサンプリングに問題あり。

## 設定
| パラメータ | 値 |
|-----------|-----|
| LORA_R | 32 |
| MAX_SEQ_LEN | 1024 |
| BATCH_SIZE | 8 |
| NUM_EPOCHS | 不明 |
| 出力フォーマット | `Rule: ...\n\boxed{answer}` |
| オーバーサンプリング | バグあり（Text Encryptionがhard扱いから漏れ） |

## 結果
- Kaggle Score: **0.63**
- eval (80件):

| タイプ | 正解率 | boxed率 |
|--------|--------|---------|
| Number Base Conversion | 77.8% | 77.8% |
| Bit Manipulation | 23.1% | 53.8% |
| Equation Transformation | 0% | 0% |
| Gravitational Constant | 0% | 0% |
| Text Encryption | 0% | 0% |
| Unit Conversion | 0% | 0% |
| **Overall** | **12.5%** | **17.5%** |

## 学び
- boxed_rate 17.5%：フォーマット崩壊が主因
- Number Base Conversionはベースモデルの素の理解力で解けている
- Text Encryptionがオーバーサンプリングから漏れていた
