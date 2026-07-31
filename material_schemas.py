#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
13个素材库的数据模型定义
每个素材库有独立的Pydantic模型和字段配置
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================================
# 基础模型
# ============================================================
class MaterialMeta(BaseModel):
    """素材库元信息"""
    name: str = ""
    version: str = "1.0"
    total: int = 0
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class MaterialBase(BaseModel):
    """所有素材条目的公共字段"""
    id: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    source: str = "manual"
    source_hotspot_id: Optional[str] = None
    source_title: Optional[str] = None


# ============================================================
# 1. 热梗素材库
# ============================================================
class HotMemeItem(MaterialBase):
    code: str = ""
    type_tag: str = ""
    source_platform: str = ""
    core_conflict: str = ""
    emotion_level: str = ""
    adaptation_direction: str = ""
    sweet_angst_index: str = ""
    sweet_angst_balance: str = ""
    suitable_relationship: str = ""
    suitable_chapter: str = ""
    prop_symbol: str = ""
    taboo_redline: str = ""
    multi_platform_heat: str = ""
    foreshadowing_need: str = ""
    reader_expectation: str = ""
    risk_warning: str = ""
    suitable_plot: str = ""


# ============================================================
# 2. 冲突素材库
# ============================================================
class ConflictItem(MaterialBase):
    code: str = ""
    conflict_type: str = ""
    source_platform: str = ""
    reality_prototype: str = ""
    core_contradiction: str = ""
    emotion_curve: str = ""
    suitable_relationship: str = ""
    suitable_scene: str = ""
    risk_level: str = ""
    adaptation_direction: str = ""
    adaptation_case: str = ""
    eruption_scene: str = ""
    resolution_method: str = ""
    emotion_value: str = ""
    foreshadowing_need: str = ""
    suitable_plot: str = ""


# ============================================================
# 3. 钩子素材库
# ============================================================
class HookItem(MaterialBase):
    code: str = ""
    hook_type: str = ""
    placement_position: str = ""
    type_tag: str = ""
    trigger_chapter: str = ""
    core_element: str = ""
    placement_technique: str = ""
    emotion_orientation: str = ""
    recovery_cycle: str = ""
    related_reversal: str = ""
    hook_density: str = ""
    foreshadowing_requirement: str = ""
    modification_direction: str = ""
    risk_warning: str = ""
    suitable_plot: str = ""


# ============================================================
# 4. 反转素材库
# ============================================================
class ReversalItem(MaterialBase):
    code: str = ""
    reversal_type: str = ""
    foreshadowing_clue: str = ""
    eruption_chapter: str = ""
    emotion_impact: str = ""
    logic_check: str = ""
    surface_presentation: str = ""
    truth_reveal: str = ""
    foreshadow_design: str = ""
    adaptation_case: str = ""
    reality_prototype: str = ""
    suitable_genre: str = ""
    risk_barrier: str = ""
    suitable_plot: str = ""


# ============================================================
# 5. 人设基因库
# ============================================================
class CharacterItem(MaterialBase):
    code: str = ""
    role_positioning: str = ""
    surface_traits: str = ""
    hidden_traits: str = ""
    tag: str = ""
    occupation_identity: str = ""
    emotional_obstacle: str = ""
    exclusive_item: str = ""
    signature_action: str = ""
    romance_foreshadow: str = ""
    hidden_connection: str = ""
    hormone_trigger: str = ""
    fatal_flaw: str = ""
    redemption_switch: str = ""
    taboo_boundary: str = ""
    suitable_plot: str = ""


# ============================================================
# 6. 场景库
# ============================================================
class SceneItem(MaterialBase):
    code: str = ""
    scene_type: str = ""
    visual_focus: str = ""
    auditory_detail: str = ""
    tactile_image: str = ""
    olfactory_memory: str = ""
    taste_metaphor: str = ""
    emotion_curve: str = ""
    conflict_trigger: str = ""
    foreshadow_recovery: str = ""
    suitable_plot: str = ""
    data_reference: str = ""
    taboo_tip: str = ""
    emotion_intensity: str = ""


# ============================================================
# 7. 法律风险库
# ============================================================
class LegalRiskItem(MaterialBase):
    code: str = ""
    risk_type: str = ""
    legal_basis: str = ""
    trigger_condition: str = ""
    consequence_severity: str = ""
    reality_prototype: str = ""
    adaptation_plan: str = ""
    prevention_measure: str = ""
    dramatic_technique: str = ""
    suitable_plot: str = ""


# ============================================================
# 8. 词汇库
# ============================================================
class VocabularyItem(MaterialBase):
    code: str = ""
    category: str = ""
    sub_category: str = ""
    core_word: str = ""
    intensity: str = ""
    synesthesia_example: str = ""
    suitable_genre: str = ""
    related_emotion: str = ""
    source_reference: str = ""


# ============================================================
# 9. 情绪库
# ============================================================
class EmotionItem(MaterialBase):
    code: str = ""
    core_emotion: str = ""
    intensity_level: str = ""
    physiological_reaction: str = ""
    micro_expression_code: str = ""
    behavior_mapping: str = ""
    dialogue_feature: str = ""
    suitable_scene: str = ""
    taboo_misuse: str = ""
    case_source: str = ""


# ============================================================
# 10. 景色库
# ============================================================
class SceneryItem(MaterialBase):
    code: str = ""
    spacetime_coordinate: str = ""
    optical_description: str = ""
    acoustic_description: str = ""
    olfactory_level: str = ""
    tactile_feedback: str = ""
    dynamic_element: str = ""
    data_layer: str = ""
    era_tag: str = ""
    related_color_palette: str = ""


# ============================================================
# 11. 动作库
# ============================================================
class ActionItem(MaterialBase):
    code: str = ""
    scene_type: str = ""
    action_level: str = ""
    main_action: str = ""
    chain_reaction: str = ""
    metaphor_meaning: str = ""
    rhythm_value: str = ""
    taboo_combination: str = ""
    classic_case: str = ""


# ============================================================
# 12. 对话库
# ============================================================
class DialogueItem(MaterialBase):
    code: str = ""
    conflict_type: str = ""
    surface_dialogue: str = ""
    subtext: str = ""
    action_anchor: str = ""
    tone_mark: str = ""
    information_density: str = ""
    power_relation: str = ""
    source_chapter: str = ""


# ============================================================
# 13. 金句库
# ============================================================
class QuoteItem(MaterialBase):
    code: str = ""
    quote_content: str = ""
    type_tag: str = ""
    phonetic_structure: str = ""
    metaphor_density: str = ""
    cross_library_impact: str = ""
    related_meme: str = ""
    suitable_plot: str = ""


# ============================================================
# 素材库配置
# ============================================================

# 每个库的中文名、分组、图标、字段定义
LIBRARY_CONFIG: Dict[str, Dict] = {
    "hot_meme": {
        "name": "热梗素材库",
        "group": "story_core",
        "icon": "🔥",
        "model": HotMemeItem,
        "fields": [
            {"key": "code", "label": "编号", "type": "text", "width": "120px"},
            {"key": "type_tag", "label": "类型标签", "type": "text", "width": "140px"},
            {"key": "source_platform", "label": "来源平台", "type": "text", "width": "100px"},
            {"key": "core_conflict", "label": "核心冲突点", "type": "textarea"},
            {"key": "emotion_level", "label": "情感层次", "type": "text", "width": "200px"},
            {"key": "adaptation_direction", "label": "改编方向", "type": "textarea"},
            {"key": "sweet_angst_index", "label": "甜虐指数", "type": "text", "width": "100px"},
            {"key": "sweet_angst_balance", "label": "甜虐平衡指数", "type": "text", "width": "100px"},
            {"key": "suitable_relationship", "label": "适配角色关系", "type": "text", "width": "160px"},
            {"key": "suitable_chapter", "label": "适用章节", "type": "text", "width": "120px"},
            {"key": "prop_symbol", "label": "道具符号", "type": "text", "width": "160px"},
            {"key": "taboo_redline", "label": "禁忌红线", "type": "text", "width": "160px"},
            {"key": "multi_platform_heat", "label": "多平台热度", "type": "text", "width": "120px"},
            {"key": "foreshadowing_need", "label": "伏笔需求", "type": "text", "width": "160px"},
            {"key": "reader_expectation", "label": "读者预期", "type": "text", "width": "160px"},
            {"key": "risk_warning", "label": "风险提示", "type": "text", "width": "160px"},
            {"key": "suitable_plot", "label": "适用情节", "type": "textarea"},
        ],
    },
    "conflict": {
        "name": "冲突素材库",
        "group": "story_core",
        "icon": "⚡",
        "model": ConflictItem,
        "fields": [
            {"key": "code", "label": "编号", "type": "text", "width": "120px"},
            {"key": "conflict_type", "label": "冲突类型", "type": "text", "width": "120px"},
            {"key": "source_platform", "label": "来源平台", "type": "text", "width": "100px"},
            {"key": "reality_prototype", "label": "现实原型", "type": "text", "width": "160px"},
            {"key": "core_contradiction", "label": "核心矛盾", "type": "textarea"},
            {"key": "emotion_curve", "label": "情绪曲线", "type": "text", "width": "200px"},
            {"key": "suitable_relationship", "label": "适配角色关系", "type": "text", "width": "160px"},
            {"key": "suitable_scene", "label": "适用场景", "type": "text", "width": "160px"},
            {"key": "risk_level", "label": "风险等级", "type": "text", "width": "80px"},
            {"key": "adaptation_direction", "label": "改编方向", "type": "textarea"},
            {"key": "adaptation_case", "label": "改编案例", "type": "textarea"},
            {"key": "eruption_scene", "label": "爆发场景", "type": "text", "width": "200px"},
            {"key": "resolution_method", "label": "解决方式", "type": "text", "width": "200px"},
            {"key": "emotion_value", "label": "情绪价值", "type": "text", "width": "160px"},
            {"key": "foreshadowing_need", "label": "伏笔需求", "type": "text", "width": "160px"},
            {"key": "suitable_plot", "label": "适用情节", "type": "textarea"},
        ],
    },
    "hook": {
        "name": "钩子素材库",
        "group": "story_core",
        "icon": "🪝",
        "model": HookItem,
        "fields": [
            {"key": "code", "label": "编号", "type": "text", "width": "120px"},
            {"key": "hook_type", "label": "钩子类型", "type": "text", "width": "120px"},
            {"key": "placement_position", "label": "埋设位置", "type": "text", "width": "160px"},
            {"key": "type_tag", "label": "类型标签", "type": "text", "width": "140px"},
            {"key": "trigger_chapter", "label": "引爆章节", "type": "text", "width": "100px"},
            {"key": "core_element", "label": "核心元素", "type": "text", "width": "160px"},
            {"key": "placement_technique", "label": "埋设手法", "type": "text", "width": "120px"},
            {"key": "emotion_orientation", "label": "情感导向", "type": "text", "width": "160px"},
            {"key": "recovery_cycle", "label": "回收周期", "type": "text", "width": "100px"},
            {"key": "related_reversal", "label": "关联反转", "type": "text", "width": "160px"},
            {"key": "hook_density", "label": "钩子密度", "type": "text", "width": "80px"},
            {"key": "foreshadowing_requirement", "label": "伏笔要求", "type": "text", "width": "160px"},
            {"key": "modification_direction", "label": "修改方向", "type": "text", "width": "160px"},
            {"key": "risk_warning", "label": "风险提示", "type": "text", "width": "160px"},
            {"key": "suitable_plot", "label": "适用情节", "type": "textarea"},
        ],
    },
    "reversal": {
        "name": "反转素材库",
        "group": "story_core",
        "icon": "🔄",
        "model": ReversalItem,
        "fields": [
            {"key": "code", "label": "编号", "type": "text", "width": "120px"},
            {"key": "reversal_type", "label": "反转类型", "type": "text", "width": "140px"},
            {"key": "foreshadowing_clue", "label": "铺垫线索", "type": "textarea"},
            {"key": "eruption_chapter", "label": "爆发章节", "type": "text", "width": "100px"},
            {"key": "emotion_impact", "label": "情感冲击", "type": "text", "width": "100px"},
            {"key": "logic_check", "label": "逻辑校验", "type": "text", "width": "160px"},
            {"key": "surface_presentation", "label": "表面呈现", "type": "textarea"},
            {"key": "truth_reveal", "label": "真相揭露", "type": "textarea"},
            {"key": "foreshadow_design", "label": "伏笔设计（3+线索）", "type": "textarea"},
            {"key": "adaptation_case", "label": "改编案例", "type": "text", "width": "200px"},
            {"key": "reality_prototype", "label": "现实原型", "type": "text", "width": "160px"},
            {"key": "suitable_genre", "label": "适用题材", "type": "text", "width": "160px"},
            {"key": "risk_barrier", "label": "风险屏障", "type": "text", "width": "160px"},
            {"key": "suitable_plot", "label": "适用情节", "type": "textarea"},
        ],
    },
    "character": {
        "name": "人设基因库",
        "group": "character_scene",
        "icon": "👤",
        "model": CharacterItem,
        "fields": [
            {"key": "code", "label": "编号", "type": "text", "width": "120px"},
            {"key": "role_positioning", "label": "角色定位", "type": "text", "width": "160px"},
            {"key": "surface_traits", "label": "表面属性", "type": "text", "width": "200px"},
            {"key": "hidden_traits", "label": "隐藏属性", "type": "text", "width": "200px"},
            {"key": "tag", "label": "标签(MBTI等)", "type": "text", "width": "120px"},
            {"key": "occupation_identity", "label": "职业/身份", "type": "text", "width": "160px"},
            {"key": "emotional_obstacle", "label": "情感障碍", "type": "text", "width": "200px"},
            {"key": "exclusive_item", "label": "专属物品", "type": "text", "width": "160px"},
            {"key": "signature_action", "label": "标志动作/微习惯", "type": "text", "width": "200px"},
            {"key": "romance_foreshadow", "label": "感情线伏笔", "type": "text", "width": "200px"},
            {"key": "hidden_connection", "label": "隐秘关联", "type": "text", "width": "200px"},
            {"key": "hormone_trigger", "label": "荷尔蒙触发点", "type": "text", "width": "200px"},
            {"key": "fatal_flaw", "label": "致命性缺点", "type": "text", "width": "200px"},
            {"key": "redemption_switch", "label": "救赎开关", "type": "text", "width": "200px"},
            {"key": "taboo_boundary", "label": "禁忌边界", "type": "text", "width": "200px"},
            {"key": "suitable_plot", "label": "适用情节", "type": "textarea"},
        ],
    },
    "scene": {
        "name": "场景库",
        "group": "character_scene",
        "icon": "🎬",
        "model": SceneItem,
        "fields": [
            {"key": "code", "label": "编号", "type": "text", "width": "120px"},
            {"key": "scene_type", "label": "场景类型", "type": "text", "width": "140px"},
            {"key": "visual_focus", "label": "视觉焦点", "type": "text", "width": "200px"},
            {"key": "auditory_detail", "label": "听觉细节", "type": "text", "width": "200px"},
            {"key": "tactile_image", "label": "触觉意象", "type": "text", "width": "200px"},
            {"key": "olfactory_memory", "label": "嗅觉记忆", "type": "text", "width": "200px"},
            {"key": "taste_metaphor", "label": "味觉隐喻", "type": "text", "width": "200px"},
            {"key": "emotion_curve", "label": "情感曲线", "type": "text", "width": "200px"},
            {"key": "conflict_trigger", "label": "冲突触发点", "type": "text", "width": "200px"},
            {"key": "foreshadow_recovery", "label": "伏笔回收点", "type": "text", "width": "200px"},
            {"key": "suitable_plot", "label": "适用情节", "type": "textarea"},
            {"key": "data_reference", "label": "数据参考", "type": "text", "width": "200px"},
            {"key": "taboo_tip", "label": "禁忌提示", "type": "text", "width": "160px"},
            {"key": "emotion_intensity", "label": "情感强度", "type": "text", "width": "160px"},
        ],
    },
    "legal_risk": {
        "name": "法律风险库",
        "group": "writing_technique",
        "icon": "⚖️",
        "model": LegalRiskItem,
        "fields": [
            {"key": "code", "label": "编号", "type": "text", "width": "120px"},
            {"key": "risk_type", "label": "风险类型", "type": "text", "width": "140px"},
            {"key": "legal_basis", "label": "法律依据", "type": "text", "width": "200px"},
            {"key": "trigger_condition", "label": "触发条件", "type": "text", "width": "200px"},
            {"key": "consequence_severity", "label": "后果严重性", "type": "text", "width": "100px"},
            {"key": "reality_prototype", "label": "现实原型", "type": "text", "width": "200px"},
            {"key": "adaptation_plan", "label": "改编方案", "type": "textarea"},
            {"key": "prevention_measure", "label": "预防措施", "type": "text", "width": "200px"},
            {"key": "dramatic_technique", "label": "戏剧化技巧", "type": "text", "width": "200px"},
            {"key": "suitable_plot", "label": "适用情节", "type": "textarea"},
        ],
    },
    "vocabulary": {
        "name": "词汇库",
        "group": "writing_technique",
        "icon": "📝",
        "model": VocabularyItem,
        "fields": [
            {"key": "code", "label": "序号", "type": "text", "width": "80px"},
            {"key": "category", "label": "分类", "type": "text", "width": "120px"},
            {"key": "sub_category", "label": "子类", "type": "text", "width": "120px"},
            {"key": "core_word", "label": "核心词汇", "type": "text", "width": "160px"},
            {"key": "intensity", "label": "强度", "type": "text", "width": "80px"},
            {"key": "synesthesia_example", "label": "通感转化示例", "type": "textarea"},
            {"key": "suitable_genre", "label": "适用题材", "type": "text", "width": "160px"},
            {"key": "related_emotion", "label": "关联情绪", "type": "text", "width": "140px"},
            {"key": "source_reference", "label": "出处", "type": "text", "width": "160px"},
        ],
    },
    "emotion": {
        "name": "情绪库",
        "group": "writing_technique",
        "icon": "💭",
        "model": EmotionItem,
        "fields": [
            {"key": "code", "label": "序号", "type": "text", "width": "80px"},
            {"key": "core_emotion", "label": "核心情绪", "type": "text", "width": "140px"},
            {"key": "intensity_level", "label": "强度等级", "type": "text", "width": "80px"},
            {"key": "physiological_reaction", "label": "生理反应", "type": "textarea"},
            {"key": "micro_expression_code", "label": "微表情编码", "type": "text", "width": "120px"},
            {"key": "behavior_mapping", "label": "行为映射", "type": "text", "width": "200px"},
            {"key": "dialogue_feature", "label": "对话特征", "type": "text", "width": "200px"},
            {"key": "suitable_scene", "label": "适用场景", "type": "text", "width": "160px"},
            {"key": "taboo_misuse", "label": "禁忌误用", "type": "text", "width": "200px"},
            {"key": "case_source", "label": "案例来源", "type": "text", "width": "200px"},
        ],
    },
    "scenery": {
        "name": "景色库",
        "group": "writing_technique",
        "icon": "🏞️",
        "model": SceneryItem,
        "fields": [
            {"key": "code", "label": "序号", "type": "text", "width": "80px"},
            {"key": "spacetime_coordinate", "label": "时空坐标", "type": "text", "width": "160px"},
            {"key": "optical_description", "label": "光学描写", "type": "textarea"},
            {"key": "acoustic_description", "label": "声学描写", "type": "textarea"},
            {"key": "olfactory_level", "label": "嗅觉层次", "type": "text", "width": "200px"},
            {"key": "tactile_feedback", "label": "触觉反馈", "type": "text", "width": "200px"},
            {"key": "dynamic_element", "label": "动态元素", "type": "text", "width": "200px"},
            {"key": "data_layer", "label": "数据层（可选）", "type": "text", "width": "200px"},
            {"key": "era_tag", "label": "时代标签", "type": "text", "width": "120px"},
            {"key": "related_color_palette", "label": "关联色卡", "type": "text", "width": "160px"},
        ],
    },
    "action": {
        "name": "动作库",
        "group": "writing_technique",
        "icon": "🏃",
        "model": ActionItem,
        "fields": [
            {"key": "code", "label": "序号", "type": "text", "width": "80px"},
            {"key": "scene_type", "label": "场景类型", "type": "text", "width": "140px"},
            {"key": "action_level", "label": "动作分级", "type": "text", "width": "120px"},
            {"key": "main_action", "label": "主体动作", "type": "textarea"},
            {"key": "chain_reaction", "label": "连带反应", "type": "text", "width": "200px"},
            {"key": "metaphor_meaning", "label": "隐喻意义", "type": "text", "width": "200px"},
            {"key": "rhythm_value", "label": "节奏值(1-5)", "type": "text", "width": "80px"},
            {"key": "taboo_combination", "label": "禁忌组合", "type": "text", "width": "200px"},
            {"key": "classic_case", "label": "经典案例", "type": "text", "width": "200px"},
        ],
    },
    "dialogue": {
        "name": "对话库",
        "group": "writing_technique",
        "icon": "💬",
        "model": DialogueItem,
        "fields": [
            {"key": "code", "label": "序号", "type": "text", "width": "80px"},
            {"key": "conflict_type", "label": "冲突类型", "type": "text", "width": "140px"},
            {"key": "surface_dialogue", "label": "表层对话", "type": "textarea"},
            {"key": "subtext", "label": "潜台词", "type": "textarea"},
            {"key": "action_anchor", "label": "动作锚点", "type": "text", "width": "200px"},
            {"key": "tone_mark", "label": "声调标记", "type": "text", "width": "140px"},
            {"key": "information_density", "label": "信息密度", "type": "text", "width": "140px"},
            {"key": "power_relation", "label": "权力关系", "type": "text", "width": "160px"},
            {"key": "source_chapter", "label": "出处章节", "type": "text", "width": "160px"},
        ],
    },
    "quote": {
        "name": "金句库",
        "group": "writing_technique",
        "icon": "💎",
        "model": QuoteItem,
        "fields": [
            {"key": "code", "label": "编号", "type": "text", "width": "120px"},
            {"key": "quote_content", "label": "金句内容", "type": "textarea"},
            {"key": "type_tag", "label": "类型标签", "type": "text", "width": "140px"},
            {"key": "phonetic_structure", "label": "声韵结构", "type": "text", "width": "160px"},
            {"key": "metaphor_density", "label": "隐喻密度", "type": "text", "width": "80px"},
            {"key": "cross_library_impact", "label": "跨库冲击力", "type": "text", "width": "100px"},
            {"key": "related_meme", "label": "关联热梗", "type": "text", "width": "160px"},
            {"key": "suitable_plot", "label": "适用情节", "type": "textarea"},
        ],
    },
}

# 分组配置
LIBRARY_GROUPS = [
    {"key": "story_core", "name": "故事内核素材库", "libraries": ["hot_meme", "conflict", "hook", "reversal"]},
    {"key": "character_scene", "name": "人物与场景", "libraries": ["character", "scene"]},
    {"key": "writing_technique", "name": "写作技法库", "libraries": ["legal_risk", "vocabulary", "emotion", "scenery", "action", "dialogue", "quote"]},
]

# 所有库的key列表（用于"all"操作）
ALL_LIBRARY_KEYS = list(LIBRARY_CONFIG.keys())
