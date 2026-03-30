# 0003 - seq512_v78

## 仮説
MAX_SEQ_LEN=512 + gradient_checkpointing=False + BATCH_SIZE=16 で学習を高速化できる。

## 設定
| パラメータ | 変更前(v76) | 変更後(v78) |
|-----------|------------|------------|
| MAX_SEQ_LEN | 1024 | **512** |
| BATCH_SIZE | 8 | 16 → OOMで8に戻す |
| GRAD_ACCUM | 4 | 2 → OOMで4に戻す |
| gradient_checkpointing | True | False → OOMで True に戻す |
| SANITY_MAX_NEW_TOKENS | 160 | **64** |

## 結果
- v77(BS=16, gc=False): **OOM**（logitsテンソル 16×326×131072 で2.55GB不足）
- v78(BS=8, gc=True, seq=512): Kaggle Score **0.63**（-0.02）
- eval (475件完走):

| タイプ | 正解率 | boxed率 |
|--------|--------|---------|
| Number Base Conversion | 76.25% | 96.25% |
| Bit Manipulation | 0% | 0% |
| Equation Transformation | 0% | 0% |
| Gravitational Constant | 0% | 2.25% |
| Text Encryption | 0% | 0% |
| Unit Conversion | 0% | 0% |
| **Overall** | **12.84%** | **16.63%** |

## 学び
- NemotronはMamba(SSM)ベース → O(n)処理 → MAX_SEQ_LEN削減では高速化できない
- MAX_SEQ_LEN=512でプロンプトが切れる → \boxed{}フォーマット学習失敗
- Number Base ConversionだけはプロンプトがSEQ内に収まり76%維持
- BS=16 + gc=False は102GB VRAMでもOOM（vocab=131072のlogitsが原因）
- **MAX_SEQ_LEN=1024に戻すべき**。高速化の打ち手はほぼない
