/**
 * Bilibili 音频下载器 - 前端交互逻辑
 */

// DOM 元素
const downloadForm = document.getElementById('downloadForm');
const urlInput = document.getElementById('urlInput');
const downloadBtn = document.getElementById('downloadBtn');
const btnText = document.querySelector('.btn-text');
const btnLoading = document.querySelector('.btn-loading');
const progressContainer = document.getElementById('progressContainer');
const progressText = document.getElementById('progressText');
const progressPercent = document.getElementById('progressPercent');
const progressFill = document.getElementById('progressFill');
const resultContainer = document.getElementById('resultContainer');
const successText = document.getElementById('successText');
const downloadLink = document.getElementById('downloadLink');
const errorContainer = document.getElementById('errorContainer');
const errorText = document.getElementById('errorText');
const filesList = document.getElementById('filesList');

// 播放器元素
const playerSection = document.getElementById('playerSection');
const playerTitle = document.getElementById('playerTitle');
const playBtn = document.getElementById('playBtn');
const prevBtn = document.getElementById('prevBtn');
const nextBtn = document.getElementById('nextBtn');
const progressBar = document.getElementById('progressBar');
const volumeBar = document.getElementById('volumeBar');
const currentTimeEl = document.getElementById('currentTime');
const totalTimeEl = document.getElementById('totalTime');
const audioPlayer = document.getElementById('audioPlayer');
const vinylRecord = document.getElementById('vinylRecord');

// 歌单相关元素
const playlistSection = document.getElementById('playlistSection');
const playlistList = document.getElementById('playlistList');
const newPlaylistName = document.getElementById('newPlaylistName');
const createPlaylistBtn = document.getElementById('createPlaylistBtn');
const addToPlaylistBtn = document.getElementById('addToPlaylistBtn');
const selectAllCheckbox = document.getElementById('selectAll');

// 模态框元素
const playlistModal = document.getElementById('playlistModal');
const playlistModalList = document.getElementById('playlistModalList');
const closeModalBtn = document.getElementById('closeModalBtn');

// 搜索相关元素
const searchInput = document.getElementById('searchInput');
const searchBtn = document.getElementById('searchBtn');
const searchResults = document.getElementById('searchResults');

let eventSource = null;

// 歌单变量（区分用户歌单和播放列表）
let currentPlaylist = [];
let playlist = [];  // 文件列表
let currentIndex = -1;
let isPlaying = false;
let selectedFiles = new Set();
let userPlaylists = [];

// ========== 歌单功能（使用后端 API）==========

// 从服务器加载歌单
async function loadPlaylists() {
    try {
        const response = await fetch('/playlists');
        const data = await response.json();
        userPlaylists = data.playlists || [];
    } catch (e) {
        console.error('加载歌单失败:', e);
        userPlaylists = [];
    }
    return userPlaylists;
}

// 创建歌单
async function createPlaylist(name) {
    if (!name.trim()) {
        alert('请输入歌单名称');
        return false;
    }
    try {
        const response = await fetch('/playlists', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: `name=${encodeURIComponent(name.trim())}`
        });
        const data = await response.json();
        userPlaylists.push(data.playlist);
        renderPlaylists();
        return true;
    } catch (e) {
        console.error('创建歌单失败:', e);
        alert('创建歌单失败');
        return false;
    }
}

// 删除歌单
async function deletePlaylist(playlistId) {
    if (!confirm('确定要删除这个歌单吗？')) return;
    try {
        await fetch(`/playlists/${playlistId}`, { method: 'DELETE' });
        userPlaylists = userPlaylists.filter(p => p.id !== playlistId);
        renderPlaylists();
    } catch (e) {
        console.error('删除歌单失败:', e);
        alert('删除歌单失败');
    }
}

// 重命名歌单
async function renamePlaylist(playlistId) {
    const playlist = userPlaylists.find(p => p.id === playlistId);
    if (!playlist) return;
    const newName = prompt('请输入新名称:', playlist.name);
    if (newName && newName.trim()) {
        try {
            await fetch(`/playlists/${playlistId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `name=${encodeURIComponent(newName.trim())}`
            });
            playlist.name = newName.trim();
            renderPlaylists();
        } catch (e) {
            console.error('重命名歌单失败:', e);
            alert('重命名歌单失败');
        }
    }
}

// 添加歌曲到歌单
async function addSongsToPlaylist(playlistId, songNames) {
    const playlist = userPlaylists.find(p => p.id === playlistId);
    if (!playlist) return;
    try {
        await fetch(`/playlists/${playlistId}/songs`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: `songs=${encodeURIComponent(JSON.stringify(songNames))}`
        });
        for (const name of songNames) {
            if (!playlist.songs.includes(name)) {
                playlist.songs.push(name);
            }
        }
        alert(`已添加到歌单: ${playlist.name}`);
    } catch (e) {
        console.error('添加到歌单失败:', e);
        alert('添加到歌单失败');
    }
}

// 从歌单移除歌曲
async function removeSongFromPlaylist(playlistId, songName) {
    const userPlaylist = userPlaylists.find(p => p.id === playlistId);
    if (!userPlaylist) return;
    try {
        await fetch(`/playlists/${playlistId}/songs`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: `song=${encodeURIComponent(songName)}`
        });
        userPlaylist.songs = userPlaylist.songs.filter(s => s !== songName);
        renderPlaylists();
    } catch (e) {
        console.error('移除歌曲失败:', e);
    }
}

// 渲染歌单列表
function renderPlaylists() {
    // 始终显示歌单区域
    playlistSection.style.display = 'block';

    if (userPlaylists.length > 0) {
        playlistList.innerHTML = userPlaylists.map(p => `
            <div class="playlist-item" data-id="${p.id}">
                <div class="playlist-header-row" onclick="togglePlaylistDetail('${p.id}')">
                    <div class="playlist-info">
                        <span class="playlist-name">${escapeHtml(p.name)}</span>
                        <span class="playlist-count">${p.songs.length} 首</span>
                    </div>
                    <div class="playlist-actions">
                        <span class="playlist-toggle" id="toggle-${p.id}">▼</span>
                        <button onclick="event.stopPropagation(); renamePlaylist('${p.id}')" title="重命��">✏️</button>
                        <button onclick="event.stopPropagation(); deletePlaylist('${p.id}')" title="删除">🗑️</button>
                    </div>
                </div>
                <div class="playlist-detail" id="detail-${p.id}" style="display: none;">
                    ${renderPlaylistSongs(p)}
                </div>
            </div>
        `).join('');
    } else {
        playlistList.innerHTML = '<div class="empty-state">暂无歌单，请创建</div>';
    }
}

// 渲染歌单内的歌曲
function renderPlaylistSongs(userPlaylist) {
    if (!userPlaylist.songs || userPlaylist.songs.length === 0) {
        return '<div class="empty-state">歌单为空</div>';
    }

    // 如果文件列表还没加载，显示提示
    if (!playlist || playlist.length === 0) {
        return '<div class="empty-state">请等待文件加载完成</div>';
    }

    // 从全部文件中查找匹配的歌曲
    const songs = userPlaylist.songs
        .map(songName => playlist.find(f => f.name === songName))
        .filter(f => f);

    if (songs.length === 0) {
        return '<div class="empty-state">歌曲已不存在</div>';
    }

    return songs.map((file, idx) => `
        <div class="playlist-song-item" data-playlist-id="${userPlaylist.id}" data-song-index="${idx}">
            <div class="song-cover">
                ${file.cover ? `<img src="${file.cover}" alt="封面" onerror="this.style.display='none'">` : '<span class="file-icon">🎵</span>'}
            </div>
            <span class="song-name">${escapeHtml(file.name.replace('.mp3', ''))}</span>
            <button class="song-remove" data-playlist-id="${userPlaylist.id}" data-song-name="${escapeHtml(file.name)}" title="从歌单移除">✕</button>
        </div>
    `).join('');
}

// 展开/收起歌单详情
function togglePlaylistDetail(playlistId) {
    const detail = document.getElementById(`detail-${playlistId}`);
    const toggle = document.getElementById(`toggle-${playlistId}`);
    if (detail.style.display === 'none' || detail.style.display === '') {
        detail.style.display = 'block';
        // 等待一小段时间后添加展开类，触发动画
        setTimeout(() => detail.classList.add('expanded'), 10);
        toggle.style.transform = 'rotate(0deg)';
    } else {
        detail.classList.remove('expanded');
        setTimeout(() => {
            detail.style.display = 'none';
        }, 300); // 等待动画完成
        toggle.style.transform = 'rotate(-90deg)';
    }
}

// 播放歌单中的指定歌曲
function playPlaylistSong(playlistId, songIndex) {
    const userPlaylist = userPlaylists.find(p => p.id === playlistId);
    if (!userPlaylist || !userPlaylist.songs.length) return;

    const songs = userPlaylist.songs
        .map(songName => playlist.find(f => f.name === songName))
        .filter(f => f);

    if (songIndex >= 0 && songIndex < songs.length) {
        currentPlaylist = songs;
        currentIndex = songIndex;
        playTrack(songIndex);
    }
}

// 从歌单播放
function playPlaylist(playlistId) {
    const userPlaylist = userPlaylists.find(p => p.id === playlistId);
    if (!userPlaylist || userPlaylist.songs.length === 0) {
        alert('歌单为空');
        return;
    }
    // 从全部文件中查找匹配的歌曲
    const songs = userPlaylist.songs
        .map(songName => playlist.find(f => f.name === songName))
        .filter(f => f);

    if (songs.length > 0) {
        currentPlaylist = songs;
        currentIndex = 0;
        playTrack(0);
    } else {
        alert('歌单中的歌曲可能已被删除');
    }
}

// 获取选中的歌曲
function getSelectedSongs() {
    const checkboxes = filesList.querySelectorAll('.file-checkbox:checked');
    const songs = [];
    checkboxes.forEach(cb => {
        const index = parseInt(cb.dataset.index);
        if (playlist[index]) {
            songs.push(playlist[index].name);
        }
    });
    return songs;
}

// 更新多选按钮显示
function updateAddToPlaylistBtn() {
    const selected = getSelectedSongs();
    addToPlaylistBtn.style.display = selected.length > 0 ? 'inline-block' : 'none';
    addToPlaylistBtn.textContent = `添加到歌单 (${selected.length})`;
}

// 渲染文件列表（带多选）
function renderFilesList() {
    if (playlist.length > 0) {
        filesList.innerHTML = playlist.map((file, index) => `
            <div class="file-item ${index === currentIndex ? 'active' : ''}" data-index="${index}">
                <input type="checkbox" class="file-checkbox" data-index="${index}" onchange="updateAddToPlaylistBtn()">
                <div class="file-cover">
                    ${file.cover ? `<img src="${file.cover}" alt="封面" onerror="this.style.display='none'">` : '<span class="file-icon">🎵</span>'}
                </div>
                <div class="file-info">
                    <div class="file-details">
                        <div class="file-name">${escapeHtml(file.name.replace('.mp3', ''))}</div>
                        <div class="file-size">${formatFileSize(file.size)} · ${formatDate(file.modified)}</div>
                    </div>
                </div>
                <div class="file-actions">
                    <a href="/download/${encodeURIComponent(file.name)}" download>下载</a>
                    <button onclick="event.stopPropagation(); deleteFile('${file.name.replace(/'/g, "\\'")}')">删除</button>
                </div>
            </div>
        `).join('');

        // 添加点击播放事件
        document.querySelectorAll('.file-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (e.target.type === 'checkbox') return;
                const index = parseInt(item.dataset.index);
                playTrack(index);
            });
        });
    } else {
        filesList.innerHTML = '<div class="empty-state">暂无已下载文件</div>';
    }
}

// 全选功能
selectAllCheckbox.addEventListener('change', (e) => {
    const checkboxes = filesList.querySelectorAll('.file-checkbox');
    checkboxes.forEach(cb => {
        cb.checked = e.target.checked;
    });
    updateAddToPlaylistBtn();
});

// 创建歌单按钮
createPlaylistBtn.addEventListener('click', () => {
    const name = newPlaylistName.value;
    if (createPlaylist(name)) {
        newPlaylistName.value = '';
    }
});

// 添加到歌单按钮 - 显示模态框
addToPlaylistBtn.addEventListener('click', () => {
    const songs = getSelectedSongs();
    if (songs.length === 0) {
        alert('请先选择歌曲');
        return;
    }
    if (userPlaylists.length === 0) {
        alert('请先创建歌单');
        return;
    }
    // 渲染歌单列表到模态框
    renderPlaylistModal();
    // 显示模态框
    playlistModal.classList.add('active');
});

// 渲染模态框中的歌单列表
function renderPlaylistModal() {
    if (userPlaylists.length === 0) {
        playlistModalList.innerHTML = '<div class="modal-empty">暂无歌单，请先创建</div>';
        return;
    }

    playlistModalList.innerHTML = userPlaylists.map(playlist => `
        <div class="modal-playlist-item" onclick="addToSelectedPlaylist('${playlist.id}')">
            <div class="modal-playlist-icon">🎵</div>
            <div class="modal-playlist-info">
                <div class="modal-playlist-name">${escapeHtml(playlist.name)}</div>
                <div class="modal-playlist-count">${playlist.songs.length} 首歌曲</div>
            </div>
        </div>
    `).join('');
}

// 添加到选中的歌单
window.addToSelectedPlaylist = function(playlistId) {
    const songs = getSelectedSongs();
    addSongsToPlaylist(playlistId, songs);

    // 关闭模态框
    playlistModal.classList.remove('active');

    // 清除选中
    selectAllCheckbox.checked = false;
    document.querySelectorAll('.file-checkbox').forEach(cb => cb.checked = false);
    updateAddToPlaylistBtn();
};

// 关闭模态框
closeModalBtn.addEventListener('click', () => {
    playlistModal.classList.remove('active');
});

// 点击遮罩关闭模态框
playlistModal.addEventListener('click', (e) => {
    if (e.target === playlistModal) {
        playlistModal.classList.remove('active');
    }
});

// 按 ESC 关闭模态框
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && playlistModal.classList.contains('active')) {
        playlistModal.classList.remove('active');
    }
});

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 格式化日期
function formatDate(timestamp) {
    const date = new Date(timestamp * 1000);
    return date.toLocaleDateString('zh-CN', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// 格式化时间
function formatTime(seconds) {
    if (isNaN(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// 加载文件列表
async function loadFiles() {
    try {
        // 添加时间戳防止缓存
        const response = await fetch(`/files?t=${Date.now()}`);
        const data = await response.json();

        playlist = data.files || [];
        currentPlaylist = playlist; // 当前播放列表 = 文件列表

        renderFilesList();
        // 文件加载完成后重新渲染歌单（显示歌曲）
        renderPlaylists();
    } catch (error) {
        console.error('加载文件列表失败:', error);
    }
}

// HTML 转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 删除文件
async function deleteFile(filename) {
    if (!confirm(`确定要删除 "${filename}" 吗？`)) {
        return;
    }

    try {
        const response = await fetch(`/files/${encodeURIComponent(filename)}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            const data = await response.json();
            alert(data.detail || '删除失败');
        }

    } catch (error) {
        console.error('删除文件失败:', error);
        alert('删除失败: ' + error.message);
    }

    // 不管成功失败，都刷新列表
    setTimeout(async () => {
        await loadFiles();
    }, 200);
}

// 播放指定曲目
function playTrack(index) {
    if (index < 0 || index >= currentPlaylist.length) return;

    currentIndex = index;
    const file = currentPlaylist[index];
    const audioSrc = `/download/${encodeURIComponent(file.name)}`;

    audioPlayer.src = audioSrc;
    playerTitle.textContent = file.name.replace('.mp3', '');

    // 更新唱片机封面
    if (file.cover) {
        vinylRecord.innerHTML = `<img src="${file.cover}" alt="封面" onerror="this.innerHTML='<div class=\\'vinyl-cover-default\\'><svg viewBox=\\'0 0 24 24\\' fill=\\'currentColor\\'><path d=\\'M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z\\'/></svg></div>'">`;
    } else {
        vinylRecord.innerHTML = '<div class="vinyl-cover-default"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/></svg></div>';
    }

    // 高亮当前播放
    document.querySelectorAll('.file-item').forEach((item, i) => {
        item.classList.toggle('active', i === index);
    });

    audioPlayer.play().then(() => {
        isPlaying = true;
        playBtn.textContent = '⏸';
        vinylRecord.classList.add('playing');
    }).catch(err => {
        console.error('播放失败:', err);
    });
}

// 播放/暂停
function togglePlay() {
    if (currentPlaylist.length === 0) return;

    if (currentIndex === -1) {
        playTrack(0);
        return;
    }

    if (isPlaying) {
        audioPlayer.pause();
    } else {
        audioPlayer.play();
    }
}

// 上一曲
function prevTrack() {
    if (currentPlaylist.length === 0) return;
    const newIndex = currentIndex <= 0 ? currentPlaylist.length - 1 : currentIndex - 1;
    playTrack(newIndex);
}

// 下一曲
function nextTrack() {
    if (currentPlaylist.length === 0) return;
    const newIndex = currentIndex >= currentPlaylist.length - 1 ? 0 : currentIndex + 1;
    playTrack(newIndex);
}

// 更新播放状态
function updatePlayState(playing) {
    isPlaying = playing;
    playBtn.textContent = playing ? '⏸' : '▶';
    vinylRecord.classList.toggle('playing', playing);
}

// 音频事件监听
audioPlayer.addEventListener('play', () => updatePlayState(true));
audioPlayer.addEventListener('pause', () => updatePlayState(false));
audioPlayer.addEventListener('ended', () => nextTrack());

// 加载元数据
audioPlayer.addEventListener('loadedmetadata', () => {
    totalTimeEl.textContent = formatTime(audioPlayer.duration);
    progressBar.max = Math.floor(audioPlayer.duration);
});

// 更新进度
let isDragging = false;
let wasPlayingBeforeDrag = false;

audioPlayer.addEventListener('timeupdate', () => {
    if (!isDragging) {
        const current = audioPlayer.currentTime;
        currentTimeEl.textContent = formatTime(current);
        progressBar.value = current;
    }
});

// 进度条 - 拖动时不暂停，让播放自然继续
progressBar.addEventListener('mousedown', (e) => {
    isDragging = true;
    console.log('[进度条] mousedown');
});

progressBar.addEventListener('input', (e) => {
    const newTime = parseFloat(progressBar.value);
    currentTimeEl.textContent = formatTime(newTime);
    // 只更新显示，不设置 audioPlayer.currentTime
    // 让音频自然播放到新位置
});

progressBar.addEventListener('mouseup', (e) => {
    if (isDragging) {
        const newTime = parseFloat(progressBar.value);
        console.log('[进度条] mouseup, 跳转至:', newTime);
        audioPlayer.currentTime = newTime;
        isDragging = false;
    }
});

progressBar.addEventListener('mouseleave', (e) => {
    if (isDragging) {
        const newTime = parseFloat(progressBar.value);
        console.log('[进度条] mouseleave, 跳转至:', newTime);
        audioPlayer.currentTime = newTime;
        isDragging = false;
    }
});

// 音量控制
volumeBar.addEventListener('input', () => {
    audioPlayer.volume = volumeBar.value / 100;
});

// 绑定播放器按钮事件
playBtn.addEventListener('click', togglePlay);
prevBtn.addEventListener('click', prevTrack);
nextBtn.addEventListener('click', nextTrack);

// 提交下载
downloadForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const url = urlInput.value.trim();
    if (!url) {
        alert('请输入视频链接');
        return;
    }

    // 重置 UI
    hideAllContainers();
    setButtonLoading(true);

    try {
        // 启动下载任务
        const response = await fetch('/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `url=${encodeURIComponent(url)}`
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || '启动下载失败');
        }

        // 显示进度条
        showProgress();
        progressText.textContent = '正在连接...';
        progressPercent.textContent = '0%';
        progressFill.style.width = '0%';

        // 监听进度
        startProgressListener(data.task_id);

    } catch (error) {
        showError(error.message);
        setButtonLoading(false);
    }
});

// 开始监听进度
function startProgressListener(taskId) {
    // 关闭之前的连接
    if (eventSource) {
        eventSource.close();
        eventSource = null;
    }

    // 创建 SSE 连接
    eventSource = new EventSource(`/progress/${taskId}`);

    eventSource.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);

            // 更新进度
            progressText.textContent = data.message || '处理中...';
            progressPercent.textContent = `${Math.round(data.progress)}%`;
            progressFill.style.width = `${data.progress}%`;

            if (data.status === 'complete') {
                // 下载完成
                eventSource.close();
                eventSource = null;

                if (data.filename) {
                    showResult(data.filename);
                }

                setButtonLoading(false);
                loadFiles();

            } else if (data.status === 'error') {
                // 下载失败
                eventSource.close();
                eventSource = null;

                showError(data.message || data.error || '下载失败');
                setButtonLoading(false);
            }

        } catch (error) {
            console.error('解析进度数据失败:', error);
        }
    };

    eventSource.onerror = (error) => {
        console.error('SSE 连接错误:', error);
        eventSource.close();
        eventSource = null;
        setButtonLoading(false);
    };
}

// UI 辅助函数
function hideAllContainers() {
    progressContainer.style.display = 'none';
    resultContainer.style.display = 'none';
    errorContainer.style.display = 'none';
}

function showProgress() {
    progressContainer.style.display = 'block';
}

function showResult(filename) {
    progressContainer.style.display = 'none';
    resultContainer.style.display = 'block';
    successText.textContent = '下载完成!';
    downloadLink.href = `/download/${encodeURIComponent(filename)}`;
    downloadLink.download = filename;
}

function showError(message) {
    progressContainer.style.display = 'none';
    resultContainer.style.display = 'none';
    errorContainer.style.display = 'block';
    errorText.textContent = message;
}

function setButtonLoading(loading) {
    downloadBtn.disabled = loading;
    if (loading) {
        btnText.style.display = 'none';
        btnLoading.style.display = 'inline';
    } else {
        btnText.style.display = 'inline';
        btnLoading.style.display = 'none';
    }
}

// 暴露给全局作用域
window.deleteFile = deleteFile;
window.deletePlaylist = deletePlaylist;
window.renamePlaylist = renamePlaylist;
window.playPlaylist = playPlaylist;
window.togglePlaylistSection = togglePlaylistSection;
window.togglePlaylistDetail = togglePlaylistDetail;
window.playPlaylistSong = playPlaylistSong;
window.removeSongFromPlaylist = removeSongFromPlaylist;
window.toggleFilesSection = toggleFilesSection;

// 歌单区域展开/收起
let playlistExpanded = true;
function togglePlaylistSection() {
    const content = document.getElementById('playlistContent');
    const toggle = document.getElementById('playlistToggle');
    playlistExpanded = !playlistExpanded;
    if (playlistExpanded) {
        content.style.display = 'block';
        toggle.style.transform = 'rotate(0deg)';
    } else {
        content.style.display = 'none';
        toggle.style.transform = 'rotate(-90deg)';
    }
}

// 文件列表展开/收起
let filesExpanded = true;
function toggleFilesSection() {
    const content = document.getElementById('filesContent');
    const toggle = document.getElementById('filesToggle');
    filesExpanded = !filesExpanded;
    if (filesExpanded) {
        content.style.display = 'block';
        toggle.style.transform = 'rotate(0deg)';
    } else {
        content.style.display = 'none';
        toggle.style.transform = 'rotate(-90deg)';
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    loadFiles();
    loadPlaylists();
    renderPlaylists();

    // 歌单事件委托（处理歌曲点击和删除）
    playlistList.addEventListener('click', (e) => {
        // 处理歌曲点击播放
        const songItem = e.target.closest('.playlist-song-item');
        if (songItem && !e.target.closest('.song-remove')) {
            const playlistId = songItem.dataset.playlistId;
            const songIndex = parseInt(songItem.dataset.songIndex);
            playPlaylistSong(playlistId, songIndex);
        }

        // 处理删除按钮
        const removeBtn = e.target.closest('.song-remove');
        if (removeBtn) {
            const playlistId = removeBtn.dataset.playlistId;
            const songName = removeBtn.dataset.songName;
            removeSongFromPlaylist(playlistId, songName);
        }
    });
});

// ========== 搜索功能 ==========

// 搜索按钮点击事件
searchBtn.addEventListener('click', performSearch);

// 回车搜索
searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        performSearch();
    }
});

// 执行搜索
async function performSearch() {
    const keyword = searchInput.value.trim();
    if (!keyword) {
        alert('请输入搜索关键词');
        return;
    }

    // 显示加载状态
    searchResults.innerHTML = '<div class="search-loading">搜索中...</div>';
    searchResults.style.display = 'block';

    try {
        const response = await fetch(`/search?keyword=${encodeURIComponent(keyword)}`);
        const data = await response.json();

        if (data.results && data.results.length > 0) {
            renderSearchResults(data.results);
            searchResults.classList.add('has-content');
        } else {
            searchResults.innerHTML = '<div class="search-empty">未找到相关视频</div>';
            searchResults.classList.add('has-content');
        }
    } catch (error) {
        console.error('搜索失败:', error);
        searchResults.innerHTML = '<div class="search-empty">搜索失败，请重试</div>';
        searchResults.classList.add('has-content');
    }
}

// 渲染搜索结果
function renderSearchResults(results) {
    console.log('搜索结果:', results);  // 调试
    searchResults.innerHTML = results.map(item => {
        // 处理标题，移除 HTML 标签
        const cleanTitle = item.title ? item.title.replace(/<[^>]*>/g, '') : '无标题';
        // 处理封面 URL
        const coverUrl = item.pic ? (item.pic.startsWith('http') ? item.pic : `https:${item.pic}`) : '';
        // 安全处理 URL
        const safeUrl = encodeURIComponent(item.url);

        // 调试：显示实际 URL
        console.log('视频 URL:', item.url, 'bvid:', item.bvid);

        return `
            <div class="search-item" data-url="${escapeHtml(item.url)}">
                <img class="search-item-cover" src="${coverUrl}" alt="封面" onerror="this.style.display='none'">
                <div class="search-item-info">
                    <div class="search-item-title">${escapeHtml(cleanTitle)}</div>
                    <div class="search-item-author">${escapeHtml(item.author || '未知作者')}</div>
                </div>
                <button class="search-item-download" onclick="event.stopPropagation(); downloadFromSearch('${safeUrl}')">下载音频</button>
            </div>
        `;
    }).join('');

    // 点击整行也可以下载
    document.querySelectorAll('.search-item').forEach(item => {
        item.addEventListener('click', () => {
            const url = item.dataset.url;
            console.log('点击的 URL:', url);  // 调试
            downloadFromSearch(url);
        });
    });
}

// 从搜索结果下载
async function downloadFromSearch(url) {
    // URL 解码（因为存储时进行了编码）
    const decodedUrl = decodeURIComponent(url);
    // 将 URL 填入下载输入框
    urlInput.value = decodedUrl;

    // 触发下载表单提交
    downloadForm.dispatchEvent(new Event('submit'));
}