#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小说拆解分析模块
支持：章节数据录入 → 智能分析 → 可视化报告
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from pydantic import BaseModel

BASE_DIR = Path(__file__).parent
DECON_DIR = BASE_DIR / "data" / "deconstructions"
DECON_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# Pydantic 模型
# ============================================================
class ChapterData(BaseModel):
    chapter: str
    event: str
    word_count: int
    scene_count: int
    hook_type: str  # 悬念/情绪/信息/转折/无
    hook_detail: str = ""
    emotion: int  # -5 到 +5
    notes: str = ""


class DeconProject(BaseModel):
    id: Optional[str] = None
    title: str
    author: str = ""
    genre: str = ""
    notes: str = ""
    chapters: List[ChapterData] = []
    created_at: str = ""
    updated_at: str = ""


# ============================================================
# 数据持久化
# ============================================================
def get_project_file(project_id: str) -> Path:
    return DECON_DIR / f"{project_id}.json"


def save_project(project: Dict) -> Dict:
    if not project.get("id"):
        project["id"] = f"decon_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}"
    if not project.get("created_at"):
        project["created_at"] = datetime.now().isoformat()
    project["updated_at"] = datetime.now().isoformat()

    filepath = get_project_file(project["id"])
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(project, f, ensure_ascii=False, indent=2)
    return project


def load_project(project_id: str) -> Optional[Dict]:
    filepath = get_project_file(project_id)
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def list_projects() -> List[Dict]:
    projects = []
    for f in sorted(DECON_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        with open(f, "r", encoding="utf-8") as fp:
            p = json.load(fp)
            projects.append({
                "id": p.get("id"),
                "title": p.get("title", ""),
                "author": p.get("author", ""),
                "genre": p.get("genre", ""),
                "chapter_count": len(p.get("chapters", [])),
                "created_at": p.get("created_at", ""),
                "updated_at": p.get("updated_at", ""),
            })
    return projects


def delete_project(project_id: str) -> bool:
    filepath = get_project_file(project_id)
    if filepath.exists():
        filepath.unlink()
        return True
    return False


# ============================================================
# 智能分析引擎
# ============================================================
def analyze_chapters(chapters: List[Dict]) -> Dict:
    if not chapters:
        return {"error": "暂无章节数据"}

    n = len(chapters)

    # 1. 情绪曲线数据
    emotion_data = []
    for i, ch in enumerate(chapters):
        emotion_data.append({
            "chapter": ch.get("chapter", f"第{i+1}章"),
            "emotion": ch.get("emotion", 0),
            "word_count": ch.get("word_count", 0),
        })

    # 2. 情绪统计
    emotions = [ch.get("emotion", 0) for ch in chapters]
    avg_emotion = sum(emotions) / len(emotions) if emotions else 0
    max_emotion = max(emotions) if emotions else 0
    min_emotion = min(emotions) if emotions else 0

    # 情绪波峰波谷（连续变化点）
    peaks = []
    valleys = []
    for i in range(1, len(emotions)):
        if emotions[i] > emotions[i-1] and (i == len(emotions)-1 or emotions[i] >= emotions[i+1]):
            if emotions[i] >= 3:
                peaks.append({"chapter": chapters[i].get("chapter", ""), "emotion": emotions[i]})
        if emotions[i] < emotions[i-1] and (i == len(emotions)-1 or emotions[i] <= emotions[i+1]):
            if emotions[i] <= -3:
                valleys.append({"chapter": chapters[i].get("chapter", ""), "emotion": emotions[i]})

    # 3. 钩子统计
    hook_types = {"悬念": 0, "情绪": 0, "信息": 0, "转折": 0, "无": 0}
    hook_chapters = {ht: [] for ht in hook_types}
    for ch in chapters:
        ht = ch.get("hook_type", "无")
        if ht in hook_types:
            hook_types[ht] += 1
            hook_chapters[ht].append(ch.get("chapter", ""))

    hook_rate = (n - hook_types["无"]) / n * 100 if n > 0 else 0

    # 4. 字数统计
    word_counts = [ch.get("word_count", 0) for ch in chapters]
    avg_words = sum(word_counts) / len(word_counts) if word_counts else 0
    max_words = max(word_counts) if word_counts else 0
    min_words = min(word_counts) if word_counts else 0
    total_words = sum(word_counts)

    # 找出字数异常（超出平均值30%）的章节
    word_outliers = []
    for ch in chapters:
        wc = ch.get("word_count", 0)
        if avg_words > 0 and abs(wc - avg_words) / avg_words > 0.3:
            word_outliers.append({
                "chapter": ch.get("chapter", ""),
                "word_count": wc,
                "deviation": round((wc - avg_words) / avg_words * 100, 1),
            })

    # 5. 场景密度
    scene_counts = [ch.get("scene_count", 0) for ch in chapters]
    avg_scenes = sum(scene_counts) / len(scene_counts) if scene_counts else 0

    scene_density = []
    for ch in chapters:
        wc = ch.get("word_count", 1)
        sc = ch.get("scene_count", 0)
        scene_density.append({
            "chapter": ch.get("chapter", ""),
            "scene_count": sc,
            "density": round(sc / wc * 1000, 2) if wc > 0 else 0,  # 每千字场景数
        })

    # 6. 高潮章节识别（情绪高+字数多+有钩子）
    climax_scores = []
    for i, ch in enumerate(chapters):
        score = 0
        em = ch.get("emotion", 0)
        wc = ch.get("word_count", 0)
        ht = ch.get("hook_type", "无")
        sc = ch.get("scene_count", 0)

        score += em * 10  # 情绪权重
        if avg_words > 0:
            score += (wc / avg_words - 1) * 20  # 字数偏离权重
        if ht != "无":
            score += 15  # 有钩子加分
        score += sc * 5  # 场景数加分

        climax_scores.append({
            "chapter": ch.get("chapter", ""),
            "score": round(score, 1),
            "emotion": em,
            "word_count": wc,
            "hook_type": ht,
        })

    climax_scores.sort(key=lambda x: x["score"], reverse=True)
    top_climax = climax_scores[:5]

    # 7. 前3章分析
    first3 = chapters[:3]
    first3_analysis = {
        "has_strong_opening": False,
        "hook_types": [],
        "avg_emotion": 0,
        "total_words": 0,
    }
    if first3:
        first3_hooks = [ch.get("hook_type", "无") for ch in first3 if ch.get("hook_type", "无") != "无"]
        first3_analysis["has_strong_opening"] = len(first3_hooks) >= 2
        first3_analysis["hook_types"] = first3_hooks
        first3_analysis["avg_emotion"] = round(sum(ch.get("emotion", 0) for ch in first3) / len(first3), 2)
        first3_analysis["total_words"] = sum(ch.get("word_count", 0) for ch in first3)

    # 8. 节奏诊断
    rhythm_issues = []

    # 检查连续平淡
    flat_streak = 0
    flat_start = None
    for i, ch in enumerate(chapters):
        if ch.get("emotion", 0) == 0 and ch.get("hook_type", "无") == "无":
            if flat_streak == 0:
                flat_start = ch.get("chapter", "")
            flat_streak += 1
            if flat_streak >= 3:
                rhythm_issues.append(f"连续{flat_streak}章情绪平淡且无钩子（从{flat_start}开始），建议插入冲突或悬念")
                break
        else:
            flat_streak = 0

    # 检查钩子重复
    hook_sequence = [ch.get("hook_type", "无") for ch in chapters if ch.get("hook_type", "无") != "无"]
    if len(hook_sequence) >= 3:
        for i in range(len(hook_sequence) - 2):
            if hook_sequence[i] == hook_sequence[i+1] == hook_sequence[i+2]:
                rhythm_issues.append(f"钩子类型「{hook_sequence[i]}」连续出现3次以上，建议变换钩子类型增加新鲜感")
                break

    # 检查情绪单调
    if max_emotion - min_emotion < 3 and n >= 5:
        rhythm_issues.append("整体情绪波动较小（峰谷差<3），建议增加情绪起伏")

    # 检查字数波动过大
    if avg_words > 0:
        cv = (sum((wc - avg_words)**2 for wc in word_counts) / len(word_counts))**0.5 / avg_words
        if cv > 0.4:
            rhythm_issues.append(f"章节字数波动较大（变异系数{round(cv,2)}），建议控制单章字数稳定性")

    return {
        "total_chapters": n,
        "total_words": total_words,
        "avg_words_per_chapter": round(avg_words, 0),
        "avg_emotion": round(avg_emotion, 2),
        "emotion_range": {"max": max_emotion, "min": min_emotion},
        "peaks": peaks,
        "valleys": valleys,
        "hook_stats": {
            "distribution": hook_types,
            "rate": round(hook_rate, 1),
            "chapters": hook_chapters,
        },
        "word_stats": {
            "avg": round(avg_words, 0),
            "max": max_words,
            "min": min_words,
            "outliers": word_outliers,
        },
        "scene_stats": {
            "avg": round(avg_scenes, 1),
            "density": scene_density,
        },
        "top_climax": top_climax,
        "first3_analysis": first3_analysis,
        "rhythm_diagnosis": rhythm_issues if rhythm_issues else ["节奏良好，无明显问题"],
        "emotion_curve": emotion_data,
    }


# ============================================================
# Excel 导出
# ============================================================
def export_decon_to_excel(project: Dict) -> str:
    import pandas as pd

    chapters = project.get("chapters", [])
    if not chapters:
        raise ValueError("没有章节数据")

    # Sheet1: 原始数据
    df_data = []
    for ch in chapters:
        df_data.append({
            "章节": ch.get("chapter", ""),
            "主要事件": ch.get("event", ""),
            "字数": ch.get("word_count", 0),
            "场景数": ch.get("scene_count", 0),
            "章末钩子": ch.get("hook_type", ""),
            "钩子详情": ch.get("hook_detail", ""),
            "情绪值": ch.get("emotion", 0),
            "备注": ch.get("notes", ""),
        })
    df = pd.DataFrame(df_data)

    # Sheet2: 分析报告
    analysis = analyze_chapters(chapters)
    report_rows = [
        {"项目": "书名", "值": project.get("title", "")},
        {"项目": "作者", "值": project.get("author", "")},
        {"项目": "类型", "值": project.get("genre", "")},
        {"项目": "总章节数", "值": analysis.get("total_chapters", 0)},
        {"项目": "总字数", "值": analysis.get("total_words", 0)},
        {"项目": "平均每章字数", "值": analysis.get("avg_words_per_chapter", 0)},
        {"项目": "平均情绪值", "值": analysis.get("avg_emotion", 0)},
        {"项目": "情绪最高", "值": analysis.get("emotion_range", {}).get("max", 0)},
        {"项目": "情绪最低", "值": analysis.get("emotion_range", {}).get("min", 0)},
        {"项目": "钩子覆盖率", "值": f"{analysis.get('hook_stats', {}).get('rate', 0)}%"},
        {"项目": "", "值": ""},
        {"项目": "=== 节奏诊断 ===", "值": ""},
    ]
    for issue in analysis.get("rhythm_diagnosis", []):
        report_rows.append({"项目": "诊断", "值": issue})

    report_rows.extend([
        {"项目": "", "值": ""},
        {"项目": "=== 高潮章节 TOP5 ===", "值": ""},
    ])
    for c in analysis.get("top_climax", []):
        report_rows.append({
            "项目": c.get("chapter", ""),
            "值": f"综合得分{c.get('score',0)} | 情绪{c.get('emotion',0)} | 字数{c.get('word_count',0)} | 钩子{c.get('hook_type','')}",
        })

    report_rows.extend([
        {"项目": "", "值": ""},
        {"项目": "=== 前3章分析 ===", "值": ""},
        {"项目": "是否有强开场", "值": "是" if analysis.get("first3_analysis", {}).get("has_strong_opening") else "否"},
        {"项目": "前3章钩子类型", "值": ", ".join(analysis.get("first3_analysis", {}).get("hook_types", []))},
        {"项目": "前3章平均情绪", "值": analysis.get("first3_analysis", {}).get("avg_emotion", 0)},
        {"项目": "前3章总字数", "值": analysis.get("first3_analysis", {}).get("total_words", 0)},
    ])

    df_report = pd.DataFrame(report_rows)

    filename = f"小说拆解_{project.get('title', '未命名')}_{datetime.now().strftime('%Y%m%d')}.xlsx"
    filepath = BASE_DIR / "exports" / filename
    filepath.parent.mkdir(exist_ok=True)

    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="章节数据", index=False)
        df_report.to_excel(writer, sheet_name="分析报告", index=False)

    return str(filepath)
