#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
里章屿的故事会 - 全平台热点抓取引擎
升级：高赞评论抓取 + 故事核分析 + 来源权重排序
"""

import requests
import json
import re
import time
from datetime import datetime
from typing import List, Dict
import os

# 配置
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# 导入故事核
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from story_core import analyze_hotspot, get_source_weight, generate_what_if


def enhance_item(item: Dict) -> Dict:
    """用故事核分析器增强每条热点"""
    analysis = analyze_hotspot(
        item.get("title", ""),
        item.get("content", ""),
        item.get("top_comments", []),
    )
    item["story_analysis"] = analysis
    item["source_weight"] = get_source_weight(item.get("platform", ""))
    item["what_if_prompts"] = generate_what_if(
        item.get("title", ""),
        [c["category"] for c in analysis["story_categories"]],
    )
    return item


# ============================================================
# 高赞评论抓取
# ============================================================
def fetch_weibo_comments(topic_id: str = None, limit: int = 5) -> List[str]:
    """抓取微博热搜话题的高赞评论"""
    comments = []
    try:
        # 微博热搜话题评论需要登录，尝试公开接口
        if not topic_id:
            return comments
        url = f"https://m.weibo.cn/comments/hotflow?id={topic_id}&mid={topic_id}&max_id_type=0"
        headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15",
            "Referer": "https://m.weibo.cn/"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if "data" in data and "data" in data["data"]:
                for item in data["data"]["data"][:limit]:
                    text = item.get("text", "")
                    # 清理HTML
                    text = re.sub(r'<[^>]+>', '', text)
                    like_count = item.get("like_count", 0)
                    if text:
                        comments.append(f"[{like_count}赞] {text}")
    except Exception as e:
        pass
    return comments


def fetch_zhihu_comments(answer_id: str = None, limit: int = 5) -> List[str]:
    """抓取知乎回答的高赞评论"""
    comments = []
    try:
        if not answer_id:
            return comments
        url = f"https://www.zhihu.com/api/v4/answers/{answer_id}/root_comments"
        params = {"limit": limit, "offset": 0, "order": "normal"}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.zhihu.com/"
        }
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if "data" in data:
                for item in data["data"][:limit]:
                    content = item.get("content", "")
                    content = re.sub(r'<[^>]+>', '', content)
                    vote = item.get("vote_count", 0)
                    if content:
                        comments.append(f"[{vote}赞] {content}")
    except Exception as e:
        pass
    return comments


def fetch_bilibili_comments(aid: str = None, limit: int = 5) -> List[str]:
    """抓取B站视频高赞评论"""
    comments = []
    try:
        if not aid:
            return comments
        url = f"https://api.bilibili.com/x/v2/reply/main"
        params = {"type": 1, "oid": aid, "mode": 3, "next": 0, "ps": limit}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.bilibili.com/"
        }
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("data") and "replies" in data["data"]:
                for item in data["data"]["replies"][:limit]:
                    content = item.get("content", {}).get("message", "")
                    like = item.get("like", 0)
                    if content:
                        comments.append(f"[{like}赞] {content}")
    except Exception as e:
        pass
    return comments


# ============================================================
# 平台 1: 微博热搜
# ============================================================
def fetch_weibo() -> List[Dict]:
    results = []
    try:
        url = "https://weibo.com/ajax/side/hotSearch"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://weibo.com/"
        }
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if "data" in data and "realtime" in data["data"]:
                for i, item in enumerate(data["data"]["realtime"][:50]):
                    title = item.get("word", "")
                    heat = item.get("raw_hot", "")
                    category = item.get("category", "")
                    rank = item.get("rank", i + 1)
                    note = item.get("note", "")
                    
                    hot_type = "日常热点"
                    if category in ["社会", "时事", "法治"]:
                        hot_type = "社会新闻"
                    elif category in ["娱乐", "明星", "影视"]:
                        hot_type = "娱乐热点"
                    
                    enhanced = enhance_item({
                        "platform": "微博",
                        "section": "热搜榜",
                        "rank": rank,
                        "title": title,
                        "heat": str(heat) if heat else "",
                        "category": category,
                        "hot_type": hot_type,
                        "url": f"https://s.weibo.com/weibo?q={requests.utils.quote(title)}",
                        "content": note,
                        "top_comments": [],
                        "fetch_time": datetime.now().isoformat(),
                    })
                    results.append(enhanced)
    except Exception as e:
        print(f"[微博] 抓取失败: {e}")
    return results


# ============================================================
# 平台 2: 知乎热榜 + 高赞回答
# ============================================================
def fetch_zhihu_hot() -> List[Dict]:
    results = []
    try:
        url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.zhihu.com/hot"
        }
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if "data" in data:
                for i, item in enumerate(data["data"][:30]):
                    target = item.get("target", {})
                    title = target.get("title", "")
                    heat = item.get("detail_text", "")
                    url_link = target.get("url", "")
                    excerpt = target.get("excerpt", "")[:300]
                    question_id = target.get("id", "")
                    
                    enhanced = enhance_item({
                        "platform": "知乎",
                        "section": "热榜",
                        "rank": i + 1,
                        "title": title,
                        "heat": heat,
                        "category": "",
                        "hot_type": "讨论热点",
                        "url": url_link,
                        "content": excerpt,
                        "top_comments": [],
                        "question_id": str(question_id),
                        "fetch_time": datetime.now().isoformat(),
                    })
                    results.append(enhanced)
                    
                    # 尝试抓取高赞回答的评论（只对前5条做，避免太慢）
                    if i < 5 and question_id:
                        try:
                            ans_url = f"https://www.zhihu.com/api/v4/questions/{question_id}/answers"
                            ans_params = {"limit": 1, "offset": 0, "sort_by": "voteups"}
                            ans_resp = requests.get(ans_url, headers=headers, params=ans_params, timeout=10)
                            if ans_resp.status_code == 200:
                                ans_data = ans_resp.json()
                                if "data" in ans_data and ans_data["data"]:
                                    answer = ans_data["data"][0]
                                    answer_id = answer.get("id", "")
                                    ans_content = re.sub(r'<[^>]+>', '', answer.get("content", ""))[:500]
                                    voteup = answer.get("voteup_count", 0)
                                    
                                    # 把高赞回答作为内容
                                    enhanced["content"] = f"[高赞回答 {voteup}赞] {ans_content}"
                                    
                                    # 抓取该回答的评论
                                    comments = fetch_zhihu_comments(str(answer_id), 5)
                                    if comments:
                                        enhanced["top_comments"] = comments
                        except:
                            pass
                        time.sleep(0.3)
    except Exception as e:
        print(f"[知乎热榜] 抓取失败: {e}")
    return results


# ============================================================
# 平台 3: 知乎日报
# ============================================================
def fetch_zhihu_daily() -> List[Dict]:
    results = []
    try:
        url = "https://news-at.zhihu.com/api/4/news/latest"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if "stories" in data:
                for i, item in enumerate(data["stories"][:20]):
                    title = item.get("title", "")
                    story_id = item.get("id", "")
                    hint = item.get("hint", "")
                    
                    enhanced = enhance_item({
                        "platform": "知乎日报",
                        "section": "知乎日报",
                        "rank": i + 1,
                        "title": title,
                        "heat": "",
                        "category": "",
                        "hot_type": "深度报道",
                        "url": f"https://daily.zhihu.com/story/{story_id}",
                        "content": hint,
                        "top_comments": [],
                        "fetch_time": datetime.now().isoformat(),
                    })
                    results.append(enhanced)
    except Exception as e:
        print(f"[知乎日报] 抓取失败: {e}")
    return results


# ============================================================
# 平台 4: B站热门 + 热搜 + 高赞评论
# ============================================================
def fetch_bilibili() -> List[Dict]:
    results = []
    try:
        url = "https://api.bilibili.com/x/web-interface/popular"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.bilibili.com"
        }
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("data") and "list" in data["data"]:
                for i, item in enumerate(data["data"]["list"][:30]):
                    title = item.get("title", "")
                    bvid = item.get("bvid", "")
                    aid = item.get("aid", "")
                    desc = item.get("desc", "")[:300]
                    stat = item.get("stat", {})
                    view = stat.get("view", 0)
                    like = stat.get("like", 0)
                    
                    enhanced = enhance_item({
                        "platform": "B站",
                        "section": "热门",
                        "rank": i + 1,
                        "title": title,
                        "heat": f"播放{view}",
                        "category": item.get("tname", ""),
                        "hot_type": "视频热点",
                        "url": f"https://www.bilibili.com/video/{bvid}",
                        "content": desc,
                        "top_comments": [],
                        "aid": str(aid),
                        "fetch_time": datetime.now().isoformat(),
                    })
                    results.append(enhanced)
                    
                    # 前5条抓评论
                    if i < 5 and aid:
                        comments = fetch_bilibili_comments(str(aid), 5)
                        if comments:
                            enhanced["top_comments"] = comments
                        time.sleep(0.3)
    except Exception as e:
        print(f"[B站热门] 抓取失败: {e}")
    
    # B站热搜
    try:
        url = "https://api.bilibili.com/x/web-interface/search/square"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://search.bilibili.com"
        }
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("data") and "trending" in data["data"]:
                for i, item in enumerate(data["data"]["trending"].get("list", [])[:20]):
                    title = item.get("keyword", "")
                    
                    enhanced = enhance_item({
                        "platform": "B站",
                        "section": "热搜",
                        "rank": i + 1,
                        "title": title,
                        "heat": "",
                        "category": "",
                        "hot_type": "搜索热点",
                        "url": f"https://search.bilibili.com/all?keyword={requests.utils.quote(title)}",
                        "content": "",
                        "top_comments": [],
                        "fetch_time": datetime.now().isoformat(),
                    })
                    results.append(enhanced)
    except Exception as e:
        print(f"[B站热搜] 抓取失败: {e}")
    
    return results


# ============================================================
# 平台 5: 抖音热点榜
# ============================================================
def fetch_douyin() -> List[Dict]:
    results = []
    try:
        url = "https://www.douyin.com/aweme/v1/web/hot/search/list/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.douyin.com/"
        }
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if "data" in data and "word_list" in data["data"]:
                for i, item in enumerate(data["data"]["word_list"][:30]):
                    word = item.get("word", "")
                    hot_value = item.get("hot_value", "")
                    
                    enhanced = enhance_item({
                        "platform": "抖音",
                        "section": "热点榜",
                        "rank": i + 1,
                        "title": word,
                        "heat": str(hot_value),
                        "category": "",
                        "hot_type": "短视频热点",
                        "url": f"https://www.douyin.com/search/{requests.utils.quote(word)}",
                        "content": "",
                        "top_comments": [],
                        "fetch_time": datetime.now().isoformat(),
                    })
                    results.append(enhanced)
    except Exception as e:
        print(f"[抖音热点] 抓取失败: {e}")
    return results


# ============================================================
# 平台 6: 抖音搜索热榜
# ============================================================
def fetch_douyin_search() -> List[Dict]:
    results = []
    try:
        url = "https://www.douyin.com/aweme/v1/web/search/suggest/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.douyin.com/"
        }
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if "sug_list" in data:
                for i, item in enumerate(data["sug_list"][:20]):
                    word = item.get("content", "")
                    
                    enhanced = enhance_item({
                        "platform": "抖音",
                        "section": "搜索热榜",
                        "rank": i + 1,
                        "title": word,
                        "heat": "",
                        "category": "",
                        "hot_type": "脑洞词条",
                        "url": f"https://www.douyin.com/search/{requests.utils.quote(word)}",
                        "content": "【提示】只看词条表面，自己联想拓展，保证脑洞独一无二",
                        "top_comments": [],
                        "fetch_time": datetime.now().isoformat(),
                    })
                    results.append(enhanced)
    except Exception as e:
        print(f"[抖音搜索] 抓取失败: {e}")
    return results


# ============================================================
# 平台 7: 小红书搜索热榜
# ============================================================
def fetch_xiaohongshu() -> List[Dict]:
    results = []
    try:
        url = "https://www.xiaohongshu.com/web_api/sns/v3/search/trending"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.xiaohongshu.com/"
        }
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if "data" in data and "queries" in data["data"]:
                for i, item in enumerate(data["data"]["queries"][:30]):
                    query = item.get("query", "")
                    
                    enhanced = enhance_item({
                        "platform": "小红书",
                        "section": "搜索热榜",
                        "rank": i + 1,
                        "title": query,
                        "heat": "",
                        "category": "",
                        "hot_type": "轻脑洞热点",
                        "url": f"https://www.xiaohongshu.com/search_result?keyword={requests.utils.quote(query)}",
                        "content": "【提示】小红书热点脑洞比其他平台大，适合轻脑洞文",
                        "top_comments": [],
                        "fetch_time": datetime.now().isoformat(),
                    })
                    results.append(enhanced)
    except Exception as e:
        print(f"[小红书] 抓取失败: {e}")
    return results


# ============================================================
# 平台 8: 网易新闻
# ============================================================
def fetch_netease() -> List[Dict]:
    results = []
    try:
        url = "https://news.163.com/"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, 'html.parser')
            hot_items = soup.select('.news_title a')[:15]
            for i, item in enumerate(hot_items):
                title = item.get_text(strip=True)
                link = item.get('href', '')
                if title and link:
                    enhanced = enhance_item({
                        "platform": "网易新闻",
                        "section": "首页热点",
                        "rank": i + 1,
                        "title": title,
                        "heat": "",
                        "category": "",
                        "hot_type": "新闻热点",
                        "url": link if link.startswith('http') else f"https://news.163.com{link}",
                        "content": "",
                        "top_comments": [],
                        "fetch_time": datetime.now().isoformat(),
                    })
                    results.append(enhanced)
    except Exception as e:
        print(f"[网易新闻] 抓取失败: {e}")
    return results


# ============================================================
# 平台 9: 腾讯新闻
# ============================================================
def fetch_tencent() -> List[Dict]:
    results = []
    try:
        url = "https://i.news.qq.com/trpc.qqnews_web.kv_srv.kv_srv_http_proxy/list"
        params = {"sub_srv_id": "social", "srv_id": "pc", "offset": 0, "limit": 15, "strategy": 1}
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if "data" in data and "list" in data["data"]:
                for i, item in enumerate(data["data"]["list"][:15]):
                    title = item.get("title", "")
                    link = item.get("url", "")
                    if title:
                        enhanced = enhance_item({
                            "platform": "腾讯新闻",
                            "section": "社会新闻",
                            "rank": i + 1,
                            "title": title,
                            "heat": "",
                            "category": "",
                            "hot_type": "新闻热点",
                            "url": link,
                            "content": "",
                            "top_comments": [],
                            "fetch_time": datetime.now().isoformat(),
                        })
                        results.append(enhanced)
    except Exception as e:
        print(f"[腾讯新闻] 抓取失败: {e}")
    return results


# ============================================================
# 主抓取函数
# ============================================================
def fetch_all() -> Dict[str, List[Dict]]:
    """抓取所有平台的热点"""
    print(f"\n{'='*60}")
    print(f"  里章屿的故事会 - 全平台抓取")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    all_data = {
        "微博": fetch_weibo(),
        "知乎热榜": fetch_zhihu_hot(),
        "知乎日报": fetch_zhihu_daily(),
        "B站": fetch_bilibili(),
        "抖音": fetch_douyin(),
        "抖音搜索": fetch_douyin_search(),
        "小红书": fetch_xiaohongshu(),
        "网易新闻": fetch_netease(),
        "腾讯新闻": fetch_tencent(),
    }
    
    total = sum(len(v) for v in all_data.values())
    story_worthy = sum(
        1 for items in all_data.values() 
        for item in items 
        if item.get("story_analysis", {}).get("is_story_worthy", False)
    )
    
    print(f"\n{'='*60}")
    print(f"  抓取完成！总计: {total} 条 | 故事感强: {story_worthy} 条")
    for platform, items in all_data.items():
        sw = sum(1 for i in items if i.get("story_analysis", {}).get("is_story_worthy", False))
        print(f"  {platform}: {len(items)} 条 (故事感强 {sw} 条)")
    print(f"{'='*60}\n")
    
    return all_data


if __name__ == "__main__":
    data = fetch_all()
