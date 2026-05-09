#!/usr/bin/env bash
set -e

# 用法：bash push_to_github.sh your-github-username dq-quality-agent
GITHUB_USER=${1:-your-github-username}
REPO_NAME=${2:-dq-quality-agent}

if [ "$GITHUB_USER" = "your-github-username" ]; then
  echo "请传入你的 GitHub 用户名，例如：bash push_to_github.sh wenxiaofeng dq-quality-agent"
  exit 1
fi

git init
git add .
git commit -m "Initial commit: Hive data quality inspection agent"
git branch -M main
git remote add origin "https://github.com/${GITHUB_USER}/${REPO_NAME}.git"
git push -u origin main
