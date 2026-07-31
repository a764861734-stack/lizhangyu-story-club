#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
里章屿的故事会 - Web服务
创作加工车间：智能筛选 + 如果生成器 + 零件拆解 + 关联推荐 + 仪表盘 + 素材包
"""

import os
import sys
import json
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Query, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import pandas as pd
import uvicorn

from scraper import fetch_all
from story_core import (
    STORY_CORE, SOURCE_WEIGHTS, WHAT_IF_TEMPLATES, PART_TEMPLATES,
    analyze_hotspot, get_source_weight, generate_what_if, suggest_parts,
    find_related, generate_starter_pack, get_keyword_library,
    filter_by_story_core,
)
from deconstruction import (
    save_project, load_project, list_projects, delete_project,
    analyze_chapters, export_decon_to_excel,
    DeconProject, ChapterData,
)
from material_manager import (
    get_index, get_items, add_item, update_item, delete_item,
    export_library_to_excel, export_all_to_excel,
    LIBRARY_CONFIG,
)
from material_auto_fill import auto_fill_from_hotspots

# 配置
BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "data" / "hotspots.json"
COLLECTION_FILE = BASE_DIR / "data" / "collection.json"  # 收藏的素材
DATA_FILE.parent.mkdir(exist_ok=True)
EXCEL_DIR = BASE_DIR / "exports"
EXCEL_DIR.mkdir(exist_ok=True)

app = FastAPI(title="里章屿的故事会", description="小说创作热点聚合 + 加工车间")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


# ============================================================
# 数据管理
# ============================================================
def save_data(data: Dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_data() -> Dict:
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def load_collection() -> List[Dict]:
    if COLLECTION_FILE.exists():
        with open(COLLECTION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_collection(collection: List[Dict]):
    with open(COLLECTION_FILE, "w", encoding="utf-8") as f:
        json.dump(collection, f, ensure_ascii=False, indent=2)


def export_to_excel(data: Dict, filename: str = None) -> str:
    if filename is None:
        filename = f"热点原始材料_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    filepath = EXCEL_DIR / filename
    
    all_items = []
    for platform, items in data.items():
        for item in items:
            analysis = item.get("story_analysis", {})
            all_items.append({
                "抓取时间": item.get("fetch_time", ""),
                "平台": item.get("platform", ""),
                "版块": item.get("section", ""),
                "排名": item.get("rank", ""),
                "标题": item.get("title", ""),
                "热度": item.get("heat", ""),
                "热点类型": item.get("hot_type", ""),
                "故事核分类": ", ".join(c["category"] for c in analysis.get("story_categories", [])),
                "匹配关键词": ", ".join(analysis.get("matched_keywords", [])),
                "故事感评分": analysis.get("story_score", 0),
                "情感浓度": analysis.get("emotion_density", 0),
                "适用题材": analysis.get("story_type", ""),
                "内容摘要": item.get("content", ""),
                "高赞评论": " | ".join(item.get("top_comments", [])),
                "链接": item.get("url", ""),
            })
    
    df = pd.DataFrame(all_items)
    
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='全部热点', index=False)
        
        for platform in df['平台'].unique():
            if pd.notna(platform):
                platform_df = df[df['平台'] == platform].copy()
                platform_df.to_excel(writer, sheet_name=str(platform)[:31], index=False)
        
        story_df = df[df['故事感评分'] >= 20].sort_values('故事感评分', ascending=False)
        if not story_df.empty:
            story_df.to_excel(writer, sheet_name='故事感强', index=False)
    
    return str(filepath)


# ============================================================
# 定时任务
# ============================================================
async def scheduled_fetch():
    print(f"[{datetime.now()}] 开始定时抓取...")
    try:
        data = fetch_all()
        save_data(data)
        export_to_excel(data)
        print(f"[{datetime.now()}] 定时抓取完成！")
    except Exception as e:
        print(f"[{datetime.now()}] 定时抓取失败: {e}")


async def schedule_task():
    while True:
        now = datetime.now()
        target_times = [
            now.replace(hour=8, minute=0, second=0, microsecond=0),
            now.replace(hour=20, minute=0, second=0, microsecond=0),
        ]
        for i, t in enumerate(target_times):
            if t <= now:
                target_times[i] = t + timedelta(days=1)
        next_run = min(target_times)
        wait_seconds = (next_run - now).total_seconds()
        print(f"[{datetime.now()}] 下次抓取: {next_run} (等待 {wait_seconds/3600:.1f}h)")
        await asyncio.sleep(wait_seconds)
        await scheduled_fetch()


# ============================================================
# Pydantic 模型
# ============================================================
class WhatIfRequest(BaseModel):
    item_id: str
    title: str
    what_if: str
    platform: str = ""
    url: str = ""


class PartRequest(BaseModel):
    item_id: str
    title: str
    selected_text: str
    parts: Dict[str, str]  # {"人设零件": "...", "场景零件": "...", ...}
    platform: str = ""
    url: str = ""


class StarterPackRequest(BaseModel):
    genre: str
    item_ids: Optional[List[str]] = None


# ============================================================
# 小说拆解分析 API
# ============================================================
@app.post("/api/deconstructions")
async def api_create_decon(project: DeconProject):
    data = project.dict()
    saved = save_project(data)
    return {"status": "ok", "project": saved}


@app.get("/api/deconstructions")
async def api_list_decons():
    return {"status": "ok", "projects": list_projects()}


@app.get("/api/deconstructions/{project_id}")
async def api_get_decon(project_id: str):
    project = load_project(project_id)
    if not project:
        return JSONResponse(status_code=404, content={"status": "error", "message": "项目不存在"})
    return {"status": "ok", "project": project}


@app.put("/api/deconstructions/{project_id}")
async def api_update_decon(project_id: str, project: DeconProject):
    existing = load_project(project_id)
    if not existing:
        return JSONResponse(status_code=404, content={"status": "error", "message": "项目不存在"})

    data = project.dict()
    data["id"] = project_id
    data["created_at"] = existing.get("created_at", datetime.now().isoformat())
    saved = save_project(data)
    return {"status": "ok", "project": saved}


@app.delete("/api/deconstructions/{project_id}")
async def api_delete_decon(project_id: str):
    if delete_project(project_id):
        return {"status": "ok", "message": "已删除"}
    return JSONResponse(status_code=404, content={"status": "error", "message": "项目不存在"})


@app.post("/api/deconstructions/{project_id}/analyze")
async def api_analyze_decon(project_id: str):
    project = load_project(project_id)
    if not project:
        return JSONResponse(status_code=404, content={"status": "error", "message": "项目不存在"})

    analysis = analyze_chapters(project.get("chapters", []))
    return {"status": "ok", "analysis": analysis}


@app.get("/api/deconstructions/{project_id}/export")
async def api_export_decon(project_id: str):
    project = load_project(project_id)
    if not project:
        return JSONResponse(status_code=404, content={"status": "error", "message": "项目不存在"})

    try:
        filepath = export_decon_to_excel(project)
        filename = Path(filepath).name
        return FileResponse(filepath, filename=filename)
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


# ============================================================
# API路由
# ============================================================
@app.get("/", response_class=HTMLResponse)
async def root():
    html_path = BASE_DIR / "static" / "index.html"
    if html_path.exists():
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>里章屿的故事会</h1>"


@app.get("/api/hotspots")
async def get_hotspots(
    platform: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    story_only: bool = Query(False),
    min_score: int = Query(0),
    sort_by: str = Query("story"),  # story / time / source
):
    """获取热点数据 - 支持故事核筛选"""
    data = load_data()
    if not data:
        return {"status": "empty", "message": "暂无数据，请等待自动更新或手动触发抓取", "data": {}}
    
    filtered = {}
    for plat, items in data.items():
        if platform and plat != platform:
            continue
        
        filtered_items = []
        for item in items:
            # 关键词搜索
            if keyword:
                search_text = f"{item.get('title', '')} {item.get('content', '')} {' '.join(item.get('top_comments', []))}"
                if keyword.lower() not in search_text.lower():
                    continue
            
            # 故事感筛选
            analysis = item.get("story_analysis", {})
            if story_only and not analysis.get("is_story_worthy", False):
                continue
            
            # 最低评分
            if min_score > 0 and analysis.get("story_score", 0) < min_score:
                continue
            
            filtered_items.append(item)
        
        # 排序
        if sort_by == "story":
            filtered_items.sort(
                key=lambda x: x.get("story_analysis", {}).get("story_score", 0) + x.get("source_weight", 0),
                reverse=True,
            )
        elif sort_by == "source":
            filtered_items.sort(key=lambda x: x.get("source_weight", 0), reverse=True)
        
        if filtered_items:
            filtered[plat] = filtered_items
    
    return {
        "status": "ok",
        "update_time": datetime.now().isoformat(),
        "total": sum(len(v) for v in filtered.values()),
        "platforms": list(filtered.keys()),
        "data": filtered
    }


@app.get("/api/keywords")
async def get_keywords():
    """获取故事核关键词库"""
    return get_keyword_library()


@app.get("/api/what-if")
async def get_what_if(title: str, categories: Optional[str] = Query(None)):
    """生成"如果"提问"""
    cat_list = categories.split(",") if categories else None
    prompts = generate_what_if(title, cat_list)
    return {"title": title, "prompts": prompts}


@app.get("/api/parts/suggest")
async def get_part_suggestions(text: str, category: str = ""):
    """零件拆解建议"""
    return suggest_parts(text, category)


@app.get("/api/related/{item_idx}")
async def get_related(
    item_idx: int,
    platform: str = Query(...),
):
    """跨源关联推荐"""
    data = load_data()
    source_items = data.get(platform, [])
    if item_idx >= len(source_items):
        return {"related": []}
    
    item = source_items[item_idx]
    related = find_related(item, data)
    return {"related": related}


@app.post("/api/collect/what-if")
async def collect_what_if(req: WhatIfRequest):
    """收藏"如果"脑洞"""
    collection = load_collection()
    
    # 查找是否已存在
    existing = None
    for c in collection:
        if c.get("item_id") == req.item_id:
            existing = c
            break
    
    if existing:
        existing["what_if"] = req.what_if
        existing["updated_at"] = datetime.now().isoformat()
    else:
        collection.append({
            "id": str(uuid.uuid4()),
            "item_id": req.item_id,
            "title": req.title,
            "what_if": req.what_if,
            "platform": req.platform,
            "url": req.url,
            "parts": {},
            "collected_at": datetime.now().isoformat(),
        })
    
    save_collection(collection)
    return {"status": "ok", "message": "脑洞已保存", "total": len(collection)}


@app.post("/api/collect/parts")
async def collect_parts(req: PartRequest):
    """收藏拆解的零件"""
    collection = load_collection()
    
    existing = None
    for c in collection:
        if c.get("item_id") == req.item_id:
            existing = c
            break
    
    if existing:
        existing["parts"] = req.parts
        existing["selected_text"] = req.selected_text
        existing["updated_at"] = datetime.now().isoformat()
    else:
        collection.append({
            "id": str(uuid.uuid4()),
            "item_id": req.item_id,
            "title": req.title,
            "selected_text": req.selected_text,
            "parts": req.parts,
            "platform": req.platform,
            "url": req.url,
            "what_if": "",
            "collected_at": datetime.now().isoformat(),
        })
    
    save_collection(collection)
    return {"status": "ok", "message": "零件已保存", "total": len(collection)}


@app.get("/api/collection")
async def get_collection():
    """获取已收藏的素材"""
    collection = load_collection()
    return {"status": "ok", "total": len(collection), "data": collection}


@app.delete("/api/collection/{item_id}")
async def delete_collection_item(item_id: str):
    """删除收藏的素材"""
    collection = load_collection()
    collection = [c for c in collection if c.get("id") != item_id and c.get("item_id") != item_id]
    save_collection(collection)
    return {"status": "ok", "message": "已删除", "total": len(collection)}


@app.post("/api/starter-pack")
async def create_starter_pack(req: StarterPackRequest):
    """生成开文素材包"""
    collection = load_collection()
    
    if req.item_ids:
        collected_items = [c for c in collection if c.get("item_id") in req.item_ids]
    else:
        collected_items = collection
    
    pack = generate_starter_pack(req.genre, collected_items)
    
    # 保存素材包
    pack_file = BASE_DIR / "data" / f"starter_pack_{req.genre}_{datetime.now().strftime('%Y%m%d')}.json"
    with open(pack_file, "w", encoding="utf-8") as f:
        json.dump(pack, f, ensure_ascii=False, indent=2)
    
    return {
        "status": "ok",
        "genre": req.genre,
        "pack": pack,
        "file": str(pack_file),
    }


@app.get("/api/dashboard")
async def get_dashboard():
    """故事仪表盘数据"""
    data = load_data()
    collection = load_collection()
    
    if not data:
        return {"status": "empty"}
    
    # 统计各故事核分类
    category_stats = {}
    score_distribution = {"0-20": 0, "20-40": 0, "40-60": 0, "60-80": 0, "80-100": 0}
    top_items = []
    
    for platform, items in data.items():
        for item in items:
            analysis = item.get("story_analysis", {})
            score = analysis.get("story_score", 0)
            
            for cat in analysis.get("story_categories", []):
                cat_name = cat["category"]
                if cat_name not in category_stats:
                    category_stats[cat_name] = {"count": 0, "keywords": set()}
                category_stats[cat_name]["count"] += 1
                for kw in cat["matched_keywords"]:
                    category_stats[cat_name]["keywords"].add(kw)
            
            if 0 <= score < 20: score_distribution["0-20"] += 1
            elif 20 <= score < 40: score_distribution["20-40"] += 1
            elif 40 <= score < 60: score_distribution["40-60"] += 1
            elif 60 <= score < 80: score_distribution["60-80"] += 1
            elif score >= 80: score_distribution["80-100"] += 1
            
            if score >= 40:
                top_items.append({
                    "title": item.get("title", ""),
                    "platform": platform,
                    "score": score,
                    "categories": [c["category"] for c in analysis.get("story_categories", [])],
                    "url": item.get("url", ""),
                })
    
    top_items.sort(key=lambda x: x["score"], reverse=True)
    
    # 转换set为list
    for cat in category_stats.values():
        cat["keywords"] = list(cat["keywords"])[:10]
    
    return {
        "status": "ok",
        "total_items": sum(len(v) for v in data.values()),
        "story_worthy": sum(1 for items in data.values() for i in items if i.get("story_analysis", {}).get("is_story_worthy")),
        "collected": len(collection),
        "category_stats": category_stats,
        "score_distribution": score_distribution,
        "top_items": top_items[:20],
        "platforms": list(data.keys()),
    }


@app.post("/api/fetch")
async def trigger_fetch(background_tasks: BackgroundTasks):
    background_tasks.add_task(scheduled_fetch)
    return {"status": "ok", "message": "抓取任务已启动"}


@app.get("/api/export")
async def export_excel():
    data = load_data()
    if not data:
        return JSONResponse(status_code=404, content={"status": "error", "message": "暂无数据"})
    
    filename = f"热点原始材料_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    filepath = export_to_excel(data, filename)
    return FileResponse(filepath, filename=filename)


@app.get("/api/export-collection")
async def export_collection():
    """导出已收藏的素材为Excel"""
    collection = load_collection()
    if not collection:
        return JSONResponse(status_code=404, content={"status": "error", "message": "暂无收藏"})
    
    rows = []
    for c in collection:
        parts = c.get("parts", {})
        rows.append({
            "标题": c.get("title", ""),
            "平台": c.get("platform", ""),
            "如果脑洞": c.get("what_if", ""),
            "人设零件": parts.get("人设零件", ""),
            "场景零件": parts.get("场景零件", ""),
            "对白零件": parts.get("对白零件", ""),
            "情节结构零件": parts.get("情节结构零件", ""),
            "选中原文": c.get("selected_text", ""),
            "链接": c.get("url", ""),
            "收藏时间": c.get("collected_at", ""),
        })
    
    df = pd.DataFrame(rows)
    filename = f"我的素材库_{datetime.now().strftime('%Y%m%d')}.xlsx"
    filepath = EXCEL_DIR / filename
    df.to_excel(filepath, index=False, engine='openpyxl')
    
    return FileResponse(filepath, filename=filename)


@app.get("/api/platforms")
async def get_platforms():
    return {
        "platforms": [
            {"id": "微博", "name": "微博热搜", "auto": True, "weight": SOURCE_WEIGHTS.get("微博", 1), "desc": "社会事件、人物特稿"},
            {"id": "知乎热榜", "name": "知乎热榜", "auto": True, "weight": SOURCE_WEIGHTS.get("知乎", 1), "desc": "高赞回答、真实经历、评论神评"},
            {"id": "知乎日报", "name": "知乎日报", "auto": True, "weight": SOURCE_WEIGHTS.get("知乎日报", 1), "desc": "事件过程、处置方式"},
            {"id": "B站", "name": "B站热门", "auto": True, "weight": SOURCE_WEIGHTS.get("B站", 1), "desc": "视频热点、热点日报、高赞评论"},
            {"id": "抖音", "name": "抖音热点", "auto": True, "weight": SOURCE_WEIGHTS.get("抖音", 1), "desc": "短视频热点"},
            {"id": "抖音搜索", "name": "抖音搜索热榜", "auto": True, "weight": SOURCE_WEIGHTS.get("抖音", 1), "desc": "脑洞词条、联想拓展"},
            {"id": "小红书", "name": "小红书热榜", "auto": True, "weight": SOURCE_WEIGHTS.get("小红书", 1), "desc": "轻脑洞、人际矛盾"},
            {"id": "网易新闻", "name": "网易新闻", "auto": True, "weight": SOURCE_WEIGHTS.get("网易新闻", 1), "desc": "社会新闻、非虚构"},
            {"id": "腾讯新闻", "name": "腾讯新闻", "auto": True, "weight": SOURCE_WEIGHTS.get("腾讯新闻", 1), "desc": "社会新闻、立场碰撞"},
            {"id": "豆瓣", "name": "豆瓣", "auto": False, "weight": SOURCE_WEIGHTS.get("豆瓣", 1), "desc": "社死现场、crush瞬间"},
            {"id": "裁判文书网", "name": "裁判文书网", "auto": False, "weight": SOURCE_WEIGHTS.get("裁判文书网", 1), "desc": "法庭人性、真实案件"},
        ]
    }


# ============================================================
# 素材库 API（静态路由必须在动态路由前）
# ============================================================
@app.get("/api/materials/index")
async def api_material_index():
    """获取所有素材库索引"""
    return get_index()


@app.post("/api/materials/auto-fill")
async def api_auto_fill(request: Dict = None):
    """一键自动填入：分析所有热点并填入素材库"""
    if request is None:
        request = {}
    library_names = request.get("library_names", ["all"])
    if "all" in library_names:
        library_names = list(LIBRARY_CONFIG.keys())

    data = load_data()
    all_hotspots = []
    for items in data.values():
        all_hotspots.extend(items)

    results = auto_fill_from_hotspots(all_hotspots, library_names)
    total = sum(results.values())

    return {"status": "ok", "message": f"共填入 {total} 条素材", "results": results, "total": total}


@app.get("/api/materials/export-all")
async def api_export_all_materials():
    """导出所有素材库为一个Excel"""
    try:
        filepath = export_all_to_excel()
        filename = Path(filepath).name
        return FileResponse(filepath, filename=filename)
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


@app.get("/api/materials/{library_name}")
async def api_get_materials(
    library_name: str,
    search: str = Query(""),
    sort_by: str = Query("created_at"),
    order: str = Query("desc"),
    page: int = Query(1),
    page_size: int = Query(50),
):
    """获取指定素材库条目"""
    if library_name not in LIBRARY_CONFIG:
        return JSONResponse(status_code=404, content={"status": "error", "message": "未知素材库"})
    try:
        result = get_items(library_name, search, sort_by, order, page, page_size)
        return {"status": "ok", **result}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


@app.post("/api/materials/{library_name}")
async def api_add_material(library_name: str, item: Dict):
    """添加素材条目"""
    if library_name not in LIBRARY_CONFIG:
        return JSONResponse(status_code=404, content={"status": "error", "message": "未知素材库"})
    try:
        result = add_item(library_name, item)
        return {"status": "ok", "item": result}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


@app.put("/api/materials/{library_name}/{item_id}")
async def api_update_material(library_name: str, item_id: str, updates: Dict):
    """更新素材条目"""
    if library_name not in LIBRARY_CONFIG:
        return JSONResponse(status_code=404, content={"status": "error", "message": "未知素材库"})
    result = update_item(library_name, item_id, updates)
    if not result:
        return JSONResponse(status_code=404, content={"status": "error", "message": "条目不存在"})
    return {"status": "ok", "item": result}


@app.delete("/api/materials/{library_name}/{item_id}")
async def api_delete_material(library_name: str, item_id: str):
    """删除素材条目"""
    if library_name not in LIBRARY_CONFIG:
        return JSONResponse(status_code=404, content={"status": "error", "message": "未知素材库"})
    if delete_item(library_name, item_id):
        return {"status": "ok", "message": "已删除"}
    return JSONResponse(status_code=404, content={"status": "error", "message": "条目不存在"})


@app.get("/api/materials/{library_name}/export")
async def api_export_material(library_name: str):
    """导出指定素材库为Excel"""
    if library_name not in LIBRARY_CONFIG:
        return JSONResponse(status_code=404, content={"status": "error", "message": "未知素材库"})
    try:
        filepath = export_library_to_excel(library_name)
        filename = Path(filepath).name
        return FileResponse(filepath, filename=filename)
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


@app.on_event("startup")
async def startup_event():
    print("=" * 60)
    print("  里章屿的故事会 - 创作加工车间启动")
    print("=" * 60)
    
    if not DATA_FILE.exists():
        print("[启动] 首次运行，执行抓取...")
        await scheduled_fetch()
    else:
        print(f"[启动] 已加载数据")
    
    asyncio.create_task(schedule_task())
    print("[启动] 定时任务已启动 (08:00 / 20:00)")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
