#!/bin/bash
CAT=$(cat .claude/CURRENT_CATEGORY 2>/dev/null || echo app)
MODE="${1:-latest}"  # latest | major | next-minor | next-major

# 全バージョンを取得（旧形式 ver12 と新形式 ver13.0 の両方に対応）
ALL=$(ls -1d "docs/$CAT/ver"*/ 2>/dev/null | sed 's|.*/ver||;s|/||' | sort -t. -k1,1n -k2,2n)

case "$MODE" in
  latest)
    # 最新バージョン（形式問わず）
    echo "${ALL}" | tail -1 | tr -d '[:space:]'
    ;;
  major)
    # 最新のメジャーバージョン（X.0 または旧形式の整数）
    echo "${ALL}" | grep -E '^[0-9]+$|\.0$' | tail -1 | tr -d '[:space:]'
    ;;
  next-minor)
    # 次のマイナーバージョン番号を提案
    LATEST=$(echo "${ALL}" | tail -1 | tr -d '[:space:]')
    if echo "$LATEST" | grep -q '\.'; then
      MAJOR=$(echo "$LATEST" | cut -d. -f1)
      MINOR=$(echo "$LATEST" | cut -d. -f2)
      echo "${MAJOR}.$((MINOR + 1))"
    else
      # 旧形式からの移行: 次のメジャー番号.1
      echo "$((LATEST + 1)).1"
    fi
    ;;
  next-major)
    # 次のメジャーバージョン番号を提案
    LATEST=$(echo "${ALL}" | tail -1 | tr -d '[:space:]')
    if echo "$LATEST" | grep -q '\.'; then
      MAJOR=$(echo "$LATEST" | cut -d. -f1)
      echo "$((MAJOR + 1)).0"
    else
      echo "$((LATEST + 1)).0"
    fi
    ;;
  *)
    echo "Usage: $0 [latest|major|next-minor|next-major]" >&2
    exit 1
    ;;
esac
