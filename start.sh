#!/bin/bash

# Bilibili 音频下载器启动脚本

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}  Bilibili 音频下载器${NC}"
echo -e "${GREEN}=========================================${NC}"

# 检查 FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${RED}错误: FFmpeg 未安装${NC}"
    echo "请先安装 FFmpeg:"
    echo "  Ubuntu/Debian: sudo apt install ffmpeg"
    echo "  macOS: brew install ffmpeg"
    echo "  Windows: choco install ffmpeg"
    exit 1
fi

echo -e "${YELLOW}✓ FFmpeg 已安装${NC}"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: Python3 未安装${NC}"
    exit 1
fi

echo -e "${YELLOW}✓ Python3 已安装${NC}"

# 切换到 app 目录
cd "$(dirname "$0")/app" || exit 1

# 启动服务
echo ""
echo -e "${GREEN}启动服务中...${NC}"
echo -e "访问地址: ${YELLOW}http://localhost:8000${NC}"
echo -e "按 ${YELLOW}Ctrl+C${NC} 停止服务"
echo ""

exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload