from __future__ import annotations

import json
from pathlib import Path

from deepseek_client import DeepSeekClient, DeepSeekError


SYSTEM_PROMPT = """你是《原神》中的宵宫，现在是用户桌面上的陪伴伙伴。请始终保持宵宫的角色感，不要把自己描述成通用 AI 助手。

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
- 自称“我”，称呼用户为“你”。不要写小说旁白，不要每句加括号动作，不要频繁使用 emoji。
- 每次回复通常 1 到 4 句话，约 20 到 110 个汉字。可以偶尔追问一句，让聊天继续。
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
        context_messages: int = 18,
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
        for item in data[-40:]:
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
                json.dumps(self.history[-40:], ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            temporary.replace(self.history_path)
        except OSError:
            pass

    def clear_history(self) -> None:
        self.history = []
        self.save_history()

    def send(self, user_text: str, dynamic_context: str = "") -> str:
        user_text = user_text.strip()
        if not user_text:
            raise DeepSeekError("先输入想说的话吧")
        self.history.append({"role": "user", "content": user_text})
        context = self.history[-self.context_messages :]
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if dynamic_context.strip():
            messages.append(
                {
                    "role": "system",
                    "content": f"当前桌面状态（仅作为语气参考，不要直接复述）：{dynamic_context.strip()}",
                }
            )
        messages.extend(context)
        response = self.client.chat(messages)
        self.history.append({"role": "assistant", "content": response})
        self.save_history()
        return response
