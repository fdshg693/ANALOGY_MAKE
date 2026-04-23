---
status: raw
assigned: ai
priority: low
---
# `.claude/rules/*.md` の `paths:` frontmatter 自動読込挙動の検証

## 概要

ver14.0（PHASE7.0 §7）で `.claude/rules/scripts.md` を新規作成し、`paths: scripts/**/*` frontmatter を付けた。しかし Claude Code が `paths:` frontmatter をどう解釈するか（agent 実行時にどの条件で rule が注入されるか、path glob の書式対応範囲など）は公式ドキュメントに明示がなく、`claude_edit.md` 以外の実例が乏しい。

本バージョンでは「ルールとして書いておけば agents が参照しうる状態」を整えるに留めており、実動作の検証は先送りしている。

## 本番発生時の兆候

- scripts 系を編集するセッションで `.claude/rules/scripts.md` が期待どおり注入されていない（agent 出力に規約違反が見える、`print()` を新規に書く、`Optional[...]` 型を使う等）
- 逆に scripts 以外を編集するセッションにも rules/scripts.md が注入されてコンテキストを圧迫している
- `paths:` の glob 形式が期待どおり解釈されず、意図しないファイルセットにマッチする

## 対応方針

1. ver15.0 以降の `/retrospective` §3.5 評価で本 rule の注入挙動を観察対象にする
2. 挙動が想定と異なる場合は `paths:` の書式変更（例: 複数 glob の列挙、除外パターン追加）や、必要なら rules を SKILL 本文側に戻す判断を検討する
3. 公式ドキュメント・issue tracker で `paths:` frontmatter の仕様が明示され次第、本 ISSUE に追記し `ready` 昇格

## 影響範囲

- 影響は `.claude/rules/scripts.md` 1 ファイルに限定
- 既存 `.claude/rules/claude_edit.md`（`paths: .claude/**/*`）の挙動に関しても同様の不確実性があるため、併せて観察対象にする
- 規約違反があっても Python コード実行は壊れず、コード品質の低下として顕在化するにとどまる（セキュリティリスク・データ破壊リスクはない）

## 参照

- `docs/util/ver14.0/IMPLEMENT.md` §6-6（リスク列挙）
- `.claude/rules/scripts.md`（本 rule 本体）
- `.claude/rules/claude_edit.md`（既存の `paths:` 付き rule の唯一の実例）
