"""
Bilibili 视频音频下载器 - FastAPI 后端
"""

import os
import json
import asyncio
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

from fastapi import FastAPI, HTTPException, Form, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from urllib.parse import quote
import uuid

import yt_dlp
from downloader import task_manager, downloader


# 配置日志
BASE_DIR = Path(__file__).parent
LOG_DIR = BASE_DIR.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 创建统一的 logger
def setup_logger(name: str) -> logging.Logger:
    """创建带请求ID支持的 logger"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    # 控制台 handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s',
        defaults={'request_id': '-'}
    )
    console_handler.setFormatter(console_formatter)

    # 文件 handler - 按天分割，保留 7 天
    file_handler = TimedRotatingFileHandler(
        LOG_DIR / "app.log",
        when='midnight',
        interval=1,
        backupCount=7,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s'
    )
    file_handler.setFormatter(file_formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

# 使用 custom filter 添加 request_id
class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = getattr(record, 'request_id', '-')
        return True

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 检查是否已配置过
if not logger.handlers:
    # 控制台 handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(request_id)s] - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(RequestIdFilter())

    # 文件 handler - 按天分割，保留 7 天
    file_handler = TimedRotatingFileHandler(
        LOG_DIR / "app.log",
        when='midnight',
        interval=1,
        backupCount=7,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(request_id)s] - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    file_handler.addFilter(RequestIdFilter())

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.propagate = False


# 创建 FastAPI 应用
app = FastAPI(
    title="Bilibili 音频下载器",
    description="从Bilibili视频下载音频",
    version="1.0.0"
)


# 应用启动事件
@app.on_event("startup")
async def startup_event():
    logger.info(f"服务启动，日志目录: {LOG_DIR}")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 获取项目根目录
BASE_DIR = Path(__file__).parent
DOWNLOADS_DIR = BASE_DIR / "downloads"
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
COVERS_DIR = DOWNLOADS_DIR / "covers"
COVERS_DIR.mkdir(parents=True, exist_ok=True)

# 配置静态文件
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.mount("/covers", StaticFiles(directory=str(COVERS_DIR)), name="covers")


@app.get("/", response_class=HTMLResponse)
async def index():
    """主页 - 返回 Web 界面"""
    html_file = BASE_DIR / "templates" / "index.html"
    return HTMLResponse(content=html_file.read_text(encoding='utf-8'))


@app.post("/download")
async def start_download(url: str = Form(...), request: Request = None):
    """
    启动下载任务

    Args:
        url: Bilibili 视频链接
        request: 请求对象，用于获取客户端信息

    Returns:
        task_id: 任务ID，用于查询进度
    """
    # 获取客户端 IP
    client_ip = request.client.host if request else "unknown"
    req_id = str(uuid.uuid4())[:8]

    # 验证 URL
    if not url or not url.strip():
        logger.warning(f"[{req_id}] 下载失败: 空的URL, 客户端: {client_ip}")
        raise HTTPException(status_code=400, detail="请输入视频链接")

    url = url.strip()

    # 简单的 URL 验证
    if 'bilibili.com' not in url and 'b23.tv' not in url:
        logger.warning(f"[{req_id}] 下载失败: 无效的URL - {url}, 客户端: {client_ip}")
        raise HTTPException(status_code=400, detail="请输入有效的Bilibili视频链接")

    # 创建任务
    task_id = task_manager.create_task()
    logger.info(f"[{req_id}] ========== 新建下载任务 ==========")
    logger.info(f"[{req_id}] 任务ID: {task_id}")
    logger.info(f"[{req_id}] 客户端IP: {client_ip}")
    logger.info(f"[{req_id}] 视频URL: {url}")

    # 在后台线程中执行下载（不阻塞异步循环）
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, downloader.download, url, task_id)

    logger.info(f"[{req_id}] 任务已加入队列，等待下载完成...")
    return {"task_id": task_id, "message": "下载任务已启动"}


@app.get("/search")
async def search_bilibili(keyword: str, request: Request = None):
    """
    搜索 Bilibili 视频

    Args:
        keyword: 搜索关键词
        request: 请求对象

    Returns:
        搜索结果列表
    """
    client_ip = request.client.host if request else "unknown"
    req_id = str(uuid.uuid4())[:8]

    if not keyword or not keyword.strip():
        logger.warning(f"[{req_id}] 搜索失败: 空的关键词, 客户端: {client_ip}")
        raise HTTPException(status_code=400, detail="请输入搜索关键词")

    keyword = keyword.strip()
    logger.info(f"[{req_id}] 搜索请求: {keyword}, 客户端: {client_ip}")

    try:
        import httpx
        import re
        from urllib.parse import quote

        async def search_with_cookies():
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, trust_env=False) as client:
                # 1. 先访问 B站首页获取 cookies
                await client.get("https://www.bilibili.com")

                # 2. 携带 cookies 搜索
                search_url = "https://api.bilibili.com/x/web-interface/search/all/v2"
                encoded_keyword = quote(keyword)
                params = {
                    "keyword": keyword,
                    "page": 1,
                    "page_size": 20,
                }
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    "Referer": f"https://www.bilibili.com",
                }

                response = await client.get(search_url, params=params, headers=headers)
                data = response.json()

                if data.get("code") != 0:
                    logger.error(f"[{req_id}] 搜索 API 错误: {data.get('message')}")
                    return {"results": []}

                # 3. 解析结果 - result 数组包含各类型模块，找到 video 模块
                result_modules = data.get("data", {}).get("result", [])

                # 找到 video 类型的模块
                video_module = None
                for module in result_modules:
                    if module.get("result_type") == "video":
                        video_module = module
                        break

                if not video_module:
                    logger.warning(f"[{req_id}] 未找到 video 模块")
                    return {"results": []}

                video_list = video_module.get("data", [])
                logger.info(f"[{req_id}] 视频数量: {len(video_list)}")

                result_list = []
                for item in video_list:
                    # 获取 arcurl
                    arcurl = item.get("arcurl", "")
                    bvid = item.get("bvid", "")

                    # 如果没有 arcurl，尝试用 bvid 构造
                    if not arcurl and bvid:
                        arcurl = f"https://www.bilibili.com/video/{bvid}"

                    # 如果还是没有有效 URL，跳过
                    if not arcurl or arcurl == "https://www.bilibili.com/video/":
                        continue

                    # 提取视频信息
                    title = item.get("title", "")
                    title = re.sub(r'<[^>]*>', '', title)  # 移除 HTML

                    # 封面 URL 修正
                    pic = item.get("pic", "")
                    if pic.startswith("//"):
                        pic = "https:" + pic

                    result_list.append({
                        "aid": item.get("aid", ""),
                        "title": title,
                        "pic": pic,
                        "author": item.get("author", ""),
                        "duration": item.get("duration", ""),
                        "description": item.get("description", ""),
                        "bvid": bvid,
                        "arcurl": arcurl,
                        "url": arcurl
                    })

                logger.info(f"[{req_id}] 解析后结果数量: {len(result_list)}")
                if result_list:
                    logger.info(f"[{req_id}] 示例 URL: {result_list[0]['url']}")
                return result_list

        result_list = await search_with_cookies()
        logger.info(f"[{req_id}] 搜索成功，返回 {len(result_list)} 条结果")
        return {"results": result_list}

    except httpx.TimeoutException:
        logger.error(f"[{req_id}] 搜索超时")
        raise HTTPException(status_code=504, detail="搜索超时，请重试")
    except Exception as e:
        logger.error(f"[{req_id}] 搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@app.get("/progress/{task_id}")
async def get_progress(task_id: str, request: Request = None):
    """
    SSE 端点 - 推送下载进度

    Args:
        task_id: 任务ID
        request: 请求对象

    Yields:
        JSON 格式的进度数据
    """
    client_ip = request.client.host if request else "unknown"
    logger.info(f"[{task_id}] 进度查询请求, 客户端: {client_ip}")

    async def event_generator():
        last_progress = -1
        check_count = 0
        max_checks = 300  # 最多等待 5 分钟 (300 * 1s)

        while check_count < max_checks:
            task = task_manager.get_task(task_id)

            if not task:
                yield "data: {\"error\": \"任务不存在\"}\n\n"
                break

            status = task.get('status', '')

            # 只有进度变化时才发送，避免前端接收过多重复数据
            current_progress = task.get('progress', 0)
            if current_progress != last_progress or status in ['complete', 'error']:
                last_progress = current_progress

                data = {
                    "status": status,
                    "progress": task.get('progress', 0),
                    "message": task.get('message', ''),
                    "filename": task.get('filename'),
                    "error": task.get('error'),
                }
                yield f"data: {json.dumps(data)}\n\n"

            # 如果任务完成或出错，发送完成后退出
            if status in ['complete', 'error']:
                break

            await asyncio.sleep(1)
            check_count += 1

        # 超时
        if check_count >= max_checks:
            yield "data: {\"status\": \"error\", \"message\": \"任务超时\"}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.get("/download/{filename}")
async def download_file(filename: str, request: Request = None):
    """
    下载完成的音频文件 / 在线播放音频

    Args:
        filename: 文件名
        request: 请求对象

    Returns:
        文件流
    """
    client_ip = request.client.host if request else "unknown"
    range_header = request.headers.get("Range", None)

    # 安全检查：防止路径遍历攻击
    filename = filename.replace("..", "").replace("/", "").replace("\\", "")

    file_path = DOWNLOADS_DIR / filename

    if not file_path.exists():
        logger.warning(f"[{filename}] 文件不存在, 客户端: {client_ip}")
        raise HTTPException(status_code=404, detail="文件不存在")

    # 获取文件大小
    file_size = file_path.stat().st_size

    # 根据 Range header 判断是在线播放还是下载
    if range_header:
        logger.info(f"[{filename}] 🎵 在线播放请求, 客户端: {client_ip}, Range: {range_header[:50]}...")
    else:
        logger.info(f"[{filename}] 📥 文件下载请求, 客户端: {client_ip}, 大小: {file_size / 1024 / 1024:.2f} MB")

    def iter_file():
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                yield chunk

    return StreamingResponse(
        iter_file(),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}",
            "Content-Length": str(file_size),
        }
    )


@app.get("/files")
async def list_files(request: Request = None):
    """列出已下载的文件"""
    client_ip = request.client.host if request else "unknown"
    logger.info(f"[/files] 文件列表请求, 客户端: {client_ip}")

    files = []
    for f in DOWNLOADS_DIR.glob("*.mp3"):
        # 检查是否有对应的封面
        cover_name = f.stem + "_cover.jpg"
        cover_path = COVERS_DIR / cover_name
        has_cover = cover_path.exists()

        # 没有匹配封面时使用默认封面
        if not has_cover:
            cover_name = "default_cover.jpg"

        files.append({
            "name": f.name,
            "size": f.stat().st_size,
            "modified": f.stat().st_mtime,
            "cover": f"/covers/{cover_name}"
        })
    # 按修改时间排序，最新的在前
    files.sort(key=lambda x: x['modified'], reverse=True)
    logger.info(f"[/files] 返回 {len(files)} 个文件")
    return {"files": files}


@app.delete("/files/{filename}")
async def delete_file(filename: str, request: Request = None):
    """删除文件"""
    client_ip = request.client.host if request else "unknown"

    # FastAPI 已经自动解码了 URL 参数，不要重复解码
    # 否则会导致双重解码破坏中文字符

    filename = filename.replace("..", "").replace("/", "").replace("\\", "")
    file_path = DOWNLOADS_DIR / filename

    logger.info(f"[{filename}] 删除文件请求, 客户端: {client_ip}")

    # 如果精确匹配找不到，尝试模糊匹配（处理省略号、编码问题等）
    if not file_path.exists():
        # 获取所有文件，尝试匹配
        all_files = list(DOWNLOADS_DIR.glob("*.mp3")) + list(DOWNLOADS_DIR.glob("*.m4a"))
        matched_file = None

        # 尝试多种匹配方式
        for f in all_files:
            # 1. 精确匹配
            if f.name == filename:
                matched_file = f
                break
            # 2. 只比较名称部分（不含扩展名）
            if f.stem == Path(filename).stem:
                matched_file = f
                logger.info(f"[{filename}] 模糊匹配成功 (stem): {f.name}")
                break
            # 3. 名称包含关系
            if filename in f.name or f.name in filename:
                matched_file = f
                logger.info(f"[{filename}] 模糊匹配成功 (contains): {f.name}")
                break
            # 4. 处理特殊字符变体
            stem = Path(filename).stem
            if stem in f.stem or f.stem in stem:
                matched_file = f
                logger.info(f"[{filename}] 模糊匹配成功 (stem contains): {f.name}")
                break

        if matched_file:
            file_path = matched_file
            filename = matched_file.name
            logger.info(f"[{filename}] 使用匹配的文件路径: {file_path}")

    if not file_path.exists():
        logger.warning(f"[{filename}] 删除失败: 文件不存在")
        raise HTTPException(status_code=404, detail=f"文件不存在: {filename}")

    # 同时删除对应的封面图片
    cover_name = Path(filename).stem + "_cover.jpg"
    cover_path = COVERS_DIR / cover_name
    if cover_path.exists():
        cover_path.unlink()
        logger.info(f"[{filename}] 封面已删除: {cover_name}")

    file_path.unlink()
    logger.info(f"[{filename}] 文件已删除")
    return {"message": "文件已删除"}


# ========== 歌单管理接口 ==========

PLAYLISTS_FILE = BASE_DIR / "playlists.json"

def load_playlists() -> list:
    """从文件加载歌单数据"""
    if PLAYLISTS_FILE.exists():
        try:
            return json.loads(PLAYLISTS_FILE.read_text(encoding='utf-8'))
        except:
            return []
    return []

def save_playlists(playlists: list):
    """保存歌单数据到文件"""
    PLAYLISTS_FILE.write_text(json.dumps(playlists, ensure_ascii=False, indent=2), encoding='utf-8')

@app.get("/playlists")
async def get_playlists():
    """获取所有歌单"""
    logger.info("[/playlists] 获取歌单列表")
    playlists = load_playlists()
    return {"playlists": playlists}

@app.post("/playlists")
async def create_playlist(name: str = Form(...)):
    """创建新歌单"""
    req_id = str(uuid.uuid4())[:8]
    logger.info(f"[{req_id}] 创建歌单: {name}")

    playlists = load_playlists()
    new_playlist = {
        "id": "playlist_" + str(uuid.uuid4())[:8],
        "name": name,
        "songs": [],
        "createdAt": datetime.now().isoformat()
    }
    playlists.append(new_playlist)
    save_playlists(playlists)

    return {"playlist": new_playlist}

@app.put("/playlists/{playlist_id}")
async def update_playlist(playlist_id: str, name: str = Form(...)):
    """更新歌单名称"""
    req_id = str(uuid.uuid4())[:8]
    logger.info(f"[{req_id}] 更新歌单: {playlist_id} -> {name}")

    playlists = load_playlists()
    for p in playlists:
        if p["id"] == playlist_id:
            p["name"] = name
            save_playlists(playlists)
            return {"playlist": p}

    raise HTTPException(status_code=404, detail="歌单不存在")

@app.delete("/playlists/{playlist_id}")
async def delete_playlist(playlist_id: str):
    """删除歌单"""
    req_id = str(uuid.uuid4())[:8]
    logger.info(f"[{req_id}] 删除歌单: {playlist_id}")

    playlists = load_playlists()
    playlists = [p for p in playlists if p["id"] != playlist_id]
    save_playlists(playlists)

    return {"message": "歌单已删除"}

@app.post("/playlists/{playlist_id}/songs")
async def add_songs_to_playlist(playlist_id: str, songs: str = Form(...)):
    """添加歌曲到歌单"""
    req_id = str(uuid.uuid4())[:8]
    logger.info(f"[{req_id}] 添加歌曲到歌单: {playlist_id}")

    import json
    song_list = json.loads(songs)

    playlists = load_playlists()
    for p in playlists:
        if p["id"] == playlist_id:
            for song in song_list:
                if song not in p["songs"]:
                    p["songs"].append(song)
            save_playlists(playlists)
            return {"playlist": p}

    raise HTTPException(status_code=404, detail="歌单不存在")

@app.delete("/playlists/{playlist_id}/songs")
async def remove_song_from_playlist(playlist_id: str, song: str = Form(...)):
    """从歌单移除歌曲"""
    req_id = str(uuid.uuid4())[:8]
    logger.info(f"[{req_id}] 从歌单移除歌曲: {playlist_id} - {song}")

    playlists = load_playlists()
    for p in playlists:
        if p["id"] == playlist_id:
            if song in p["songs"]:
                p["songs"].remove(song)
            save_playlists(playlists)
            return {"playlist": p}

    raise HTTPException(status_code=404, detail="歌单不存在")


if __name__ == "__main__":
    import uvicorn
    logger.info(f"服务启动，日志目录: {LOG_DIR}")
    uvicorn.run(app, host="0.0.0.0", port=8000)