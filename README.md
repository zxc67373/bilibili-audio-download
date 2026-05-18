# Bilibili 音频下载器

从 Bilibili 视频下载音频文件的 Web 应用。

## 功能特性

- 🌐 Web 界面，无需安装客户端
- 📥 输入视频链接即可下载音频
- 📊 实时显示下载进度
- 🎵 输出 MP3 格式（192kbps）
- 🔍 搜索 Bilibili 视频并下载
- 📂 已下载文件管理（查看、播放、下载、删除）
- 🎧 在线播放器，支持上一首/下一首
- 📋 歌单功能，创建和管理播放列表

## 环境要求

- Python 3.8+
- FFmpeg（用于音频转换）

## 安装步骤

### 1. 安装 FFmpeg

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows (使用 Chocolatey)
choco install ffmpeg
```

### 2. 克隆项目

```bash
git clone https://github.com/你的用户名/bilibili-audio-downloader.git
cd bilibili-audio-downloader
```

### 3. 创建虚拟环境（推荐）

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 4. 安装依赖

```bash
pip install -r requirements.txt
```

## 启动服务

```bash
cd app
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

启动后，在浏览器中访问：`http://localhost:8000`

## 使用方法

### 下载音频

1. 打开浏览器访问 `http://localhost:8000`
2. 在输入框中粘贴 Bilibili 视频链接
3. 点击"开始下载"按钮
4. 等待下载完成，点击下载链接获取音频文件

### 搜索并下载

1. 在搜索框中输入关键词
2. 点击搜索按钮或按回车
3. 在搜索结果中点击"下载音频"

### 播放音乐

- 点击已下载文件列表中的任意文件即可播放
- 使用播放器控制按钮：上一首、播放/暂停、下一首
- 拖动进度条可调整播放位置
- 调整音量滑块控制音量

### 歌单管理

1. 在"我的歌单"区域输入歌单名称，点击"+"创建
2. 勾选多个文件后点击"添加到歌单"
3. 选择目标歌单即可

## 支持的链接格式

- 视频页面: `https://www.bilibili.com/video/BVxxxx`
- 短链接: `https://b23.tv/xxxx`
- 分享链接
- AV 号: `https://www.bilibili.com/video/avxxxxxx`

## 项目结构

```
bilibili-audio-downloader/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI 后端主程序
│   ├── downloader.py     # 下载核心逻辑
│   ├── playlists.json    # 歌单数据（本地存储）
│   ├── templates/
│   │   └── index.html    # Web 界面
│   └── static/
│       ├── style.css     # 样式文件
│       ├── app.js        # 前端交互脚本
│       └── preview-style.css
├── downloads/            # 音频输出目录（不会被提交）
├── logs/                 # 日志目录（不会被提交）
├── requirements.txt      # Python 依赖
├── test.py              # 命令行测试脚本
└── README.md            # 项目文档
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | Web 界面 |
| POST | `/download` | 启动下载 |
| GET | `/progress/{task_id}` | 进度 SSE 流 |
| GET | `/download/{filename}` | 下载文件 |
| GET | `/files` | 文件列表 |
| DELETE | `/files/{filename}` | 删除文件 |
| GET | `/search` | 搜索视频 |
| GET | `/playlists` | 获取歌单列表 |
| POST | `/playlists` | 创建歌单 |
| PUT | `/playlists/{id}` | 重命名歌单 |
| DELETE | `/playlists/{id}` | 删除歌单 |
| POST | `/playlists/{id}/songs` | 添加歌曲到歌单 |
| DELETE | `/playlists/{id}/songs` | 从歌单移除歌曲 |

## 技术栈

- **后端**: FastAPI + Python
- **前端**: 原生 HTML + CSS + JavaScript
- **下载**: yt-dlp
- **音频转换**: FFmpeg

## 注意事项

- 请遵守 Bilibili 服务条款，仅下载允许的内容
- 仅供个人学习研究使用
- 尊重内容创作者版权
- 部分高画质视频需要登录账号才能下载

## 常见问题

### FFmpeg 未找到

确保 FFmpeg 已正确安装并添加到系统 PATH：

```bash
ffmpeg -version
```

### 下载失败

1. 检查网络连接
2. 确保视频是否可访问
3. 尝试更新 yt-dlp：`pip install -U yt-dlp`

### 端口被占用

修改启动端口：

```bash
uvicorn main:app --host 0.0.0.0 --port 8080
```

## 贡献

欢迎提交 Pull Request！

## 许可证

MIT License