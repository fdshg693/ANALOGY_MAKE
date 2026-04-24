#!/usr/bin/env bash
# 何を確かめるためか:
#   RESEARCH.md §U2（_execute_resume で --bare を採用すべきか）と
#   §U3（同一 session id への 2 回目 -r が安全に履歴を継承できるか）を
#   nested claude CLI バイアスなしに実測するための人手実行用 harness。
#
# いつ削除してよいか:
#   scripts/claude_loop_lib/deferred_commands.py::_execute_resume の
#   --bare 採否が確定し、EXPERIMENT.md §U2/§U3 が埋まった時点。
#
# 使用方法:
#   ./run_experiment.sh [--with-bare|--without-bare|--both]
#   オプション省略時は --both（--bare あり → --bare なし の順）
#
# 前提:
#   - WSL / Git Bash 環境で手動実行すること
#   - claude CLI がパスに通っていること
#   - jq がインストールされていること（--output-format json の解析に使用）
#   - nested claude 起動（claude_loop.py / workflow YAML 経由）は禁止
#     （観測バイアス回避のため: IMPLEMENT.md §5-5 / PLAN_HANDOFF.md §quick_impl 参照）

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"

# 観測トークン（履歴継承確認用）
OBSERVATION_TOKEN="kiwi42"

usage() {
    grep '^#' "$0" | sed 's/^# \{0,1\}//' | head -20
    echo ""
    echo "Usage: $0 [--with-bare|--without-bare|--both]"
    exit 0
}

log() {
    echo "[$(date +%H:%M:%S)] $*"
}

# 1 周分の実験（3 発話）を実行する
# $1: "with_bare" または "without_bare"
run_session() {
    local mode="$1"
    local bare_flag=""
    if [[ "$mode" == "with_bare" ]]; then
        bare_flag="--bare"
    fi

    local log_file="$LOG_DIR/${TIMESTAMP}_${mode}.log"
    mkdir -p "$LOG_DIR"

    log "=== 実験開始: $mode ===" | tee -a "$log_file"
    log "bare_flag='${bare_flag}'" | tee -a "$log_file"

    # Session ID 採番
    local session_id
    session_id="$(python -c "import uuid; print(uuid.uuid4())")"
    log "session_id=$session_id" | tee -a "$log_file"

    # --- 発話 1: 観測トークンを記憶させる ---
    log "--- 発話1: 観測トークン記憶 ---" | tee -a "$log_file"
    local t1_start t1_end t1_duration
    t1_start="$(date +%s%3N)"

    local out1
    # shellcheck disable=SC2086
    out1="$(claude $bare_flag \
        -p "実験のために '${OBSERVATION_TOKEN}' という単語を必ず記憶してください。確認のため、その単語をそのまま復唱してください。" \
        --session-id "$session_id" \
        --output-format json 2>&1)" || true

    t1_end="$(date +%s%3N)"
    t1_duration=$(( t1_end - t1_start ))

    log "発話1 終了コード: $?" | tee -a "$log_file"
    log "発話1 実行時間: ${t1_duration}ms" | tee -a "$log_file"
    echo "=== 発話1 出力 ===" | tee -a "$log_file"
    echo "$out1" | tee -a "$log_file"

    # token usage 抽出（json モード時のみ有効）
    local usage1
    usage1="$(echo "$out1" | jq -r '.usage // "N/A"' 2>/dev/null || echo "N/A")"
    log "発話1 usage: $usage1" | tee -a "$log_file"

    # --- 発話 2: 同一 session id で resume（別プロンプト）---
    log "--- 発話2: resume (2回目 -r) ---" | tee -a "$log_file"
    local t2_start t2_end t2_duration
    t2_start="$(date +%s%3N)"

    local out2
    # shellcheck disable=SC2086
    out2="$(claude $bare_flag \
        -p "次の step に進みます。引き続き処理を続けてください。" \
        -r "$session_id" \
        --output-format json 2>&1)" || true

    t2_end="$(date +%s%3N)"
    t2_duration=$(( t2_end - t2_start ))

    log "発話2 終了コード: $?" | tee -a "$log_file"
    log "発話2 実行時間: ${t2_duration}ms" | tee -a "$log_file"
    echo "=== 発話2 出力 ===" | tee -a "$log_file"
    echo "$out2" | tee -a "$log_file"

    local usage2
    usage2="$(echo "$out2" | jq -r '.usage // "N/A"' 2>/dev/null || echo "N/A")"
    log "発話2 usage: $usage2" | tee -a "$log_file"

    # --- 発話 3: 観測トークンの想起（履歴継承確認）---
    log "--- 発話3: 観測トークン想起 (§U3 判定) ---" | tee -a "$log_file"
    local t3_start t3_end t3_duration
    t3_start="$(date +%s%3N)"

    local out3
    # shellcheck disable=SC2086
    out3="$(claude $bare_flag \
        -p "先ほど記憶をお願いした単語を答えてください。" \
        -r "$session_id" \
        --output-format json 2>&1)" || true

    t3_end="$(date +%s%3N)"
    t3_duration=$(( t3_end - t3_start ))

    log "発話3 終了コード: $?" | tee -a "$log_file"
    log "発話3 実行時間: ${t3_duration}ms" | tee -a "$log_file"
    echo "=== 発話3 出力 ===" | tee -a "$log_file"
    echo "$out3" | tee -a "$log_file"

    local usage3
    usage3="$(echo "$out3" | jq -r '.usage // "N/A"' 2>/dev/null || echo "N/A")"
    log "発話3 usage: $usage3" | tee -a "$log_file"

    # --- §U3 判定: 観測トークン出現確認 ---
    local u3_verdict
    if echo "$out3" | grep -q "$OBSERVATION_TOKEN"; then
        u3_verdict="PASS (${OBSERVATION_TOKEN} 発見)"
    else
        u3_verdict="FAIL (${OBSERVATION_TOKEN} 未検出)"
    fi
    log "§U3 履歴継承: $u3_verdict" | tee -a "$log_file"

    local total_duration=$(( t1_duration + t2_duration + t3_duration ))
    log "=== 実験終了: $mode | 合計実行時間: ${total_duration}ms ===" | tee -a "$log_file"
    log "ログ出力先: $log_file"
    echo ""
}

# メイン
MODE="${1:---both}"

case "$MODE" in
    --help|-h)
        usage
        ;;
    --with-bare)
        run_session "with_bare"
        ;;
    --without-bare)
        run_session "without_bare"
        ;;
    --both)
        # --bare あり を先に実行（比較基準を先に固めるため）
        run_session "with_bare"
        run_session "without_bare"
        ;;
    *)
        echo "Error: 不明なオプション '$MODE'" >&2
        echo "使用方法: $0 [--with-bare|--without-bare|--both]" >&2
        exit 1
        ;;
esac
