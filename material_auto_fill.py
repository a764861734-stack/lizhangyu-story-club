#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
热点自动填入引擎
从热点数据中自动提取内容填入13个素材库
"""

import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from material_manager import load_library, save_library, add_item

BASE_DIR = Path(__file__).parent


def auto_fill_from_hotspots(hotspots: List[Dict], library_names: Optional[List[str]] = None) -> Dict:
    """对所有热点执行自动填入

    Args:
        hotspots: 热点条目列表（扁平化后的）
        library_names: 要填入的库名列表，None或["all"]表示全部

    Returns:
        { "hot_meme": 5, "conflict": 3, ... }
    """
    if library_names is None or "all" in library_names:
        library_names = [
            "hot_meme", "conflict", "hook", "reversal", "character",
            "scene", "legal_risk", "vocabulary", "emotion", "scenery",
            "action", "dialogue", "quote",
        ]

    results = {}
    for lib_name in library_names:
        try:
            count = _auto_fill_library(lib_name, hotspots)
            results[lib_name] = count
        except Exception as e:
            print(f"自动填入 {lib_name} 失败: {e}")
            results[lib_name] = 0

    return results


def _auto_fill_library(library_name: str, hotspots: List[Dict]) -> int:
    """对指定素材库执行自动填入，返回新增条目数"""
    extractors = {
        "hot_meme": _extract_memes,
        "conflict": _extract_conflicts,
        "hook": _extract_hooks,
        "reversal": _extract_reversals,
        "character": _extract_characters,
        "scene": _extract_scenes,
        "legal_risk": _extract_legal_risks,
        "vocabulary": _extract_vocabulary,
        "emotion": _extract_emotions,
        "scenery": _extract_scenery,
        "action": _extract_actions,
        "dialogue": _extract_dialogues,
        "quote": _extract_quotes,
    }

    extract_func = extractors.get(library_name)
    if not extract_func:
        return 0

    # 加载已有数据用于去重
    existing_data = load_library(library_name)
    existing_ids = {item.get("source_hotspot_id") for item in existing_data["items"] if item.get("source_hotspot_id")}

    count = 0
    for hotspot in hotspots:
        items = extract_func(hotspot)
        for item in items:
            # 去重
            if item.get("source_hotspot_id") and item["source_hotspot_id"] in existing_ids:
                continue

            # 过滤空内容
            has_content = False
            for k, v in item.items():
                if k not in ("id", "source", "created_at", "updated_at", "source_hotspot_id", "source_title") and v:
                    has_content = True
                    break

            if not has_content:
                continue

            add_item(library_name, item)
            if item.get("source_hotspot_id"):
                existing_ids.add(item["source_hotspot_id"])
            count += 1

    return count


def _make_item(hotspot: Dict, **extra) -> Dict:
    """创建带有来源信息的素材条目"""
    title = hotspot.get("title", "")
    hotspot_id = f"{hotspot.get('platform','')}_{hotspot.get('rank','')}_{title[:20]}"

    item = {
        "source": f"auto_from_hotspot",
        "source_hotspot_id": hotspot_id,
        "source_title": title,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    item.update(extra)
    return item


# ============================================================
# 各素材库提取函数
# ============================================================
def _extract_memes(hotspot: Dict) -> List[Dict]:
    """提取热梗素材"""
    items = []
    title = hotspot.get("title", "")
    content = hotspot.get("content", "")
    hot_type = hotspot.get("hot_type", "")
    analysis = hotspot.get("story_analysis", {})
    story_type = analysis.get("story_type", "")
    emotion_density = analysis.get("emotion_density", 0)
    categories = analysis.get("story_categories", [])

    # 脑洞词条直接提取
    if hot_type == "脑洞词条" or "梗" in title or "热梗" in title:
        item = _make_item(hotspot,
            type_tag=hot_type,
            source_platform=hotspot.get("platform", ""),
            core_conflict=content[:200] if content else title,
            adaptation_direction=story_type,
            multi_platform_heat=hotspot.get("heat", ""),
            suitable_plot=content[:200] if content else title,
        )
        items.append(item)

    # 标题含热搜/讨论关键词的也提取
    if any(kw in title for kw in ["彩礼", "出轨", "离婚", "相亲", "渣", "翻车", "塌房", "反转", "逆袭", "替身"]):
        item = _make_item(hotspot,
            type_tag="社会热梗",
            source_platform=hotspot.get("platform", ""),
            core_conflict=content[:200] if content else title,
            adaptation_direction=story_type,
            sweet_angst_index="5" if emotion_density > 0.5 else "3",
            multi_platform_heat=hotspot.get("heat", ""),
            suitable_plot=content[:200] if content else title,
        )
        items.append(item)

    return items


def _extract_conflicts(hotspot: Dict) -> List[Dict]:
    """提取冲突素材"""
    items = []
    analysis = hotspot.get("story_analysis", {})
    categories = analysis.get("story_categories", [])
    emotion_density = analysis.get("emotion_density", 0)
    content = hotspot.get("content", "")
    title = hotspot.get("title", "")

    # 从故事核分类中提取
    for cat in categories:
        if cat.get("category") in ("情感冲突", "社会冲突") and emotion_density > 0:
            item = _make_item(hotspot,
                conflict_type=cat.get("category", ""),
                source_platform=hotspot.get("platform", ""),
                core_contradiction=content[:200] if content else title,
                emotion_curve=f"峰值{emotion_density}",
                suitable_relationship=cat.get("story_type", ""),
                risk_level="★★" if emotion_density > 0.3 else "★",
                adaptation_direction=cat.get("story_type", ""),
                suitable_plot=content[:200] if content else title,
            )
            items.append(item)
            break  # 每个热点只取一个冲突

    return items


def _extract_hooks(hotspot: Dict) -> List[Dict]:
    """提取钩子素材"""
    items = []
    analysis = hotspot.get("story_analysis", {})
    score = analysis.get("story_score", 0)
    categories = analysis.get("story_categories", [])
    title = hotspot.get("title", "")

    if score >= 30:
        # 根据分类推断钩子类型
        hook_type = "悬念"
        cat_names = [c.get("category", "") for c in categories]
        if "猎奇与反转" in cat_names:
            hook_type = "转折"
        elif "情感冲突" in cat_names:
            hook_type = "情绪"
        elif "社会冲突" in cat_names:
            hook_type = "信息"

        item = _make_item(hotspot,
            hook_type=hook_type,
            type_tag=",".join(c.get("category","") for c in categories[:2]),
            core_element=title,
            emotion_orientation="虐" if score > 60 else "甜虐平衡",
            hook_density="中" if score > 50 else "低",
            suitable_plot=hotspot.get("content", "")[:200],
        )
        items.append(item)

    return items


def _extract_reversals(hotspot: Dict) -> List[Dict]:
    """提取反转素材"""
    items = []
    analysis = hotspot.get("story_analysis", {})
    categories = analysis.get("story_categories", [])
    content = hotspot.get("content", "")
    title = hotspot.get("title", "")

    for cat in categories:
        if cat.get("category") == "猎奇与反转":
            item = _make_item(hotspot,
                reversal_type="猎奇反转",
                surface_presentation=title,
                truth_reveal=content[:300] if content else title,
                emotion_impact="★★★★" if analysis.get("story_score", 0) > 50 else "★★★",
                suitable_genre=cat.get("story_type", ""),
                suitable_plot=content[:200] if content else title,
            )
            items.append(item)
            break

    return items


def _extract_characters(hotspot: Dict) -> List[Dict]:
    """提取人设素材"""
    items = []
    content = hotspot.get("content", "")
    title = hotspot.get("title", "")

    if not content:
        return items

    # 简单的人物提取：找"XX人"、"XX者"、"XX男/女"等
    person_patterns = [
        r'([\u4e00-\u9fa5]{2,4}(?:女|男|人|者|主|角|手|方|夫|妻|母|父|儿|子|女|孩|生|师|长|员))',
        r'(?:女主|男主|主角|反派|配角)[\u4e00-\u9fa5]{0,8}',
    ]

    found_persons = set()
    for pattern in person_patterns:
        matches = re.findall(pattern, content)
        for m in matches:
            if isinstance(m, tuple):
                m = m[0]
            if len(m) >= 2 and m not in found_persons:
                found_persons.add(m)

    if found_persons:
        item = _make_item(hotspot,
            role_positioning="、".join(list(found_persons)[:3]),
            surface_traits=title,
            occupation_identity=list(found_persons)[0] if found_persons else "",
            suitable_plot=content[:200],
        )
        items.append(item)

    return items


def _extract_scenes(hotspot: Dict) -> List[Dict]:
    """提取场景素材"""
    items = []
    content = hotspot.get("content", "")
    title = hotspot.get("title", "")
    analysis = hotspot.get("story_analysis", {})

    if not content or analysis.get("story_score", 0) < 20:
        return items

    # 提取场景关键词
    scene_keywords = {
        "法庭": "法庭对峙",
        "医院": "医院场景",
        "婚礼": "婚礼场景",
        "葬礼": "葬礼场景",
        "办公室": "办公室场景",
        "深夜": "深夜独处",
        "餐厅": "餐厅场景",
        "学校": "校园场景",
        "地铁": "公共交通",
        "机场": "机场离别",
        "雨中": "雨中场景",
        "海边": "海边场景",
        "电话": "电话对峙",
    }

    for kw, scene_type in scene_keywords.items():
        if kw in content or kw in title:
            item = _make_item(hotspot,
                scene_type=scene_type,
                visual_focus=content[:200],
                suitable_plot=content[:200],
                emotion_intensity=str(analysis.get("story_score", 30)),
            )
            items.append(item)
            break

    return items


def _extract_legal_risks(hotspot: Dict) -> List[Dict]:
    """提取法律风险素材"""
    items = []
    platform = hotspot.get("platform", "")
    content = hotspot.get("content", "")
    title = hotspot.get("title", "")

    legal_keywords = ["判决", "法院", "离婚", "合同", "协议", "继承", "赔偿", "诈骗", "侵权", "婚姻", "财产", "抚养"]

    if platform == "裁判文书网" or any(kw in (title + content) for kw in legal_keywords):
        item = _make_item(hotspot,
            risk_type="婚姻纠纷" if any(kw in title for kw in ["婚姻","离婚","继承"]) else "民事纠纷",
            legal_basis="民法典相关",
            trigger_condition=content[:200] if content else title,
            reality_prototype=title,
            adaptation_plan="建议将具体法律细节模糊化处理",
            suitable_plot=content[:200] if content else title,
        )
        items.append(item)

    return items


def _extract_vocabulary(hotspot: Dict) -> List[Dict]:
    """提取词汇素材"""
    items = []
    analysis = hotspot.get("story_analysis", {})
    keywords = analysis.get("matched_keywords", [])
    categories = analysis.get("story_categories", [])

    for kw in keywords[:5]:
        item = _make_item(hotspot,
            core_word=kw,
            category=categories[0].get("category", "") if categories else "",
            suitable_genre=analysis.get("story_type", ""),
        )
        items.append(item)

    return items


def _extract_emotions(hotspot: Dict) -> List[Dict]:
    """提取情绪素材"""
    items = []
    analysis = hotspot.get("story_analysis", {})
    emotion_density = analysis.get("emotion_density", 0)
    categories = analysis.get("story_categories", [])
    title = hotspot.get("title", "")

    if emotion_density > 0.5:
        # 从分类推断情绪类型
        emotion_map = {
            "情感冲突": "愤怒/悲伤",
            "社会冲突": "焦虑/无力感",
            "猎奇与反转": "震惊/好奇",
        }
        emotion_type = "复杂情绪"
        for cat in categories:
            emotion_type = emotion_map.get(cat.get("category", ""), emotion_type)
            break

        item = _make_item(hotspot,
            core_emotion=emotion_type,
            intensity_level=str(round(emotion_density * 10, 1)),
            suitable_scene=title,
            case_source=hotspot.get("platform", ""),
        )
        items.append(item)

    return items


def _extract_scenery(hotspot: Dict) -> List[Dict]:
    """提取景色素材"""
    items = []
    content = hotspot.get("content", "")
    title = hotspot.get("title", "")

    if not content:
        return items

    # 提取时间/地点描述
    time_patterns = ["深夜", "清晨", "黄昏", "傍晚", "黎明", "午夜", "午后", "凌晨"]
    place_patterns = ["城市", "乡村", "山间", "海边", "小镇", "都市", "废墟", "花园", "城堡"]

    time_found = [t for t in time_patterns if t in content or t in title]
    place_found = [p for p in place_patterns if p in content or p in title]

    if time_found or place_found:
        spacetime = f"{','.join(time_found[:2])}的{','.join(place_found[:2])}" if place_found else ",".join(time_found[:2])
        item = _make_item(hotspot,
            spacetime_coordinate=spacetime,
            optical_description=content[:200],
            dynamic_element=title,
            era_tag="当代",
        )
        items.append(item)

    return items


def _extract_actions(hotspot: Dict) -> List[Dict]:
    """提取动作素材"""
    items = []
    content = hotspot.get("content", "")
    title = hotspot.get("title", "")

    if not content:
        return items

    # 提取动作相关描述
    action_patterns = [
        r'([\u4e00-\u9fa5]+(?:推|拉|打|摔|冲|闯|撕|砸|拍|踢|夺|追|逃|躲|藏|翻|跳|爬|钻|扔|丢|扯|拽|拖|抱|搂|吻|咬|哭|笑|怒|吼))',
    ]

    actions_found = []
    for pattern in action_patterns:
        matches = re.findall(pattern, content)
        for m in matches:
            if isinstance(m, tuple):
                m = m[0]
            if len(m) >= 3 and m not in actions_found:
                actions_found.append(m)

    if actions_found:
        item = _make_item(hotspot,
            main_action=actions_found[0] if actions_found else "",
            scene_type=title,
            chain_reaction="、".join(actions_found[:3]),
            rhythm_value="3",
        )
        items.append(item)

    return items


def _extract_dialogues(hotspot: Dict) -> List[Dict]:
    """提取对话素材"""
    items = []
    comments = hotspot.get("top_comments", [])
    title = hotspot.get("title", "")

    for comment in comments[:3]:
        # 去除点赞数前缀
        clean = re.sub(r'^\[\d+赞\]\s*', '', comment).strip()
        if not clean:
            continue

        # 寻找潜台词/反讽
        item = _make_item(hotspot,
            surface_dialogue=clean,
            conflict_type="社会讨论",
            information_density="高" if len(clean) > 30 else "中",
            source_chapter=title,
        )

        # 如果是知乎评论，可能有深度讨论
        if "但" in clean or "然而" in clean or "其实" in clean:
            item["subtext"] = "表面认同，实则质疑"

        items.append(item)

    return items


def _extract_quotes(hotspot: Dict) -> List[Dict]:
    """提取金句素材"""
    items = []
    comments = hotspot.get("top_comments", [])
    title = hotspot.get("title", "")
    analysis = hotspot.get("story_analysis", {})

    for comment in comments[:3]:
        clean = re.sub(r'^\[\d+赞\]\s*', '', comment).strip()
        if not clean or len(clean) < 10:
            continue

        # 判断是否像金句（有一定长度、有修辞感）
        has_rhetoric = any(kw in clean for kw in ["是", "不是", "就像", "仿佛", "如同", "原来", "终于", "永远", "从未"])

        if has_rhetoric or len(clean) > 30:
            item = _make_item(hotspot,
                quote_content=clean,
                type_tag="网友神评",
                cross_library_impact=str(min(10, round(analysis.get("emotion_density", 0) * 10 + 3))),
                suitable_plot=title,
            )
            items.append(item)

    return items
