# PHASE7.0: ワークフロー設定の明示化と運用ループ整理

YAML のステップ別設定、起動前 validation、FEEDBACKS / ISSUES の運用ルール、`.claude/rules` への stable な規約配置をまとめて整理し、次ループへの handoff を明文化するフェーズ。

## 実装進捗

| 節 | 内容 | 状態 | 想定バージョン |
|---|---|---|---|
| §1 | workflow YAML による step 単位の system prompt / model 設定 override | 未着手 | ver10.0 |
| §2 | category・YAML・全 step の起動前 validation | 未着手 | ver10.0 |
| §3 | legacy `--auto` と対応 YAML 設定の撤去 | 未着手 | ver10.0 |
| §4 | FEEDBACKS の 1 ループ限定運用と `FEEDBACKS/done` 退避 | 未着手 | ver10.1 |
| §5 | `REQUESTS/AI` / `REQUESTS/HUMAN` の ISSUES への統合 | 未着手 | ver10.1 |
| §6 | `/retrospective` から次ループ向け FEEDBACK を書き出す handoff | 未着手 | ver10.1 |
| §7 | `.claude/rules` の整備と `scripts` 向け stable rule 追加 | 未着手 | ver10.2 |
| §8 | `/retrospective` による workflow system prompt / model 利用評価 | 未着手 | ver10.2 |

想定分割は ver10.0〜ver10.2 の 3 段階とし、CLI / YAML 仕様の整理を先行し、その上に運用ルールとレトロスペクティブ改善を重ねる。

## 概要

PHASE7.0 では、ワークフロー実行系の「何をどこで設定し、どの時点で壊れていることを検知し、ループ間で何を持ち越すか」を明文化する。主眼は 3 つある。第 1 に、workflow YAML で step ごとの system prompt / model 系設定を上書きできるようにしつつ、起動前に全 step を検証して実行途中の設定不整合をなくすこと。第 2 に、FEEDBACKS を 1 ループ限定の入力キューとして扱い、REQUESTS を ISSUES に統合して、運用上の入力チャネルを減らすこと。第 3 に、`/retrospective` と `.claude/rules` を強化し、次ループへの handoff と stable な作法を docs ではなく rules 側に寄せること。

## 動機

- 現状は workflow YAML が step 単位の prompt / model 調整に弱く、設定差分を試したいときにスクリプト側や SKILL 側へ責務が漏れやすい
- category ミス、YAML 記述ミス、存在しない step 参照などが実行途中まで発覚しないと、長いループの失敗コストが高い
- `--auto` の意味が実質的に曖昧で、CLI と YAML の両方に似た概念があると保守者と利用者が混乱する
- FEEDBACKS と REQUESTS が「一時入力」「恒常バックログ」「人間向けメモ」の役割を分離し切れておらず、次ループに何が自動で持ち越されるのかが曖昧
- `/retrospective` がコード作業の振り返り中心に寄り、workflow 自体の prompt / model 設計や次ループへの引き継ぎを十分に扱えていない
- `.claude/rules` に置くべき stable な運用規約が docs 側に散りやすく、scripts 系の複雑化に対して参照点が弱い

## 前提条件

- PHASE6.0 までで `/issue_plan` を含む workflow 分岐と、`scripts/claude_loop.py` の CLI 基盤が存在していること
- workflow YAML の読込と step 実行が `scripts/claude_loop.py` および `scripts/claude_loop_lib/` 配下に集約されていること
- `FEEDBACKS/`, `REQUESTS/`, `ISSUES/`, `.claude/rules/` の現行ディレクトリ構成が利用可能であること
- `REQUESTS/AI` / `REQUESTS/HUMAN` には移行が必要な既存ファイルが実質なく、主作業が運用ルールと参照先の更新で済むこと
- `/retrospective` と `/issue_plan` の SKILL / WORKFLOW 文書が存在し、次ループ handoff の指示追加先が明確であること

## やること

### 1. workflow YAML で step 単位の system prompt / model 系設定を override 可能にする

#### 1-1. 想定仕様

- workflow YAML は全体既定値に加え、各 step ごとに `system_prompt`, `model`, `temperature`, `max_tokens` などの model 関連設定を個別指定できるようにする
- step に個別指定がある場合はその step のみで優先し、未指定項目は workflow 全体の既定値を継承する
- override 対象は「実行系が安定して解釈できる設定」に限定し、任意キーの透過 pass-through は行わない
- step 定義から最終的に解決された有効設定は、少なくとも validation 時点で一意に決まる状態にする

#### 1-2. 完了条件

- workflow YAML だけで「この step だけ prompt / model を変える」が表現できる
- 同一 workflow 内で複数 step が異なる model 設定を持っても、継承順序が曖昧にならない
- 無効な model 名、未解決 prompt 参照、型不正な設定値は実行前 validation で検出される

### 2. 起動前 validation で category・YAML・全 step を最後まで検査する

#### 2-1. 検証対象

- `.claude/CURRENT_CATEGORY` または CLI 指定 category が有効なカテゴリ名であること
- 指定された workflow YAML が存在し、パース可能で、期待 schema を満たすこと
- workflow に含まれる全 step が、参照先の SKILL / command / workflow 定義まで含めて解決可能であること
- step ごとの override 設定が §1 の許容範囲内で、必須値が欠けていないこと
- 実行前に判定できる入出力条件がある場合は、その不足も同じ validation でまとめて報告すること

#### 2-2. 期待される挙動

- 実行開始時に workflow 全体を一度走査し、1 件でも重大な不整合があれば最初の step を実行せず終了する
- エラーは 1 件ずつ逐次停止ではなく、可能な範囲でまとめて列挙し、修正対象を一度で把握できるようにする
- validation 通過後は「最後まで到達可能な定義である」ことを最低限保証し、途中で設定起因の失敗を極力なくす

### 3. legacy `--auto` mode と対応 YAML 設定を撤去する

#### 3-1. 方針

- 旧来の `--auto` mode は廃止し、通常実行が常にその挙動を内包する前提へ寄せる
- YAML 側に `auto` mode と対になる設定項目が残っている場合も同時に撤去し、CLI と YAML の二重表現をなくす
- 旧オプションや旧設定を指定した場合は、黙って無視するのではなく、明示的なエラーまたは移行案内を返す

#### 3-2. 完了条件

- 実行者が「自動実行にするための別モード」を意識しなくてよい
- CLI ヘルプ、README、workflow YAML 例が同じ仕様を指す
- `--auto` と旧 YAML 設定の説明は docs / tests / 実装から消え、保守対象は 1 系統に絞られる

### 4. FEEDBACKS を 1 ループ限定の入力キューとして扱う

#### 4-1. 運用ルール

- 自動読込対象は `FEEDBACKS/` 直下のみとし、`FEEDBACKS/done/` 配下は次回 run で自動読込しない
- 1 回のループで読み込まれた FEEDBACK は、そのループ終了後に `FEEDBACKS/done/` へ移動する
- 同じ FEEDBACK を次回も使いたい場合だけ、人間が `FEEDBACKS/done/` から `FEEDBACKS/` 直下へ戻す
- FEEDBACK は「次の 1 ループへの一時的な入力」であり、恒久的な backlog や仕様メモとしては扱わない

#### 4-2. 期待される挙動

- 次回 run は前回取り込んだ FEEDBACK を自動再読込しない
- retrospective などが新しい FEEDBACK を生成した場合も、最大 1 回だけ消費される
- FEEDBACK の再利用は明示的な人間操作が必要になり、暗黙の持ち越しを防げる

### 5. `REQUESTS/AI` と `REQUESTS/HUMAN` を ISSUES に統合する

#### 5-1. 方針

- `REQUESTS/AI` と `REQUESTS/HUMAN` は workflow の入力源として廃止し、新規要求は `ISSUES/{category}/{priority}/*.md` に集約する
- AI 向けか human 向けかは `assigned`、進行状態は `status` など既存 ISSUE frontmatter で表現する
- 現状 `REQUESTS/` 配下に実ファイルがない前提を活かし、主作業はディレクトリ整理と docs / instructions の参照先更新に寄せる

#### 5-2. 完了条件

- docs, SKILL, workflow 説明のどこから見ても、「依頼を書く場所」は ISSUES で一貫する
- `REQUESTS/AI` と `REQUESTS/HUMAN` 前提の説明や分岐は残さない
- 人間向けメモのような用途も、必要なら ISSUES の `assigned: human` などで吸収する

### 6. `/retrospective` から次ループ向け FEEDBACK を書き出せるようにする

#### 6-1. handoff の対象

- `/retrospective` は必要に応じて、次のループで読むための FEEDBACK を `FEEDBACKS/` に書き出せるようにする
- handoff 内容には、次回の `issue_plan` に渡したい候補 ISSUE、注意点、保留判断、workflow 設定見直しメモを含められるようにする
- 特に「次に着手すべき ISSUE を `issue_plan` に渡す」用途を明示し、単なる感想ではなく次ステップに効く入力として扱う

#### 6-2. §4 との接続

- retrospective が書いた FEEDBACK も、次回 loop で 1 回だけ自動消費され、その後は `FEEDBACKS/done/` へ移る
- FEEDBACK を書かなかった場合は、次ループは通常どおり ISSUES / MASTER_PLAN を起点に判断する
- handoff は「次ループを少し有利にする補助線」であり、永続的な状態保存の代替にはしない

### 7. `.claude/rules` を整備し、`scripts` 向け stable rule file を追加する

#### 7-1. rules に置く内容

- `scripts/**/*` を対象にした rule file を追加し、`pathlib` 利用、CLI 引数処理、ログ出力、frontmatter / YAML 更新時の作法など、変わりにくい規約を定義する
- `.claude/rules` には「毎回守るべき約束」を置き、PHASE ごとの進行状況や一時的な注意点は docs 側に残す
- 既存 rule / CLAUDE / SKILL に重複がある場合は、stable な規約を rules 側に寄せ、説明責務を整理する

#### 7-2. 完了条件

- scripts 系の実装・編集で参照すべき規約が docs ではなく `.claude/rules` から辿れる
- volatile な運用メモと stable な作法が混ざらない
- `.claude/rules` の読込対象や適用範囲が明示され、agents が毎回同じ前提で動ける

### 8. `/retrospective` で workflow system prompt / model 利用も評価対象にする

#### 8-1. 評価項目

- 各 step の system prompt が役割に合っていたか、長すぎないか、指示重複がないかを振り返る
- 各 step の model 選択、temperature などが品質・速度・コストに見合っていたかを評価する
- 評価結果は「維持」「調整」「削除候補」の形で次回の YAML / FEEDBACK 修正に接続できるようにする

#### 8-2. 期待される挙動

- `/retrospective` がコード成果だけでなく workflow 設計そのものも改善対象として扱う
- §1 の step 別 override と組み合わせて、「どの step の prompt / model をどう変えるべきか」を次ループに具体的に渡せる
- prompt / model の見直しが人手の記憶頼みにならず、ループ改善の定常作業になる

## ファイル変更一覧

| ファイル | 操作 | 内容 |
|---|---|---|
| `scripts/claude_loop.py` | 変更予定 | step override 解決、起動前 validation、legacy `--auto` 廃止対応 |
| `scripts/claude_loop.yaml` | 変更予定 | step 別 prompt / model 設定、旧 `auto` 設定削除 |
| `scripts/claude_loop_quick.yaml` | 変更予定 | step 別 prompt / model 設定、旧 `auto` 設定削除 |
| `scripts/claude_loop_issue_plan.yaml` | 変更予定 | `issue_plan` handoff と step 設定 override の反映 |
| `scripts/claude_loop_lib/workflow.py` | 変更予定 | YAML schema 正規化、全 step validation、設定継承の解決 |
| `scripts/claude_loop_lib/commands.py` | 変更予定 | CLI 引数整理、廃止オプションのエラー化 |
| `scripts/claude_loop_lib/feedbacks.py` | 変更予定 | 1 ループ限定 FEEDBACK 読込と `FEEDBACKS/done` 退避 |
| `scripts/README.md` | 変更予定 | YAML 仕様、validation、FEEDBACKS ルール、REQUESTS 廃止の説明 |
| `.claude/SKILLS/issue_plan/SKILL.md` | 変更予定 | retrospective からの FEEDBACK handoff の受け取り指示 |
| `.claude/SKILLS/retrospective/SKILL.md` | 変更予定 | 次ループ FEEDBACK 書出し、prompt / model 評価の指示 |
| `.claude/SKILLS/meta_judge/WORKFLOW.md` | 変更予定 | FEEDBACKS / ISSUES / workflow YAML の新運用ルール反映 |
| `.claude/rules/scripts.md` | 新規作成予定 | scripts 系の stable conventions を定義する rule file |
| `CLAUDE.md` | 変更予定 | REQUESTS ではなく ISSUES を参照する運用へ説明更新 |
| `ISSUES/README.md` | 変更予定 | REQUESTS 統合後の起票・分類手順を明文化 |
| `REQUESTS/AI` | 廃止予定 | ISSUES 統合後は入力源として使わない |
| `REQUESTS/HUMAN` | 廃止予定 | ISSUES 統合後は入力源として使わない |

## リスク・不確実性

- step 別 override の優先順位を曖昧にすると、global 設定と step 設定のどちらが効くかが再びブラックボックス化する
- 起動前 validation で「全 step を検証する」ためには、実行せずに解決できる参照範囲を明確に切り出す必要がある
- `--auto` を撤去すると既存 wrapper やメモが壊れる可能性があるため、移行エラー文言と docs 更新を同じ変更セットで進める必要がある
- FEEDBACK を loop 終了時に移動する設計は、異常終了時の取り扱いを明確にしないと二重読込 or 取りこぼしが起きうる
- REQUESTS 統合後の ISSUE frontmatter 運用が曖昧だと、人間向けメモが再び別置き場へ流出する
- rules と docs の責務分離を中途半端にすると、stable convention が二重管理になる

## やらないこと

- workflow YAML から任意の内部実装パラメータを無制限に上書きできるようにはしない
- `FEEDBACKS/done` を自動再読込する仕組みは作らない
- REQUESTS を ISSUES と並ぶ第 2 の恒久バックログとして残さない
- retrospective を恒久メモリ機構や状態 DB の代替にはしない
- `.claude/rules` に PHASE 固有の進捗メモや頻繁に変わる運用ログまでは書かない