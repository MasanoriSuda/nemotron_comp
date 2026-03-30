---
name: new-experiment
description: Create a new experiment entry under .steering/. Use when starting a new training run or experiment. Creates a numbered folder and experiment.md template.
---

# New Experiment

Creates a new experiment folder under `.steering/` with a numbered directory and `experiment.md` template.

## Usage

```
/new-experiment <title>
```

Example:
```
/new-experiment answer_only_format
```

## Steps

1. List existing `.steering/` directories to find the next number (zero-padded to 4 digits)
2. Create `.steering/<NNNN>_<title>/experiment.md` with the template below
3. Report the created path

## Template

```markdown
# <NNNN> - <title>

## 仮説
<!-- 何を期待してやるか -->

## 設定
<!-- 変更したパラメータ・コード -->
| パラメータ | 変更前 | 変更後 |
|-----------|--------|--------|
|  |  |  |

## 結果
<!-- スコア・eval数値 -->
- Kaggle Score:
- Overall accuracy:
- By type:

## 学び
<!-- 次に活かすこと -->
```
