# 0004 - answer_only_format

## 仮説
システムプロンプトとユーザープロンプトに「答えだけ返せ」指示を追加することで、
モデルが推論文を出力せず\boxed{answer}のみを返すようになりスコアが上がる。

## 設定

| パラメータ | 変更前(v76) | 変更後 |
|-----------|------------|--------|
| SYSTEM_PROMPT | "...Output your answer inside \boxed{}." | "...Output only the final answer inside \boxed{}. Do not explain your reasoning." |
| user content | row['prompt'] | row['prompt']（変更なし） |
| MAX_TRAIN_SAMPLES | None | 3000（クイック検証） |
| MAX_SEQ_LEN | 512(v78) | **1024**（戻す） |
| FAST_ITER | False | True |
| NUM_EPOCHS | 2 | 1 |

## 結果
- Kaggle Score: 未提出（v76=0.65 より大幅悪化のため見送り）
- Overall accuracy: 1.7% (1/60)
- boxed率: 13.3% (8/60)
- train_loss: 1.86（v76=0.694 より高く未収束）

| タイプ | 正解率 | boxed率 |
|--------|--------|---------|
| Number Base Conversion | 12.5% (1/8) | 100% (8/8) |
| Bit Manipulation | 0% (0/9) | 0% |
| Equation Transformation | 0% (0/13) | 0% |
| Gravitational Constant | 0% (0/10) | 0% |
| Text Encryption | 0% (0/11) | 0% |
| Unit Conversion | 0% (0/9) | 0% |
| **Overall** | **1.7%** | **13.3%** |

Sample errors:
- [Gravitational Constant] got="We need to infer the rule. The examples show distance vs time..."（推論文垂れ流し）
- [Number Base Conversion] expected="LV" got="55"（正しい数値だが形式違い）
- [Bit Manipulation] got="3"（全く別形式）

## 学び
- SYSTEM_PROMPT の「answer only」指示だけではベースモデルの推論癖は消えない
  - 52/60 サンプルで `\boxed{}` なし → モデルが推論文を出力し続ける
- 3000 samples/1 epoch では format 上書きに全く足りない（train_loss=1.86 で未収束）
- Number Base Conversion だけ boxed=100% だが正解率は 76%→12.5% に激落ち
- v76（フル学習、boxed形式）が依然ベスト（0.65）
- **次の方向**: v76 ベースに戻し、後処理（タイプ別正規化）＋ user プロンプト追加＋タイプ別増強でフル学習
