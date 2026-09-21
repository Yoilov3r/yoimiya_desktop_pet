from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ShopItem:
    key: str
    name: str
    category: str
    price: int
    icon: str
    description: str
    effects: dict[str, float]
    reactions: tuple[str, ...]
    card_group: str


SHOP_ITEMS = {
    "dango": ShopItem(
        "dango",
        "三色团子",
        "甜点",
        3,
        "团",
        "软糯的三色团子，适合忙里偷闲。",
        {"fullness": 0.20, "mood": 0.09},
        (
            "三颗团子三种味道，今天最喜欢哪一颗？",
            "嚼起来软软的，心情也跟着变软啦。",
            "甜甜的，但不腻，刚刚好。",
        ),
        "eat",
    ),
    "rice_ball": ShopItem(
        "rice_ball",
        "甜虾饭团",
        "主食",
        4,
        "饭",
        "有甜虾和芝麻，能补充不少体力。",
        {"fullness": 0.30, "energy": 0.06},
        (
            "饭团包得很结实，吃完一定有力气。",
            "甜虾的味道很有精神！",
            "这一口是认真工作的奖励。",
        ),
        "eat",
    ),
    "firework_candy": ShopItem(
        "firework_candy",
        "烟花糖",
        "甜点",
        2,
        "糖",
        "会在嘴里轻轻噼啪作响的糖果。",
        {"mood": 0.16, "energy": 0.03},
        (
            "嘴里像开了一场小烟花！",
            "噼啪一下，烦恼也散开啦。",
            "好吃，而且很有节日的感觉。",
        ),
        "cheer",
    ),
    "konpeito": ShopItem(
        "konpeito",
        "金平糖",
        "甜点",
        2,
        "星",
        "彩色的星星糖，适合放在小罐子里。",
        {"mood": 0.13, "fullness": 0.05},
        (
            "像把一小把星星倒进嘴里。",
            "每一颗颜色都不一样，挑起来很开心。",
            "甜甜的，衣角好像都亮起来了。",
        ),
        "welcome",
    ),
    "grilled_fish": ShopItem(
        "grilled_fish",
        "烤鱼",
        "主食",
        4,
        "鱼",
        "外皮微焦、里面很嫩，营养均衡。",
        {"fullness": 0.28, "health": 0.05},
        (
            "烤得刚刚好，香味都钻进鼻子里了。",
            "外脆里嫩，这一餐很满足。",
            "吃饱以后，身体也暖暖的。",
        ),
        "eat",
    ),
    "matcha_dango": ShopItem(
        "matcha_dango",
        "抹茶团子",
        "甜点",
        3,
        "茶",
        "微苦的抹茶配上柔软团子。",
        {"fullness": 0.18, "mood": 0.08},
        (
            "抹茶的苦味很清爽，和甜味刚好平衡。",
            "慢慢嚼，茶香会一点点出来。",
            "这个味道很适合安静的下午。",
        ),
        "daydream",
    ),
    "apple_candy": ShopItem(
        "apple_candy",
        "苹果糖",
        "甜点",
        3,
        "果",
        "祭典小摊上的经典甜点。",
        {"mood": 0.16, "fullness": 0.08},
        (
            "外壳亮晶晶的，像一小块红色玻璃。",
            "祭典的味道就是这一口。",
            "咬下去会咔嚓一下，很过瘾。",
        ),
        "cheer",
    ),
    "zousui": ShopItem(
        "zousui",
        "暖胃杂煮",
        "主食",
        5,
        "汤",
        "热汤和蔬菜，疲惫时最合适。",
        {"fullness": 0.34, "health": 0.08, "energy": 0.04},
        (
            "热乎乎的汤喝下去，整个人都放松了。",
            "这一碗很适合累的时候。",
            "肚子里暖暖的，肩膀也没那么紧啦。",
        ),
        "sleep",
    ),
    "milk": ShopItem(
        "milk",
        "温热牛奶",
        "饮品",
        2,
        "奶",
        "温热、柔和，适合睡前。",
        {"fullness": 0.10, "health": 0.05, "energy": 0.04},
        (
            "喝完感觉可以好好睡一觉。",
            "暖暖的，连手指都放松了。",
            "晚安前的一小杯温柔。",
        ),
        "sleep",
    ),
    "tea": ShopItem(
        "tea",
        "清心茶",
        "饮品",
        2,
        "茶",
        "清爽的茶香，有助于重新集中精神。",
        {"energy": 0.09, "focus": 0.08, "mood": 0.04},
        (
            "茶香飘起来以后，脑子也清醒了一点。",
            "先停一下，再继续也不迟。",
            "这一杯适合配一本好看的书。",
        ),
        "study",
    ),
    "firework_book": ShopItem(
        "firework_book",
        "《烟花配方笔记》",
        "书籍",
        6,
        "书",
        "记录颜色、药量和空中形状的工坊笔记。",
        {"knowledge": 0.14, "focus": 0.10},
        (
            "原来这个颜色要这样配，赶紧记下来。",
            "看到新的配方，脑子里已经有烟花形状了。",
            "知识增加了，下一次一定能做得更漂亮。",
        ),
        "study",
    ),
    "inazuma_stories": ShopItem(
        "inazuma_stories",
        "《稻妻怪谈》",
        "书籍",
        5,
        "怪",
        "稻妻各地流传的奇怪故事。",
        {"knowledge": 0.10, "mood": 0.08},
        (
            "这个故事有点吓人，但我还是想看下一页。",
            "稻妻原来还有这种传说。",
            "白天看应该不会害怕吧……应该。",
        ),
        "daydream",
    ),
    "mechanism_book": ShopItem(
        "mechanism_book",
        "《机关设计入门》",
        "书籍",
        7,
        "机",
        "讲解机关、转轴和稳定结构的入门书。",
        {"knowledge": 0.16, "focus": 0.12, "energy": -0.03},
        (
            "这个结构如果放进烟花装置，会很稳。",
            "有点难，不过看懂了就很有趣。",
            "终于明白这里为什么要多加一个转轴。",
        ),
        "study",
    ),
    "folk_tales": ShopItem(
        "folk_tales",
        "《民间故事集》",
        "书籍",
        5,
        "话",
        "收录各地关于节日和朋友的短篇故事。",
        {"knowledge": 0.10, "mood": 0.10, "affection": 0.01},
        (
            "这个故事讲完，感觉像坐在篝火旁边一样。",
            "原来别的地方也有很像的节日。",
            "下次也把这个故事讲给孩子们听吧。",
        ),
        "welcome",
    ),
    "lucky_charm": ShopItem(
        "lucky_charm",
        "幸运御守",
        "小物",
        4,
        "守",
        "送给重要朋友的小小祝福。",
        {"mood": 0.13, "health": 0.05},
        (
            "收到这个，今天的运气一定会变好。",
            "我会把它放在最显眼的地方。",
            "这份心意比御守本身更珍贵。",
        ),
        "shy",
    ),
    "panda_doll": ShopItem(
        "panda_doll",
        "小熊猫玩偶",
        "小物",
        6,
        "熊",
        "软绵绵的玩偶，抱着会很安心。",
        {"mood": 0.20, "affection": 0.015},
        (
            "抱起来软软的，今天也是我的新朋友。",
            "它也有一双认真看着我的眼睛。",
            "累的时候抱着它，好像没那么难熬了。",
        ),
        "sleep",
    ),
}
