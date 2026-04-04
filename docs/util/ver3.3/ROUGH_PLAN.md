# ver3.3 ROUGH_PLAN

## 対応種別

ISSUES 対応: `ISSUES/util/medium/ワークフロー改善.md`

## 背景

CURRENT.md はメジャーバージョンごとに「コード現況の完全版」を記述するファイルだが、カテゴリの成熟に伴い記載量が増大している（例: `docs/util/ver3.0/CURRENT.md` は 297行）。このまま機能追加が続くと、1ファイルでの管理が困難になる。

## 課題

1. **書き込み側**: write_current SKILL の CURRENT.md 記載ルールに「肥大化時は分割を検討する」とあるが、具体的な分割基準・方法が不明確で、実際には分割されたことがない
2. **読み込み側**: split_plan・imple_plan・quick_plan の各 SKILL は CURRENT.md を単一ファイルとして読む前提で記述されており、分割後のファイル構成に対応していない

## スコープ

CURRENT.md のファイル分割を SKILL レベルで運用可能にするため、関連 SKILL ファイルの記述を更新する:

- **write_current SKILL**: CURRENT.md の分割ルール（基準・命名規則・インデックス構成）を具体化する
- **読み込み側 SKILL**（split_plan・imple_plan・quick_plan）: CURRENT.md が分割されている場合に、必要なファイルだけを選択的に読み込む記述に変更する
- **retrospective SKILL**: CURRENT.md を直接参照しないため変更対象外

## 小規模タスクのため REFACTOR 省略

変更対象は 4 SKILL ファイル（テキスト文言のみ）でコード変更なし。ファイル数は基準（3つ以下）を超えるが、各ファイルの変更量は数行〜十数行で合計 100 行以下に収まる見込みのため、小規模タスクとして扱う。事前リファクタリング不要。
