# 0004 - answer_only_format

## 仮説
システムプロンプトとユーザープロンプトに「答えだけ返せ」指示を追加することで、
モデルが推論文を出力せず\boxed{answer}のみを返すようになりスコアが上がる。

## 設定
| パラメータ | 変更前(v76) | 変更後 |
|-----------|------------|--------|
| SYSTEM_PROMPT | "...Output your answer inside \boxed{}." | "...Output only the final answer inside \boxed{}. Do not explain your reasoning." |
| user content | row['prompt'] | row['prompt'] + "\nReturn only the final answer." |
| MAX_TRAIN_SAMPLES | None | 3000（クイック検証） |
| MAX_SEQ_LEN | 512(v78) | **1024**（戻す） |
| FAST_ITER | False | True |
| NUM_EPOCHS | 2 | 1 |

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

## 制限事項
- FAST_ITER用のクイック検証のため、MAX_TRAIN_SAMPLES=3000/NUM_EPOCHS=1と「答えのみ出力」プロンプト変更が同時に変わっている
- スコア変化がプロンプト変更の効果か学習量の違いによるものか判別できない
- この実験はあくまで「プロンプト変更が機能するか」の方向感を掴むもの
- 有効と判断した場合はFAST_ITER=Falseでフル学習して確認する

## 学び
<!-- 結果が出たら記入 -->
