#!/bin/bash
# Typeless AI Service - GitHub推送脚本
# 使用方法：./push_to_github.sh <your_github_username>

if [ -z "$1" ]; then
    echo "错误：请提供GitHub用户名"
    echo "用法: $0 <github_username>"
    echo ""
    echo "示例: $0 harvietse"
    exit 1
fi

USERNAME="$1"
TOKEN="githubpat11BWC5YZQ0JRU2XAp5kIyU_REo70la4OSn8sQUp7xb24oIFMGRDPc5Np8xgRBJX49qCMPMDLAKN1M5VESQ"
REPO="typeless-ai-service"

echo "=== 配置Git远程仓库 ==="
git remote remove origin 2>/dev/null
git remote add origin https://${TOKEN}@github.com/${USERNAME}/${REPO}.git

echo "=== 推送代码到GitHub ==="
GIT_TERMINAL_PROMPT=0 git push -u origin main 2>&1

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 推送成功！"
    echo "仓库地址: https://github.com/${USERNAME}/${REPO}"
else
    echo ""
    echo "❌ 推送失败，请检查："
    echo "   1. 用户名是否正确: ${USERNAME}"
    echo "   2. 仓库是否已创建: https://github.com/${USERNAME}/${REPO}"
    echo "   3. Token权限是否足够"
fi
