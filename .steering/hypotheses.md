# 弱点分析・仮説・実験計画

## 現状スコア
- **Best: v76 = 0.65** (全件, 1epoch, loss=0.694, answer-only)
- **v81 quick**: loss=0.45（Gravity/Unit CoT, 1epoch）→ **LB=0.58**（悪化）
- **v82 full**: loss=0.03（Gravity/Unit CoT 21,000件過学習）→ **LB=0.60**（悪化）
- **v85 quick**: loss=0.65（Numeral CoT追加 + SYSTEM_PROMPT修正）→ **LB=0.67 ★ New Best**
- 他者参考: 0.67（全6タイプ CoT 2,907件）, 0.68（CoT 1,200件）, 0.70（全タイプ CoT 7,200件）

---

## 根本原因：CoT データ設計が間違っていた

| 問題 | 我々（v81/v82） | 正解（0.67〜0.70モデル） |
|------|----------------|------------------------|
| CoT 対象タイプ | Gravity/Unit のみ（2/6） | 全6タイプ |
| サンプル数 | 21,000（5x オーバーサンプリング） | 1,200〜3,000 |
| 多様性 | 同じ式の繰り返し → loss=0.03 | 多様な推論 → loss=2.3 |
| 検証 | 決定論的で100%正解 | LLM生成 + rule-based 検証フィルタ |
| fast_path | デフォルト（ON） | 明示的に OFF |

**CoT フォーマット（`<think>` の扱い）は誤差範囲**  
0.70 モデルも `content` 直書き（`<think></think>CoT\boxed{}`）で成功 → 最有力仮説から降格

---

## タイプ別分析（他者実績込み）

| タイプ | 件数 | CoT pass rate（他者実績） | 対策 |
|--------|------|--------------------------|------|
| Gravity | 1,597 | 99.7%（決定論的） | 生成済み ✓ |
| Unit | 1,594 | 88.7% | 生成済み ✓ |
| Numeral | 1,576 | 99.6%（決定論的） | 未実装（自動生成可） |
| Text Encryption | 1,576 | **94.3%（77語辞書埋め込みで劇的改善）** | Alice 77語辞書を入手して生成 |
| Bit Manipulation | 1,602 | 40.3%（難） | トレースデータ待ち |
| Equation Transformation | 1,555 | 13.6%（最難） | 後回し |

---

## CoT データ生成方針（修正版）

### 目標
- 全タイプ合計 **1,500〜3,000 件**（少量・多様・検証済み）
- fast_path OFF は OOM → **使用不可**（PRO6000 でも 94GB 超える）
- オーバーサンプリングしない
- SYSTEM_PROMPT から `Do not explain your reasoning` を削除（CoT 出力と矛盾するため）

### タイプ別アクション

| タイプ | 方法 | 優先度 |
|--------|------|--------|
| Gravity | 決定論的生成（実装済み）→ 400件に絞る | 完了 |
| Unit | 決定論的生成（実装済み）→ 700件に絞る | 完了 |
| Numeral | 決定論的生成（実装予定）→ 300件 | ★★★ すぐできる |
| Text Encryption | Alice 77語辞書入手 → Claude で生成 → 検証 → 700件 | ★★★ |
| Bit Manipulation | トレースプロンプト付き生成 → 検証 → 607件（全正解） | ★★ データ待ち |
| Equation | Claude で生成 → 検証 → 200件（全正解） | ★ 後回し |

---

## 実験キュー

各ステップは quick run（~1h）。`\boxed{}` 出力率と accuracy を判定基準にする。

| Step | 実験 | 変更点 | 結果 |
|------|------|--------|------|
| S1 | v83 | fast_path OFF | ✗ OOM クラッシュ |
| S2 | v84 | fast_path 戻す + Numeral CoT + オーバーサンプリング全1x | `\boxed{}` 未出力（SYSTEM_PROMPT 矛盾）→ 中断 |
| S3 | **v85** | SYSTEM_PROMPT から `Do not explain your reasoning` 削除 | **LB=0.67 ★ New Best** |
| S4 | v86 | S3 + Text Encryption CoT（77語辞書）追加 | pending |
| S5 | v87 | S4 + Bit CoT（トレースデータ）追加 | pending |
| S6 | v88 | S5 + LoRA target `in_proj\|out_proj` のみ | pending |

---

## GPU 時間制約

- 週 30h / quick run ~1h → 週 ~25 本
- medium run（1 epoch 全件）= ~5h → S2 以降で LB 確認に使う
- フル学習（2 epoch 全件）= 12h 超 → **タイムアウト、使用不可**

---

## スコア試算

| 状態 | 予想スコア |
|------|-----------|
| v76（現 best） | 0.65 |
| S1（全タイプ CoT, 少量）| **0.67〜0.68** |
| S2（+ Text Encryption 辞書）| **0.69〜0.70** |
| S3（+ Bit CoT）| **0.71〜0.72** |
| S5（+ LoRA 最適化）| **0.73+** |

---

## その他の仮説（優先度低）

- `thinking チャネル不整合`: 0.70 モデルも同じ形式で成功 → 優先度を降格
- `use_cache ON/OFF`: Mamba 実行経路の差異 → 後回し
- `torch.compile OFF`: 安定性確認のため 1本取りたい → S5 以降
- `MAX_SEQ_LEN=1024`: CoT 付きでも最大 412 token → 問題なし
