#!/usr/bin/env python3
"""Bilibili 音频下载测试脚本 - 直接在命令行测试下载功能"""

import sys
import os

# 添加 app 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.downloader import downloader, task_manager


def test_download(url: str):
    """测试下载"""
    print(f"测试下载: {url}")
    print("=" * 50)

    # 创建任务
    task_id = task_manager.create_task()
    print(f"任务ID: {task_id}")

    # 执行下载
    filename = downloader.download(url, task_id)

    # 获取最终状态
    task = task_manager.get_task(task_id)
    print(f"\n最终状态:")
    print(f"  状态: {task.get('status')}")
    print(f"  消息: {task.get('message')}")
    print(f"  文件名: {task.get('filename')}")
    print(f"  错误: {task.get('error')}")

    return filename


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python test_download.py <Bilibili视频链接>")
        print("示例: python test_download.py https://www.bilibili.com/video/BV1xx411c7mD")
        sys.exit(1)

    url = sys.argv[1]
    test_download(url)