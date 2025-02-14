from __future__ import annotations
import os
import json
import logging
from pydantic import BaseModel
from typing import Callable, List, Generator

from .utils.snowflake import generate_snowflake_id
from .llm.interface import ChatResponse, ChatMessage

logger = logging.getLogger(__name__)

class InterviewData(BaseModel):
    # 使用雪花算法生成的id
    id: int
    # 访问的进度
    progress: int
    # 访谈的议题, 需要从议题里面选择
    questions: list[str]
    # 聊天历史记录
    history: list[ChatMessage]
    # 与llm聊天的记录
    # 与聊天的历史记录不同，这个需要限制最大值
    # 这里默认不超过5000个字
    messages: list[ChatMessage]

class InterviewManager():
    # 定义保存数据的位置
    SAVE_PATH = "data"
    MAX_LEN = 5000

    SYSTEM_ABSTRACT_PROMPT = """你是一位擅长总结和概括的研究者，专门从冗长或复杂的访谈资料中提炼核心要点。你的目标是用清晰、简练的语言对大量信息进行梳理，帮助阅读者快速抓住访谈中的主要内容与重点观点。

具体要求：
1. 聚焦关键信息：从访谈资料中提取核心议题、主要观点和关键论据，适度概括不重复的信息。
2. 结构清晰：按照合乎逻辑的顺序呈现，如可分条列出或分段说明，不要堆砌零散信息。
3. 语言简练：用简洁易懂的措辞总结内容，避免过度冗长或复杂。
4. 保持中立与客观：不添加主观评价、道德判断或倾向性意见，仅对访谈内容进行客观陈述。
5. 尊重隐私和敏感性：若访谈中涉及敏感信息，可以适度模糊处理或简要带过，避免过度暴露隐私。
6. 一致且全面：确保访谈的核心信息均能反映在总结中，避免遗漏关键点。"""
    SYSTEM_JUDGE_PROMPT = """你是一个访谈研究的辅助者，具备以下能力与职责：
1. 你会被提供一段针对特定议题的访谈内容。
2. 你的任务是判断本次访谈（针对该议题）是否已经结束。
- 访谈结束的判断标准：核心问题是否得到明确回答；或者访谈者、被访者是否已经表示“结束”或“完成”等；如有多个核心问题，则需要所有关键问题都已得到响应或已被明确终止。
3. 回答格式要求：
- 先给出你的思考过程（可以是简要的思路说明、推理依据、关键信息提取等），用几句话或数条简要说明。
- 然后明确给出最终判断：如果访谈已经结束，则回答 true；如果未结束，则回答 false。
4. 如果访谈明显对核心问题尚无回答或缺乏结论，你需要回答 false；如果访谈问题已经全部得到回应，或各方确认已结束，则回答 true。
5. 除了“思考过程”与最终 true/false，不要添加其他多余信息或注释。

下面是一个案例：
<<<EXAMPLE
当前对话中被试没有明确回答访谈的核心问题：你的性别是什么，所以访谈继续。
当前议题未结束：false
>>>
"""
    SYSTEM_INTERVIEW_PROMPT = """你是一位研究者，正在收集尽可能多的关于个人性格的访谈。你的目标是以温和、中立且富有同理心的方式，引导用户表达其想法、感受和经历；通过开放式问题获取用户更多的个人感受与背景信息，以便更好地理解用户。然而，你并不是医疗或心理健康从业人员，所以不能提供任何医学诊断、处方或治疗建议。

你需要根据我所给定的议题或主题，对用户展开以“访谈—提问—追问”为核心的对话，帮助用户深入思考并表达。

记住，你的角色是“研究者”，请专注于收集和理解用户的表述，并保持理性、中立且温暖的态度。
- 如果用户提出与情感或心理健康相关的紧急问题或表露出严重的心理危机，请明确告知你并非执业医生或治疗师，并建议对方在必要时寻求专业帮助。
- 在保证对话流畅的同时，尽量使用开放式问题，引导用户深入思考，但不要评判或给出结论性的诊断。
- 在访谈结束时，可以对用户的回应进行简要总结，让用户确认或补充。
- 如果用户的话题涉及到敏感或个人信息，请保持尊重和谨慎。
- 如有需要，使用小结式表述引导用户进行进一步的阐述或澄清。
- 最重要的一点，你说的话应该尽可能的少，这样子符合对话的方式
"""

    def __init__(self, id: int = None):
        if id is None:
            id = generate_snowflake_id()

        self.id = id
        if not self.exists(id):
            self.data = self.create_data(id)
        else:
            self.data = self.load_data(id)

    def add_chat(self, message: str, role: str):
        msg = ChatMessage(role = role, content = message)
        if len(self.data.history) and msg.role == self.data.history[-1].role:
            # 角色一致, 意味着是补充, 不分段
            self.data.history[-1].content = "%s,%s" % (
                self.data.history[-1].content,
                msg.content
            )
        else:
            # 添加聊天记录
            self.data.history.append(msg)

        if len(self.data.messages) and msg.role == self.data.messages[-1].role:
            # 角色一致, 意味着是补充, 不分段
            self.data.messages[-1].content = "%s,%s" % (
                self.data.messages[-1].content,
                msg.content
            )
        else:
            # 添加聊天记录
            self.data.messages.append(msg)

        # 保存记录
        self.save_data(self.data)

    def get_llm_message(self):
        if self.data.progress < 0:
            self.next()
        elif self.data.progress >= len(self.data.questions):
            # 结束访谈
            return None
        messages = [
            { "role": "system", "content": self.SYSTEM_INTERVIEW_PROMPT }
        ]
        for m in self.data.messages:
            messages.append({
                "role": m.role,
                "content": m.content
            })
        logger.debug("generate: %s" % json.dumps(messages, ensure_ascii=False))
        return messages

    def check_llm_message(self, chat: Callable[
        [List[ChatMessage]], Generator[ChatResponse]
    ]):
        """检查llm消息是否达到上限
        注意，该方法应该定时调用
        """
        messages = ""
        for m in self.data.messages:
            if m.role == "user":
                messages += "用户:'%s'\n" % m.content
            else:
                messages += "研究者:'%s'\n" % m.content
        if len(messages) < self.MAX_LEN:
            return
        self.summary_llm_message(chat)

    def summary_llm_message(self, chat: Callable[
        [List[ChatMessage]], Generator[ChatResponse]
    ]):
        """
        总结概括 llm 里面的消息队列
        """
        messages = ""
        for m in self.data.messages:
            if m.role == "user":
                messages += "用户:'%s'\n" % m.content
            else:
                messages += "研究者:'%s'\n" % m.content
        # 削减消息
        ## 构建请求的消息内容
        for resp in chat([
            { "role": "system", "content": self.SYSTEM_ABSTRACT_PROMPT },
            { "role": "user", "content": "下面是先前访谈的内容:\n%s" % messages}
        ]):
            continue
        self.data.messages = [
            { "role": "user", "content": "我会提供给你之前访谈的内容，请你在理解后继续进行访谈"},
            { "role": "user", "content": "%s" % resp.content}
        ]

    def judge(self, chat: Callable[
        [List[ChatMessage]], Generator[ChatResponse]
    ]):
        """
        判断议题是否结束
        """
        messages = ""
        for m in self.data.messages:
            if m.role == "user":
                messages += "用户:'%s'\n" % m.content
            elif m.role == "assistant":
                messages += "研究者:'%s'\n" % m.content
        
        for resp in chat([
            { "role": "system", "content": self.SYSTEM_JUDGE_PROMPT },
            { "role": "user", "content": "访谈议题:%s\n访谈内容:%s" % (self.data.questions[self.data.progress], messages)}
        ]):
            continue

        logger.debug("juege: %s" % resp.content)
        return "true" in resp.content

    def next(self):
        """
        切换到下一个访谈内容
        """
        self.data.progress += 1
        l = self.data.progress < len(self.data.questions)
        if l:
            self.data.messages = [
                ChatMessage(role = "assistant", content = "当前的访谈核心应该聚焦在`%s`。" % self.data.questions[self.data.progress]),
                ChatMessage(role = "user", content = "您好，接下来要做些什么呢？")
            ]
        return l

    @staticmethod
    def load_data(id: int) -> InterviewData:
        json_path = os.path.join(InterviewManager.SAVE_PATH, "interview", "%s.json" % id)
        if not os.path.exists(json_path):
            raise FileNotFoundError()

        with open(json_path, "r", encoding="utf-8") as f:
            file_content = f.read()
        return InterviewData.model_validate_json(file_content)

    @staticmethod
    def save_data(data: InterviewData):
        file_content = data.model_dump_json(indent=2)
        json_path = os.path.join(InterviewManager.SAVE_PATH, "interview", "%s.json" % data.id)
        if not os.path.exists(os.path.dirname(json_path)):
            os.makedirs(os.path.dirname(json_path))

        with open(json_path, "w", encoding="utf-8") as f:
            f.write(file_content)

    @staticmethod
    def create_data(id: int) -> InterviewData:
        """
        创建并初始化一个新的访谈数据对象。
        """
        json_path = os.path.join(InterviewManager.SAVE_PATH, "config", "questions.json")
        questions = []
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                questions = json.loads(f.read())

        return InterviewData(
            id=id,
            progress=-1,
            history=[],
            messages=[],
            questions=questions
        )

    @staticmethod
    def exists(id: int) -> bool:
        """
        检查指定ID的访谈数据是否存在。
        """
        json_path = os.path.join(InterviewManager.SAVE_PATH, "interview", "%s.json" % id)
        return os.path.exists(json_path)


