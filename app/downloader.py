"""
Bilibili视频音频下载核心模块
"""

import os
import uuid
import json
import logging
import threading
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

import yt_dlp

# 配置日志 - 继承 main.py 的配置
logger = logging.getLogger(__name__)


class TaskManager:
    """下载任务管理器"""

    def __init__(self, download_dir: str = "downloads"):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def create_task(self) -> str:
        """创建新任务"""
        task_id = str(uuid.uuid4())
        with self._lock:
            self._tasks[task_id] = {
                "id": task_id,
                "status": "pending",
                "progress": 0,
                "message": "等待开始",
                "filename": None,
                "error": None,
                "created_at": datetime.now().isoformat(),
            }
        return task_id

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        with self._lock:
            return self._tasks.get(task_id, {}).copy()

    def update_task(self, task_id: str, **kwargs):
        """更新任务状态"""
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].update(kwargs)

    def remove_task(self, task_id: str):
        """移除任务"""
        with self._lock:
            self._tasks.pop(task_id, None)


# 全局任务管理器
task_manager = TaskManager()


class Downloader:
    """音频下载器"""

    def __init__(self, download_dir: str = "downloads"):
        # 使用绝对路径
        if not Path(download_dir).is_absolute():
            self.download_dir = Path(__file__).parent / download_dir
        else:
            self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        # 封面文件夹放在 downloads 目录下
        self.covers_dir = self.download_dir / "covers"
        self.covers_dir.mkdir(parents=True, exist_ok=True)

    def _progress_hook(self, task_id: str):
        """创建进度回调函数"""

        def hook(d: dict):
            if d['status'] == 'downloading':
                # 计算下载进度
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded = d.get('downloaded_bytes', 0)
                percent = (downloaded / total * 100) if total > 0 else 0

                speed = d.get('speed', 0)
                speed_str = ""
                if speed:
                    speed_mb = speed / 1024 / 1024
                    speed_str = f" {speed_mb:.2f} MB/s"

                task_manager.update_task(
                    task_id,
                    status='downloading',
                    progress=percent,
                    message=f"下载中... {percent:.1f}%{speed_str}"
                )

            elif d['status'] == 'finished':
                task_manager.update_task(
                    task_id,
                    status='converting',
                    progress=90,
                    message="正在转换为MP3..."
                )

            elif d['status'] == 'error':
                task_manager.update_task(
                    task_id,
                    status='error',
                    progress=0,
                    message=f"下载失败: {d.get('error', '未知错误')}",
                    error=d.get('error', '未知错误')
                )

        return hook

    def download(self, url: str, task_id: str) -> Optional[str]:
        """
        下载视频音频

        Args:
            url: Bilibili视频链接
            task_id: 任务ID

        Returns:
            成功返回文件名，失败返回None
        """
        import subprocess

        logger.info(f"[{task_id}] ========== 开始下载流程 ==========")
        logger.info(f"[{task_id}] 任务ID: {task_id}")
        logger.info(f"[{task_id}] 视频URL: {url}")

        # 先获取视频信息（包括封面）
        with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True, 'skip_download': True}) as ydl_pre:
            info = ydl_pre.extract_info(url, download=False)
            title = info.get('title', 'unknown')
            title = self._sanitize_filename(title)
            # 获取封面 URL
            thumbnail_url = info.get('thumbnail')
            video_duration = info.get('duration', 0)
            video_uploader = info.get('uploader', 'unknown')

        logger.info(f"[{task_id}] ========== 视频信息解析完成 ==========")
        logger.info(f"[{task_id}] 视频标题: {title}")
        logger.info(f"[{task_id}] 视频作者: {video_uploader}")
        logger.info(f"[{task_id}] 视频时长: {video_duration} 秒")
        logger.info(f"[{task_id}] 封面URL: {thumbnail_url}")
        logger.info(f"[{task_id}] 下载目录: {self.download_dir}")
        logger.info(f"[{task_id}] 封面目录: {self.covers_dir}")

        task_manager.update_task(
            task_id,
            status='downloading',
            progress=0,
            message=f"正在下载: {title}"
        )

        logger.info(f"[{task_id}] 开始下载音频...")

        # 下载音频（不转换，用 m4a 格式）
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': str(self.download_dir / f'{title}.%(ext)s'),
            'progress_hooks': [self._progress_hook(task_id)],
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'extractor_retries': 3,
            'fragment_retries': 3,
            'skip_unavailable_fragments': False,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # 查找下载的音频文件
            audio_files = list(self.download_dir.glob(f'{title}.*'))
            if not audio_files:
                raise Exception("音频文件下载失败")

            audio_path = audio_files[0]
            audio_size = audio_path.stat().st_size
            mp3_path = self.download_dir / f"{title}.mp3"

            logger.info(f"[{task_id}] 音频下载完成!")
            logger.info(f"[{task_id}] 临时音频文件: {audio_path.name}")
            logger.info(f"[{task_id}] 临时音频大小: {audio_size} bytes ({audio_size / 1024 / 1024:.2f} MB)")

            # 下载封面到 covers 文件夹
            thumbnail_path = None
            if thumbnail_url:
                try:
                    import urllib.request
                    # 保存到 covers 文件夹
                    thumbnail_path = self.covers_dir / f"{title}_cover.jpg"
                    logger.info(f"[{task_id}] 开始下载封面...")
                    logger.info(f"[{task_id}] 封面保存路径: {thumbnail_path}")
                    urllib.request.urlretrieve(thumbnail_url, str(thumbnail_path))
                    if thumbnail_path.exists():
                        file_size = thumbnail_path.stat().st_size
                        logger.info(f"[{task_id}] ✅ 封面下载成功!")
                        logger.info(f"[{task_id}] 封面文件名: {thumbnail_path.name}")
                        logger.info(f"[{task_id}] 封面大小: {file_size} bytes ({file_size / 1024:.1f} KB)")
                    else:
                        logger.warning(f"[{task_id}] ⚠️ 封面文件未找到: {thumbnail_path}")
                    task_manager.update_task(task_id, message="正在添加封面...")
                except Exception as e:
                    logger.error(f"[{task_id}] ❌ 封面下载失败: {e}")
                    thumbnail_path = None
            else:
                logger.warning(f"[{task_id}] ⚠️ 视频无封面")

            # 使用 FFmpeg 转换为 MP3（不再嵌入封面，封面单独保存在 covers 目录）
            logger.info(f"[{task_id}] ========== 开始转换MP3 ==========")
            logger.info(f"[{task_id}] 输入文件: {audio_path}")
            logger.info(f"[{task_id}] 输出文件: {mp3_path}")
            logger.info(f"[{task_id}] 音频码率: 192kbps")

            cmd = [
                'ffmpeg', '-y', '-i', str(audio_path),
                '-ab', '192k', str(mp3_path)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"[{task_id}] ❌ FFmpeg转换失败!")
                logger.error(f"[{task_id}] 错误信息: {result.stderr}")
                raise Exception(f"FFmpeg转换失败: {result.stderr}")
            else:
                logger.info(f"[{task_id}] ✅ MP3转换成功!")

            # 清理临时文件（只删除原始音频，保留封面）
            if audio_path.exists():
                audio_path.unlink()
                logger.info(f"[{task_id}] 清理临时音频文件: {audio_path.name}")

            if mp3_path.exists():
                file_size = mp3_path.stat().st_size
                logger.info(f"[{task_id}] ========== 下载完成! ==========")
                logger.info(f"[{task_id}] ✅ MP3文件生成成功!")
                logger.info(f"[{task_id}] 文件名: {mp3_path.name}")
                logger.info(f"[{task_id}] 文件大小: {file_size} bytes ({file_size / 1024 / 1024:.2f} MB)")
                logger.info(f"[{task_id}] 文件路径: {mp3_path}")

                # 封面状态
                if thumbnail_path and thumbnail_path.exists():
                    logger.info(f"[{task_id}] 封面状态: ✅ 已保存")
                    logger.info(f"[{task_id}] 封面路径: {thumbnail_path}")
                else:
                    logger.info(f"[{task_id}] 封面状态: ⚠️ 无封面")

                logger.info(f"[{task_id}] ========== 任务结束 ==========")

                task_manager.update_task(
                    task_id,
                    status='complete',
                    progress=100,
                    message="下载完成!",
                    filename=mp3_path.name
                )
                return mp3_path.name
            else:
                raise Exception("MP3 转换失败")

        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)
            logger.error(f"[{task_id}] ❌ 下载失败 (yt-dlp error)")
            logger.error(f"[{task_id}] 错误信息: {error_msg}")
            task_manager.update_task(
                task_id,
                status='error',
                message=f"下载失败: {error_msg}",
                error=error_msg
            )
            return None

        except Exception as e:
            error_msg = str(e)
            logger.error(f"[{task_id}] ❌ 发生错误")
            logger.error(f"[{task_id}] 错误类型: {type(e).__name__}")
            logger.error(f"[{task_id}] 错误信息: {error_msg}")
            import traceback
            logger.error(f"[{task_id}] 堆栈跟踪:\n{traceback.format_exc()}")
            task_manager.update_task(
                task_id,
                status='error',
                message=f"错误: {error_msg}",
                error=error_msg
            )
            return None

    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名中的非法字符"""
        # Windows/Mac/Linux 不允许的字符
        illegal_chars = '<>:"/\\|?*'
        for char in illegal_chars:
            filename = filename.replace(char, '_')

        # 限制长度
        if len(filename) > 100:
            filename = filename[:100]

        return filename.strip()


# 创建全局下载器实例
downloader = Downloader()