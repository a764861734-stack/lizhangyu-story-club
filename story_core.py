#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
里章屿的故事会 - 故事核关键词库 & 智能筛选器
24字故事核：情感冲突 / 社会冲突 / 猎奇与反转
"""

from typing import List, Dict, Tuple
import re


# ============================================================
# 故事核关键词库 — 平台的"瞄准镜"
# ============================================================
STORY_CORE = {
    # === 一、情感冲突 ===
    "情感冲突": {
        "description": "婆媳、彩礼、出轨、扶弟魔、原生家庭之痛",
        "keywords": [
            # 婚恋家庭
            "离婚", "出轨", "小三", "前任", "婆媳", "婆婆", "儿媳", "扶弟魔",
            "彩礼", "嫁妆", "净身出户", "婚内", "婚姻", "复婚", "再婚",
            "重男轻女", "偏心", "原生家庭", "家暴", "冷暴力",
            # 恋爱情感
            "恋爱", "分手", "复合", "暗恋", "crush", "相亲", "逼婚",
            "异地恋", "网恋", "骗婚", "杀猪盘", "PUA",
            # 亲子
            "抚养权", "探望权", "私生子", "非亲生", "亲子鉴定",
            "遗弃", "收养", "寻亲", "失散",
        ],
        "weight": 3,
        "story_type": "现言, 婚恋, 家庭伦理",
    },

    # === 二、社会冲突 ===
    "社会冲突": {
        "description": "职场不公、法律判决、行业潜规则、阶层差异",
        "keywords": [
            # 法律判决
            "法院", "判决", "判了", "庭审", "起诉", "律师", "被告", "原告",
            "上诉", "申诉", "打官司", "劳动仲裁", "立案", "强制执行",
            "净身出户", "赔偿", "索赔", "违约金", "竞业限制",
            # 职场
            "职场", "裁员", "辞退", "辞职", "加班", "996", "007",
            "老板", "上司", "同事", "背锅", "甩锅", "穿小鞋",
            "职场霸凌", "性骚扰", "潜规则", "内卷", "PUA",
            # 阶层
            "富二代", "穷", "豪门", "体制内", "底层", "精英",
            "农民工", "外卖", "快递", "保洁", "保姆", "护工",
            "阶级", "阶层", "小镇做题家", "凤凰男", "孔雀女",
            # 行业
            "黑幕", "潜规则", "行业", "内幕", "曝光", "实名举报",
        ],
        "weight": 3,
        "story_type": "现言, 职场, 商战, 悬疑",
    },

    # === 三、猎奇与反转 ===
    "猎奇与反转": {
        "description": "匪夷所思的真实事件、感人的小人物故事、惊天大反转",
        "keywords": [
            # 反转
            "反转", "震惊", "没想到", "竟然", "居然", "真相", "秘密",
            "背后", "翻案", "打脸", "真面目", "伪装", "冒充",
            # 猎奇
            "奇葩", "离谱", "匪夷所思", "罕见", "罕见病", "罕见职业",
            "边缘", "地下", "灰色", "黑色", "隐秘",
            # 感人
            "感动", "泪目", "心疼", "温暖", "坚守", "一生",
            "老人", "孩子", "单亲妈妈", "留守儿童",
            # 悬疑
            "失踪", "死亡", "凶手", "作案", "诈骗", "骗局",
            "盗窃", "抢劫", "绑架", "谋杀",
        ],
        "weight": 2,
        "story_type": "悬疑, 幻言, 奇幻, 现言",
    },
}


# ============================================================
# 来源权重 — 高权重来源置顶
# ============================================================
SOURCE_WEIGHTS = {
    "裁判文书网": 10,
    "天才捕手计划": 9,
    "真实故事计划": 9,
    "知乎日报": 7,
    "知乎": 6,
    "网易新闻": 5,
    "腾讯新闻": 5,
    "微博": 4,
    "B站": 3,
    "抖音": 3,
    "小红书": 3,
    "豆瓣": 4,
}


# ============================================================
# 情感浓度检测词汇
# ============================================================
EMOTION_WORDS = [
    "愤怒", "气死", "恶心", "无语", "离谱", "可怕", "震惊",
    "哭", "泪", "心疼", "难受", "崩溃", "绝望",
    "爽", "活该", "报应", "大快人心",
    "爱", "喜欢", "甜", "暖",
    "恨", "讨厌", "恶心", "鄙视",
    "怕", "慌", "紧张", "焦虑",
    "惊", "吓", "不敢相信",
]


# ============================================================
# 智能筛选器
# ============================================================
def analyze_hotspot(title: str, content: str = "", comments: List[str] = None) -> Dict:
    """
    分析一条热点，返回故事核心分类、权重、情感浓度等
    """
    text = f"{title} {content}"
    if comments:
        text += " " + " ".join(comments)
    
    matched_categories = []
    matched_keywords = []
    total_weight = 0
    
    for category, config in STORY_CORE.items():
        matched = []
        for kw in config["keywords"]:
            if kw in text:
                matched.append(kw)
        
        if matched:
            matched_categories.append({
                "category": category,
                "description": config["description"],
                "matched_keywords": matched,
                "story_type": config["story_type"],
                "weight": config["weight"],
            })
            matched_keywords.extend(matched)
            total_weight += config["weight"]
    
    # 情感浓度
    emotion_count = 0
    if comments:
        comment_text = " ".join(comments)
    else:
        comment_text = text
    
    for word in EMOTION_WORDS:
        emotion_count += comment_text.count(word)
    
    emotion_density = emotion_count / max(len(comment_text) / 100, 1)
    
    # 故事感评分 (0-100)
    story_score = 0
    story_score += min(total_weight * 10, 50)  # 关键词权重最多50分
    story_score += min(len(matched_keywords) * 5, 25)  # 匹配关键词数量最多25分
    story_score += min(int(emotion_density * 10), 25)  # 情感浓度最多25分
    
    return {
        "story_categories": matched_categories,
        "matched_keywords": list(set(matched_keywords)),
        "story_score": min(story_score, 100),
        "emotion_density": round(emotion_density, 2),
        "is_story_worthy": story_score >= 20,
        "story_type": ", ".join(set(
            c["story_type"] for c in matched_categories
        )) if matched_categories else "",
    }


def get_source_weight(platform: str) -> int:
    """获取来源权重"""
    return SOURCE_WEIGHTS.get(platform, 1)


def filter_by_story_core(items: List[Dict], min_score: int = 20) -> List[Dict]:
    """按故事核筛选，返回评分达标的热点"""
    filtered = []
    for item in items:
        analysis = analyze_hotspot(
            item.get("title", ""),
            item.get("content", ""),
            item.get("top_comments", []),
        )
        if analysis["story_score"] >= min_score:
            item["story_analysis"] = analysis
            item["source_weight"] = get_source_weight(item.get("platform", ""))
            filtered.append(item)
    
    # 按故事评分 + 来源权重排序
    filtered.sort(
        key=lambda x: (
            x["story_analysis"]["story_score"] + x["source_weight"]
        ),
        reverse=True,
    )
    return filtered


def get_keyword_library() -> Dict:
    """返回完整关键词库（供前端展示）"""
    return {
        "story_core": STORY_CORE,
        "source_weights": SOURCE_WEIGHTS,
        "emotion_words": EMOTION_WORDS,
    }


# ============================================================
# "如果"生成器 — 模板化提问
# ============================================================
WHAT_IF_TEMPLATES = {
    "情感冲突": [
        "如果主角是受害者，TA会怎样反击？",
        "如果主角是施害者，TA的动机是什么？",
        "如果这场冲突发生在大结局前夜呢？",
        "如果主角选择原谅，代价是什么？",
        "如果这是一场误会，真相揭开时谁最崩溃？",
    ],
    "社会冲突": [
        "如果主角是那个被不公对待的人，TA会怎么反抗？",
        "如果主角是施压方，TA的弱点在哪里？",
        "如果主角掌握了关键证据，TA会用还是不用？",
        "如果这场冲突发生在主角最脆弱的时候呢？",
        "如果结局是主角赢了官司但输了人生呢？",
    ],
    "猎奇与反转": [
        "如果反转的真相比表面更可怕呢？",
        "如果主角就是那个'匪夷所思'的人呢？",
        "如果这个小人物其实有大秘密呢？",
        "如果感人故事的背后是一个阴谋呢？",
        "如果结局反转再反转，谁才是真正的赢家？",
    ],
}


def generate_what_if(title: str, categories: List[str] = None) -> List[str]:
    """根据标题和分类，生成'如果'提问"""
    if not categories:
        analysis = analyze_hotspot(title)
        categories = [c["category"] for c in analysis["story_categories"]]
    
    if not categories:
        categories = ["猎奇与反转"]  # 默认
    
    prompts = []
    for cat in categories[:2]:  # 最多取2个分类
        if cat in WHAT_IF_TEMPLATES:
            prompts.extend(WHAT_IF_TEMPLATES[cat][:3])
    
    # 通用提问
    prompts.append(f"如果这是我的小说开头，主角是谁？TA想要什么？什么阻止了TA？")
    
    return prompts[:5]  # 最多5条


# ============================================================
# 零件拆解模板
# ============================================================
PART_TEMPLATES = {
    "人设零件": [
        "冷静到可怕的主角",
        "诡辩技巧一流的伪君子",
        "表面普通、内心藏着巨大秘密的反差人物",
        "「这一生太苦」型配角——TA的作不是坏，是扭曲的自我补偿",
    ],
    "场景零件": [
        "庄严肃穆的法庭，字字诛心的判决书",
        "深夜空荡的房间，手机屏幕的微光",
        "众人围观的公开场合，所有人表情凝固在同一瞬间",
    ],
    "对白零件": [
        "「这份协议，是你亲手签的。现在，它就是你的墓碑。」",
        "「那笔钱是我们的共同财产，你拿去养别人，好，原原本本还给我。」",
        "「他们说我不行。他们错了。」",
    ],
    "情节结构零件": [
        "主角在收拾旧物时，无意中发现一张被藏起来的单据",
        "关键谈判时，一方拿出录音证据，瞬间完成极限翻盘",
        "法庭上，监控录像播放完毕，主角轻轻笑了",
    ],
}


def suggest_parts(text: str, category: str = "") -> Dict:
    """根据选中的文字，建议零件拆解方向"""
    parts = {}
    
    for part_type, examples in PART_TEMPLATES.items():
        parts[part_type] = {
            "template": f"【{part_type}】请基于选中的文字填写...",
            "examples": examples[:2],
            "hint": f"从选中文字中提取{part_type.replace('零件', '')}元素",
        }
    
    return parts


# ============================================================
# 跨源关联推荐
# ============================================================
def find_related(item: Dict, all_data: Dict, limit: int = 5) -> List[Dict]:
    """根据一条热点的关键词，在其他平台找关联内容"""
    if not item.get("story_analysis"):
        return []
    
    keywords = item["story_analysis"].get("matched_keywords", [])
    if not keywords:
        # 用标题分词
        keywords = [w for w in re.split(r'[，。！？\s]+', item.get("title", "")) if len(w) > 1]
    
    related = []
    source_platform = item.get("platform", "")
    
    for platform, items in all_data.items():
        # 不推荐同一平台
        if platform == source_platform:
            continue
        
        for other_item in items:
            other_title = other_item.get("title", "") + " " + other_item.get("content", "")
            
            # 关键词匹配
            match_count = sum(1 for kw in keywords if kw in other_title)
            if match_count > 0:
                related.append({
                    "platform": platform,
                    "title": other_item.get("title", ""),
                    "url": other_item.get("url", ""),
                    "match_count": match_count,
                    "content": other_item.get("content", "")[:100],
                })
    
    # 按匹配度排序
    related.sort(key=lambda x: x["match_count"], reverse=True)
    return related[:limit]


# ============================================================
# 开文素材包生成
# ============================================================
def generate_starter_pack(genre: str, collected_items: List[Dict]) -> Dict:
    """
    根据题材标签，从已收录的素材中打包生成《开文素材大纲》
    """
    pack = {
        "genre": genre,
        "generated_at": __import__("datetime").datetime.now().isoformat(),
        "characters": [],
        "scenes": [],
        "dialogues": [],
        "plots": [],
        "hotspots": [],
    }
    
    for item in collected_items:
        # 检查题材匹配
        item_genre = item.get("story_analysis", {}).get("story_type", "")
        if genre.lower() not in item_genre.lower() and genre:
            continue
        
        # 收集各种零件
        parts = item.get("parts", {})
        if parts.get("人设零件"):
            pack["characters"].append({
                "source": item.get("title", ""),
                "content": parts["人设零件"],
            })
        if parts.get("场景零件"):
            pack["scenes"].append({
                "source": item.get("title", ""),
                "content": parts["场景零件"],
            })
        if parts.get("对白零件"):
            pack["dialogues"].append({
                "source": item.get("title", ""),
                "content": parts["对白零件"],
            })
        if parts.get("情节结构零件"):
            pack["plots"].append({
                "source": item.get("title", ""),
                "content": parts["情节结构零件"],
            })
        
        # 脑洞
        if item.get("what_if"):
            pack["hotspots"].append({
                "source": item.get("title", ""),
                "what_if": item["what_if"],
            })
    
    return pack
