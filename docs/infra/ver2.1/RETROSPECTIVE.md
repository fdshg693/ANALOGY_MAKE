# ver2.1 振り返り

## 1. ドキュメント構成整理

### MASTER_PLAN.md

- PHASE1.0（Azure デプロイ基盤）・PHASE1.5（Bicep IaC）ともに実装済みマーク
- ver2.1 で CI/CD のシンボリックリンク問題を修正済み（PHASE1.0 の補足として記載済み）
- 現在の ISSUES 数: high(2), medium(1), low(1) — 管理可能な規模
- **判断**: 新フェーズの追加は次回の実デプロイ検証完了後が適切。現時点では不要

### CLAUDE.md

- プロジェクトルートの CLAUDE.md は約90行で安定
- infra カテゴリ固有の情報は `docs/infra/` 配下のドキュメントに十分分離されている
- **判断**: 分割不要

## 2. バージョン作成フローの振り返り

### 概要

| 項目 | 値 |
|---|---|
| カテゴリ | infra |
| バージョン | 2.1（マイナー） |
| 変更ファイル数 | 4（コード変更: deploy.yml, Justfile, .gitignore, bicepparam→example） |
| 追加行数 | 約50行（コード変更分） |
| ISSUES クローズ | 0（デプロイ検証待ち） |

### ステップ別評価

#### split_plan（ステップ1）: ★★★

- シンボリックリンク問題の根本原因分析が正確
- 代替案（`externals.inline`、`--node-linker=hoisted`、`rsync -rL`）を検討し合理的に却下
- 小規模タスクのため REFACTOR 省略は適切

#### imple_plan（ステップ2）: ★★★

- IMPLEMENT.md の計画と完全一致（乖離ゼロ）
- typecheck エラーなし、テスト 53/53 パス
- 単一ファイル変更で明確なスコープ

#### wrap_up（ステップ3）: ★★☆

- 全項目がデプロイ依存のため適切に📋先送り判定
- **課題**: 既存 ISSUES（Actionデプロイ.md, verify-output-dir-azure.md）に「修正適用済み・検証待ち」のステータス更新がされていない。修正が適用済みであることが ISSUES ファイルを読んだだけでは分からない

#### write_current（ステップ4）: ★★☆

- CHANGES.md は deploy.yml の変更のみ記載
- **課題**: 同バージョンスコープ内の以下の変更が CHANGES.md に未記載:
  - `Justfile`: Windows PowerShell 対応、`info` コマンド追加、コマンド1行化
  - `.gitignore`: 新規エントリ追加
  - `infra/main.bicepparam` → `infra/main.bicepparam.example`: シークレット除外

これらは split_plan 前の調査・対応フェーズで行われた変更だが、バージョン差分のスコープ内であり、CHANGES.md に記載すべきだった。

### 良かった点

1. **根本原因分析の精度**: ZIP デプロイのシンボリックリンク非保持という本質を正確に特定
2. **汎用的な解決策**: `hookable` だけでなく全シンボリックリンクに対応する方式を選択し、将来の依存追加にも自動対応
3. **事後検証の組み込み**: スクリプト内に残存シンボリックリンクのチェックを含め、サイレント失敗を防止
4. **計画精度**: 単一ファイル変更の計画が実装と完全一致

### 改善が必要な点

1. **CHANGES.md の網羅性不足**（ver2.0 からの継続課題ではなく新規）
   - write_current スキルが `REFACTOR.md`・`IMPLEMENT.md`・`MEMO.md` のみを変更把握のソースとしているため、計画外の変更（調査中の修正等）が漏れる
   - **対策**: write_current スキルに git diff による検証ステップを追加 → **本ステップで適用済み**

2. **ISSUES のステータス管理不足**（ver2.0 からの継続的な課題）
   - 修正が適用済みだが未検証の ISSUES について、現状ステータスが更新されない
   - **対策**: wrap_up スキルに既存 ISSUES のステータス更新ガイダンスを追加 → **本ステップで適用済み**

3. **バージョン境界の曖昧さ**（軽微）
   - split_plan 前の調査で行われた変更（Justfile、.gitignore 等）がバージョンスコープに含まれるが、計画には反映されない
   - これは調査フェーズの性質上避けがたく、write_current での git diff 検証で十分カバーできる

## 3. 次バージョン推奨

### 残存 ISSUES

| ISSUE | 優先度 | 状況 |
|---|---|---|
| `Actionデプロイ.md` | high | 修正適用済み、デプロイ検証待ち |
| `Windowsデプロイ.md` | high | 未対応（Docker 等の新アプローチ必要） |
| `verify-output-dir-azure.md` | medium | 修正適用済み、デプロイ検証待ち |
| `action_warning.md` | low | 期限: 2026-06-02（Node.js 20 強制移行） |

### 推奨: ver2.2（マイナー）

**理由**:
- 次の最優先タスクは `dev` → `main` マージ後の実デプロイ検証と ISSUES クローズ
- 新機能追加・アーキテクチャ変更を伴わない検証・クローズ作業はマイナーバージョンが適切
- Windows デプロイ対応（Docker 等）は別途メジャーバージョン（ver3.0）で対応すべき規模

## 4. スキル改善（本ステップで適用済み）

### write_current/SKILL.md

CHANGES.md / CURRENT.md の作成後に、git diff と突合する検証ステップを追加。計画外の変更の記載漏れを防止する。

### wrap_up/SKILL.md

既存 ISSUES に対して修正が適用済みだが未検証の場合、ISSUES ファイルにステータスを追記するガイダンスを追加。
