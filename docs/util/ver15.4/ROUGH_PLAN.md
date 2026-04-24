---
workflow: full
source: master_plan
---

# ver15.4 ROUGH_PLAN — PHASE7.1 §4（run 単位・永続通知）

## バージョン種別

**マイナー（ver15.4）**。PHASE7.1 §4 は通知実装の独立改修で、新 PHASE 骨子作成・アーキテクチャ変更・新規カテゴリ追加のいずれにも該当しない。新規外部ライブラリは導入せず、標準ライブラリと既存 PowerShell toast 経路の範囲で完結させる。

## 着手対象

PHASE7.1 §4（ワークフロー終了通知を「run 単位・手動 dismiss まで残る」仕様に改める）を実装する。PHASE7.1 §1 / §2 / §3 は ver15.0〜ver15.3 で実装済みで、本節を消化すれば PHASE7.1 全体が完走する。

## 提供する体験の変化

- `python scripts/claude_loop.py --max-loops N` で **1 回だけ通知が届く**（現行は loop 完了ごとに N 回通知）
- 席を外している間に multi-loop 実行が終わっていても、戻った時点で run 完了に気づける通知が残っている
- 成功・失敗・中断（Ctrl+C / タイムアウト等）で通知タイミングが一貫する
- 通知文だけで「どの workflow を何 loop 回したか、所要時間はいくらか、成功か失敗か（失敗なら終了コード／失敗 step）」が把握できる

## スコープ（実施する）

1. **通知タイミングを loop 単位 → run 単位へ移行**: `claude_loop.py` の通知呼び出し位置を整理し、`--max-loops` によらず run 全体の終了時に 1 回のみ発火する
2. **通知内容の run サマリ化**: workflow 種別 / loop 実行回数 / 所要時間 / 成功/失敗/中断区分 / 失敗時の終了コードと失敗 step を通知本文に含める
3. **永続表示に寄せた通知スタイル**: Windows トーストで可能な限り「人が閉じるまで残る」挙動を目指し、OS 制約で完全な常駐が難しければ自動消滅しにくい fallback を用意する
4. **成功・失敗・中断の各経路で通知を一貫して出す**: 正常終了 / 例外 / SIGINT / timeout のいずれでも、run 終了時に通知発火点が 1 箇所に収束するよう制御フローを整理する
5. **既存抑止オプションの維持**: `--no-notify` と `--dry-run` は現行どおり通知抑止として機能させる
6. **docs 同期**: `scripts/README.md` / `scripts/USAGE.md` の通知仕様説明を新仕様へ更新する

## スコープ外（実施しない）

- Slack / Discord / email 等の外部通知サービス連携
- 通知音・アイコン・画像等のリッチコンテンツ追加
- Linux / macOS 向け通知バックエンドの新規実装（現行 Windows 前提を維持）
- loop 単位の進捗通知を別オプションとして復活させるフラグ追加
- `scripts/` 配下の他ファイル（`claude_sync.py` / `issue_*.py` / `question_*.py` 等）のロジック改修
- ver15.3 起票の 3 件の follow-up ISSUE（generation / drift / omission）の能動消化 — 本バージョンの `/issue_plan` 実行自体が観察材料となるため並走観察にとどめる

## 想定成果物

| ファイル | 操作 | 役割 |
|---|---|---|
| `scripts/claude_loop_lib/notify.py` | 変更 | run サマリを受け取る通知 API、永続表示 fallback を追加 |
| `scripts/claude_loop.py` | 変更 | 通知呼び出しを run 終了時 1 箇所に集約、成功/失敗/中断の収束経路を整理 |
| `scripts/README.md` | 変更 | 通知仕様セクションを run 単位・永続表示前提に更新 |
| `scripts/USAGE.md` | 変更 | `--no-notify` / `--dry-run` / multi-loop 時の通知挙動を追記 |
| `docs/util/MASTER_PLAN/PHASE7.1.md` | 変更 | §4 の進捗表を「実装済み（ver15.4）」に更新 |
| `scripts/tests/` 配下 | 追加 or 変更 | run サマリ生成・通知抑止フラグ・中断経路のユニットテスト |
| `docs/util/ver15.4/CHANGES.md` / `IMPLEMENT.md` / `REFACTOR.md` / `MEMO.md` | 追加 | 後続 step で作成 |

## ワークフロー選択根拠

**workflow: full** を選択する。根拠:

- MASTER_PLAN（PHASE7.1 §4）の新項目に着手する — SKILL 規則「MASTER_PLAN 新項目 → 必ず `full`」に該当
- 通知の制御フロー整理は `claude_loop.py` 本体のエラーハンドリング経路に触れるため、変更対象が 3 ファイル以下・100 行以下の quick 基準には収まらない見込み
- OS トースト制約の検証と fallback 設計は review step で plan_review_agent を通す価値がある

## 事前リファクタリング要否

**不要**と判断する。`notify.py` は単一関数 `notify_completion(title, message)` + 2 ヘルパの小さな構造で、run サマリ導入に伴う API 拡張はそのまま同ファイル内で完結できる。`claude_loop.py` 側の通知呼び出し位置整理は §4 実装と不可分のため、先行リファクタとしてではなく本実装内で扱う（根拠の詳細は `PLAN_HANDOFF.md`）。

## 参照

- 推奨根拠・選定理由・除外理由・ISSUE 状態サマリ・並走観察対象 → `PLAN_HANDOFF.md`
- 実装手順・タイムライン → 後続 `/split_plan` で `IMPLEMENT.md` を作成
- MASTER_PLAN 原文 → `docs/util/MASTER_PLAN/PHASE7.1.md` §4
