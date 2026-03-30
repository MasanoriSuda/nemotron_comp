# 0002 - format_fix_v76

## 仮説
出力フォーマットを`\boxed{answer}`のみに統一し、オーバーサンプリングバグを修正することでスコアが上がる。

## 設定
| パラメータ | 変更前(v65) | 変更後(v76) |
|-----------|------------|------------|
| 出力フォーマット | `Rule: ...\n\boxed{answer}` | `\boxed{answer}`のみ |
| オーバーサンプリング | バグあり | 修正（hard 3x, medium 2x, easy 1x） |
| MAX_SEQ_LEN | 1024 | 1024 |
| BATCH_SIZE | 4→8 | 8 |
| NUM_EPOCHS | - | 2 |
| SANITY_MAX_NEW_TOKENS | 64 | 160 |
| train_loss (final avg) | - | 0.694 |

## 結果
- Kaggle Score: **0.65** (+0.02)
- eval: タイムアウトにより eval_results.json 未取得

## 学び
- フォーマット修正で+0.02の改善
- SANITY_MAX_NEW_TOKENS=160 → evalが475件×~128秒 ≈ 17時間でタイムアウト
- submission.zipはeval前に保存する設計が機能した
