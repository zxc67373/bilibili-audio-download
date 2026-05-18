#!/usr/bin/env python3
"""
Bilibili 搜索 API 测试脚本
"""
import httpx
import re
import asyncio
from urllib.parse import quote

async def test_search(keyword: str):
    print(f"\n========== 搜索: {keyword} ==========")

    # 禁用代理
    import os
    for var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
        os.environ.pop(var, None)

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, trust_env=False) as client:
        # 1. 先访问 B站首页获取 cookies
        print("1. 获取 cookies...")
        await client.get("https://www.bilibili.com")
        print("   Cookies 获取完成")

        # 2. 搜索
        print("2. 发送搜索请求...")
        search_url = "https://api.bilibili.com/x/web-interface/search/all/v2"
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
        print(f"   状态码: {response.status_code}")

        data = response.json()
        print(f"   API 返回 code: {data.get('code')}, message: {data.get('message')}")

        if data.get("code") != 0:
            print(f"   错误: {data.get('message')}")
            return

        # 打印完整数据结构
        import json
        print(f"\n   ===== API 完整响应 data =====")
        print(json.dumps(data.get("data", {}), indent=2, ensure_ascii=False)[:3000])

        # 3. 解析结果 - result 数组包含各类型模块，找到 video 模块
        result_modules = data.get("data", {}).get("result", [])
        print(f"   结果模块数量: {len(result_modules)}")

        # 找到 video 类型的模块
        video_module = None
        for module in result_modules:
            if module.get("result_type") == "video":
                video_module = module
                break

        if not video_module:
            print(f"   未找到 video 模块")
            return []

        video_list = video_module.get("data", [])
        print(f"   视频数量: {len(video_list)}")

        # 打印第一个视频的完整结构
        if video_list:
            print(f"\n   ===== 第1个视频完整结构 =====")
            import json
            print(json.dumps(video_list[0], indent=2, ensure_ascii=False)[:2000])

        video_results = []
        for item in video_list:
            # 只处理视频类型
            if item.get("type") != "video":
                continue

            title = item.get("title", "")
            title = re.sub(r'<[^>]*>', '', title)  # 移除 HTML

            arcurl = item.get("arcurl", "")
            bvid = item.get("bvid", "")
            aid = item.get("aid", "")

            # 处理封面
            pic = item.get("pic", "")
            if pic.startswith("//"):
                pic = "https:" + pic

            video_results.append({
                "title": title,
                "arcurl": arcurl,
                "bvid": bvid,
                "aid": aid,
                "pic": pic,
                "author": item.get("author", ""),
                "duration": item.get("duration", ""),
            })

            if len(video_results) <= 3:  # 只打印前3条
                print(f"\n   结果 {len(video_results)}:")
                print(f"   - 标题: {title[:50]}...")
                print(f"   - arcurl: {arcurl}")
                print(f"   - bvid: {bvid}")
                print(f"   - aid: {aid}")
                print(f"   - 封面: {pic[:60]}...")

        print(f"\n   视频结果数量: {len(video_results)}")
        return video_results

if __name__ == "__main__":
    # 测试搜索
    results = asyncio.run(test_search("徐良"))
    print(f"\n========== 测试完成，共找到 {len(results)} 个视频 ==========")