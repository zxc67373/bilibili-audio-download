@echo off
chcp 65001 >nul
title Bilibili 音频下载器

echo ========================================
echo   Bilibili 音频下载器
echo ========================================
echo.

REM 检查 FFmpeg
where ffmpeg >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: FFmpeg 未安装
    echo 请先安装 FFmpeg:
    echo   Windows: choco install ffmpeg
    echo   或从 https://ffmpeg.org/download.html 下载
    pause
    exit /b 1
)

echo ✓ FFmpeg 已安装
echo.

REM 切换到 app 目录
cd /d "%~dp0app"

echo 启动服务中...
echo 访问地址: http://localhost:8000
echo 按 Ctrl+C 停止服务
echo.

uvicorn main:app --host 0.0.0.0 --port 8000 --reload