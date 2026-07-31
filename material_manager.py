#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
素材库管理器 - 通用CRUD操作 + 索引管理 + Excel导出
"""

import json
import uuid
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from material_schemas import LIBRARY_CONFIG, LIBRARY_GROUPS, ALL_LIBRARY_KEYS

BASE_DIR = Path(__file__).parent
MATERIAL_DIR = BASE_DIR / "data" / "material_archive"
INDEX_FILE = MATERIAL_DIR / "index.json"


# ============================================================
# 初始化
# ============================================================
def init_all_libraries():
    """初始化所有素材库文件（如果不存在）"""
    MATERIAL_DIR.mkdir(parents=True, exist_ok=True)

    for key in ALL_LIBRARY_KEYS:
        filepath = MATERIAL_DIR / f"{key}.json"
        if not filepath.exists():
            data = {"meta": {"name": LIBRARY_CONFIG[key]["name"], "version": "1.0", "total": 0, "updated_at": datetime.now().isoformat()}, "items": []}
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    rebuild_index()


def rebuild_index():
    """重建素材库索引"""
    index = {}
    for key in ALL_LIBRARY_KEYS:
        filepath = MATERIAL_DIR / f"{key}.json"
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            index[key] = {
                "name": LIBRARY_CONFIG[key]["name"],
                "group": LIBRARY_CONFIG[key]["group"],
                "icon": LIBRARY_CONFIG[key]["icon"],
                "total": data.get("meta", {}).get("total", len(data.get("items", []))),
                "updated_at": data.get("meta", {}).get("updated_at", ""),
            }

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


# ============================================================
# 基础读写
# ============================================================
def load_library(library_name: str) -> Dict:
    """加载指定素材库"""
    if library_name not in LIBRARY_CONFIG:
        raise ValueError(f"未知素材库: {library_name}")

    filepath = MATERIAL_DIR / f"{library_name}.json"
    if not filepath.exists():
        init_all_libraries()

    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_library(library_name: str, data: Dict):
    """保存指定素材库"""
    data["meta"]["total"] = len(data.get("items", []))
    data["meta"]["updated_at"] = datetime.now().isoformat()

    filepath = MATERIAL_DIR / f"{library_name}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    rebuild_index()


# ============================================================
# CRUD
# ============================================================
def get_items(library_name: str, search: str = "", sort_by: str = "created_at",
              order: str = "desc", page: int = 1, page_size: int = 50) -> Dict:
    """分页获取素材库条目"""
    data = load_library(library_name)
    items = data.get("items", [])

    # 搜索
    if search:
        search_lower = search.lower()
        filtered = []
        for item in items:
            # 在所有字符串字段中搜索
            match = False
            for k, v in item.items():
                if isinstance(v, str) and search_lower in v.lower():
                    match = True
                    break
            if match:
                filtered.append(item)
        items = filtered

    # 排序
    reverse = order == "desc"
    items.sort(key=lambda x: x.get(sort_by, ""), reverse=reverse)

    # 分页
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    paged_items = items[start:end]

    return {
        "meta": data.get("meta", {}),
        "items": paged_items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size),
    }


def add_item(library_name: str, item: Dict) -> Dict:
    """添加条目到素材库"""
    data = load_library(library_name)

    item["id"] = str(uuid.uuid4())
    item["created_at"] = datetime.now().isoformat()
    item["updated_at"] = datetime.now().isoformat()

    # 自动生成编号
    if not item.get("code"):
        config = LIBRARY_CONFIG[library_name]
        prefix_map = {
            "hot_meme": "RG", "conflict": "CT", "hook": "GZ",
            "reversal": "FZ", "character": "RS", "scene": "CJ",
            "legal_risk": "FL", "vocabulary": "CH", "emotion": "QX",
            "scenery": "JS", "action": "DZ", "dialogue": "DH", "quote": "JJ",
        }
        prefix = prefix_map.get(library_name, "XX")
        existing = [i for i in data["items"] if i.get("code", "").startswith(f"{prefix}-")]
        next_num = len(existing) + 1
        item["code"] = f"{prefix}-{datetime.now().strftime('%Y')}-{next_num:03d}"

    data["items"].append(item)
    save_library(library_name, data)

    return item


def update_item(library_name: str, item_id: str, updates: Dict) -> Optional[Dict]:
    """更新素材库条目"""
    data = load_library(library_name)

    for item in data["items"]:
        if item.get("id") == item_id:
            item.update(updates)
            item["id"] = item_id  # 不允许修改id
            item["updated_at"] = datetime.now().isoformat()
            save_library(library_name, data)
            return item

    return None


def delete_item(library_name: str, item_id: str) -> bool:
    """删除素材库条目"""
    data = load_library(library_name)
    original_len = len(data["items"])
    data["items"] = [i for i in data["items"] if i.get("id") != item_id]

    if len(data["items"]) < original_len:
        save_library(library_name, data)
        return True
    return False


def get_index() -> Dict:
    """获取所有素材库索引"""
    if not INDEX_FILE.exists():
        init_all_libraries()

    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        index = json.load(f)

    return {
        "libraries": index,
        "groups": [{"key": g["key"], "name": g["name"], "libraries": g["libraries"]} for g in LIBRARY_GROUPS],
    }


# ============================================================
# Excel 导出
# ============================================================
def export_library_to_excel(library_name: str) -> str:
    """导出指定素材库为Excel"""
    if library_name not in LIBRARY_CONFIG:
        raise ValueError(f"未知素材库: {library_name}")

    config = LIBRARY_CONFIG[library_name]
    data = load_library(library_name)
    items = data.get("items", [])

    if not items:
        raise ValueError(f"{config['name']}暂无数据")

    # 构建行数据
    rows = []
    for item in items:
        row = {}
        for field in config["fields"]:
            row[field["label"]] = item.get(field["key"], "")
        rows.append(row)

    df = pd.DataFrame(rows)
    filename = f"{config['name']}_{datetime.now().strftime('%Y%m%d')}.xlsx"
    filepath = BASE_DIR / "exports" / filename
    filepath.parent.mkdir(exist_ok=True)

    df.to_excel(filepath, index=False, engine="openpyxl")

    return str(filepath)


def export_all_to_excel() -> str:
    """导出所有素材库为一个Excel（每个库一个Sheet）"""
    filename = f"全部素材库_{datetime.now().strftime('%Y%m%d')}.xlsx"
    filepath = BASE_DIR / "exports" / filename
    filepath.parent.mkdir(exist_ok=True)

    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        for key in ALL_LIBRARY_KEYS:
            config = LIBRARY_CONFIG[key]
            data = load_library(key)
            items = data.get("items", [])

            if items:
                rows = []
                for item in items:
                    row = {}
                    for field in config["fields"]:
                        row[field["label"]] = item.get(field["key"], "")
                    rows.append(row)

                df = pd.DataFrame(rows)
                sheet_name = config["name"][:31]
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            else:
                pd.DataFrame().to_excel(writer, sheet_name=config["name"][:31], index=False)

    return str(filepath)


# 初始化
init_all_libraries()
