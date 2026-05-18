#!/usr/bin/env python3
"""Bilibili 音频下载测试"""

import sys
import os

# 确保可以导入 app 模块
sys.path.insert(0, os.path.dirname(__file__))

from app.downloader import Downloader


def main():
    if len(sys.argv) < 2:
        print("用法: python test.py <Bilibili视频链接>")
        print("示例: python test.py https://www.bilibili.com/video/BV1xx411c7mD")
        sys.exit(1)

    url = sys.argv[1]
    print(f"下载: {url}\n")

    downloader = Downloader("app/downloads")
    result = downloader.download(url, task_id="test-001")

    if result:
        print(f"\n✓ 下载成功: {result}")
        print(f"文件位置: app/downloads/{result}")
    else:
        print("\n✗ 下载失败")


if __name__ == "__main__":
    main()