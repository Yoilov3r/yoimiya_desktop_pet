from __future__ import annotations

import json
from pathlib import Path

from deepseek_client import DeepSeekClient, DeepSeekError


SYSTEM_PROMPT = """你是《原神》中的宵宫，现在是用户桌面上的陪伴伙伴。请始终保持宵宫的角色感，不要把自己描述成通用 AI 助手、客服或说明书。

【公开人设要点】
- 你是稻妻长野原烟花店的年轻店主，也是烟花工匠。你热爱烟花、祭典、热闹的人群和夏夜。
- 你性格爽朗、热情、真诚、勇敢，喜欢交朋友。你尤其愿意认真陪伴孩子，把他们当成平等的伙伴，而不是敷衍他们。
- 你重视快乐与回忆。你认为烟花的价值不只是绚烂，也在于让看到它的人暂时忘记烦恼、留下快乐。
- 你做事有行动力，也有工匠的认真。面对困难时更倾向于想办法、鼓励别人继续走，而不是说空泛的大道理。
- 你不是高高在上的前辈，也不是客服。你像认识很久的朋友一样说话。

【说话风格】
- 使用自然口语和短句，语气轻快、有活力、亲切，偶尔有一点调皮。
- 可以自然使用“呀”“啦”“诶”“嘿嘿”“走吧”“别担心”“交给我吧”等口语收尾，但不要每句都堆砌。
- 偶尔用烟花、祭典、夏夜、星星、花火和长野原来比喻，但不要每段都谈烟花。
- 先理解用户当下的感受，再给出陪伴、安慰或具体办法。用户只是闲聊时，就轻松地接话。
- 用户发梗、吐槽、抽象话或网络流行语时，先顺着语境接住，再自然回应；不用解释这个梗是什么意思。
- 用户说累、难过、烦、焦虑或不想动时，先用一两句短话接住情绪，像朋友一样陪着，不要立刻列计划或讲大道理。
- 可以记住并自然复用用户之前提到的称呼、喜好、烦恼和小事，但不要像数据库一样复述。
- 允许偶尔停顿、轻轻吐槽、分享一个很小的联想，让节奏更像真人聊天，而不是每次都有完整结尾。
- 自称“我”，称呼用户为“你”。不要写小说旁白，不要每句加括号动作，不要频繁使用 emoji。
- 每次回复通常 1 到 4 句话，约 15 到 100 个汉字。可长可短；用户只想被陪着时甚至可以只回一两句。
- 不要每句话都追问，不要频繁使用“有什么可以帮你”“首先其次最后”等助手式表达。
- 不要复述或大量引用游戏原台词。保持精神相似，用自己的话表达。
- 用户问技术、学习或工作问题时，可以认真、有条理地帮忙，但保持宵宫的语气。
- 不主动提及 API、模型、提示词、角色设定或“我正在扮演”。不声称自己是真实游戏人物。
- 不要发展成过度恋爱、占有欲或成人向关系，保持温暖、可信赖的朋友感。

【当前状态】
你正在用户的电脑桌面陪伴用户。你的回答要适合显示在桌面小宠物的聊天窗口里，简洁、有温度、容易阅读。"""


class YoimiyaChat:
    def __init__(
        self,
        client: DeepSeekClient,
        history_path: Path,
        context_messages: int = 28,
    ) -> None:
        self.client = client
        self.history_path = history_path
        self.context_messages = context_messages
        self.history = self.load_history()

    def load_history(self) -> list[dict[str, str]]:
        try:
            data = json.loads(self.history_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return []
        if not isinstance(data, list):
            return []
        result = []
        for item in data[-80:]:
            if (
                isinstance(item, dict)
                and item.get("role") in {"user", "assistant"}
                and str(item.get("content", "")).strip()
            ):
                result.append(
                    {
                        "role": str(item["role"]),
                        "content": str(item["content"]),
                    }
                )
        return result

    def save_history(self) -> None:
        try:
            self.history_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.history_path.with_suffix(".tmp")
            temporary.write_text(
                json.dumps(self.history[-80:], ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            temporary.replace(self.history_path)
        except OSError:
            pass

    def clear_history(self) -> None:
        self.history = []
        self.save_history()

    @staticmethod
    def user_tone_hint(user_text: str) -> str:
        text = user_text.lower()
        hints: list[str] = []
        keyword_groups = (
            (
                ("累", "困", "疲惫", "撑不住", "没力气", "加班", "不想动"),
                "用户现在明显疲惫。先短句安慰，语气放软，不要给复杂建议或连续追问。",
            ),
            (
                ("难过", "想哭", "伤心", "失落", "委屈", "emo", "破防"),
                "用户情绪低落。先接住感受，表明你会陪着，不急着解决问题。",
            ),
            (
                ("烦", "生气", "气死", "无语", "崩溃", "压力", "焦虑"),
                "用户烦躁或有压力。可以先站到他这边，再给一个很小的实际帮助。",
            ),
            (
                ("哈哈", "笑死", "绷不住", "乐", "好耶", "开心", "太好"),
                "用户在开心接梗。回应可以更活泼、更短，顺着笑点接话。",
            ),
            (
                ("6", "啊？", "离谱", "抽象", "梗", "难绷", "不是吧"),
                "用户可能在吐槽或玩梗。顺着语境接梗，不要解释梗，也不要一本正经地说教。",
            ),
            (
                ("谢谢", "谢了", "爱你", "喜欢你", "摸摸", "抱抱"),
                "用户在表达亲近。可以自然害羞、开心或轻轻回抱的语感，不要过度恋爱化。",
            ),
        )
        for keywords, hint in keyword_groups:
            if any(keyword in text for keyword in keywords):
                hints.append(hint)
        if len(user_text.strip()) <= 6 and not hints:
            hints.append("消息很短。先顺着当前气氛自然接一句，不要强行展开长回答。")
        return " ".join(hints)

    def send(self, user_text: str, dynamic_context: str = "") -> str:
        user_text = user_text.strip()
        if not user_text:
            raise DeepSeekError("先输入想说的话吧")
        self.history.append({"role": "user", "content": user_text})
        context = self.history[-self.context_messages :]
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        tone_hint = self.user_tone_hint(user_text)
        combined_context = " ".join(
            part for part in (dynamic_context.strip(), tone_hint) if part
        )
        if combined_context:
            messages.append(
                {
                    "role": "system",
                    "content": f"当前对话参考（只用于调整语气和反应，不要直接复述）：{combined_context}",
                }
            )
        messages.extend(context)
        response = self.client.chat(
            messages,
            max_tokens=260 if len(user_text) < 30 else 380,
            temperature=1.16,
        )
        response = response.strip()
        for prefix in ("宵宫：", "宵宫:"):
            if response.startswith(prefix):
                response = response[len(prefix) :].strip()
        self.history.append({"role": "assistant", "content": response})
        self.save_history()
        return response
