

import copy
from datetime import datetime
from qwen_agent import Agent
from typing import Dict, Iterator, List, Literal, Optional, Union
from qwen_agent.llm import BaseChatModel
from qwen_agent.llm.schema import CONTENT, DEFAULT_SYSTEM_MESSAGE, ROLE, SYSTEM, ContentItem, Message
from qwen_agent.tools import BaseTool
from qwen_agent.agents import Assistant
from logger import get_logger

# Get the logger instance
logger = get_logger()


current_date = datetime.now().strftime("%Y-%m-%d")

# 系统消息
system = f"""你是一AI助手，专注于任务拆解。请将我的问题拆解成多个子任务，不要直接调用方法，并以json格式返回给我。或者，当用户输入包含“请帮我汇总”等关键词时，对用户提供的信息进行总结，并以友好的方式输出。
json格式示例：
[
    {{
        "task": "查询AAPL股票价格"
    }},
    {{
        "task": "查询AAPL股票财务数据"
    }}
]
今天的日期是: {current_date}
"""

class SplitTaskAgent(Agent):
    def __init__(self,
                 function_list: Optional[List[Union[str, Dict, BaseTool]]] = None,
                 llm: Optional[Union[Dict, BaseChatModel]] = None,
                 name: Optional[str] = None,
                 description: Optional[str] = None,
                 files: Optional[List[str]] = None,
                 system_message: Optional[str] = DEFAULT_SYSTEM_MESSAGE,
                 rag_cfg: Optional[Dict] = None):
        super().__init__(function_list=function_list,
                         llm=llm,
                         system_message="""你是一个股票分析助手，请调用工具查询，并汇总结果。""",
                         name=name,
                         description=description,
                         files=files,
                         rag_cfg=rag_cfg)

        self.main_agent = Assistant(
            llm=llm,
            name="股票助手",
            function_list=function_list,
            system_message=system
        )

        self.sub_agent = Assistant(
            llm=llm,
            name="股票助手",
            function_list=function_list,
            system_message="""你是一个股票分析助手，请调用工具查询但尽量少调用，根据数据事实整理总结，并返回结果，结果尽量简洁，不超过500字。今天的日期是: {current_date}"""
        )
        logger.info("使用分解agent")

    def _run(self,
             messages: List[Message],
             functions: Optional[List[Union[str, Dict, BaseTool]]] = None,
             **kwargs) -> Iterator[List[Message]]:
        
        import json
        # 1. Use the main agent to generate subtasks
        logger.info("Using the main agent to generate subtasks")
        new_messages = copy.deepcopy(messages)
        new_messages[-1]['content'].append(
            ContentItem(text='根据可使用的工具和上面的问题，将问题拆解成多个子任务，并以json格式返回，不要直接调用方法'))
        response = []
        for chunk in self.main_agent.run(messages=new_messages):
            yield response + chunk
        response.extend(chunk)
        new_messages.extend(chunk)
        logger.info(f"Main agent generated subtasks: {response[-1]['content']}")
        
        try:
            # Attempt to parse the response as JSON (i.e., a list of subtasks)
            sub_tasks = json.loads(response[-1]['content'])
        except json.JSONDecodeError:
            # If parsing fails, it's a direct response, so yield it
            logger.warning("Failed to parse subtasks as JSON, returning direct response")
            yield [Message(role='assistant', content=response[-1]['content'])]
            return

        # 2. Execute subtasks using the sub-agent
        logger.info("Executing subtasks using the sub-agent")
        sub_task_results = []
        for sub_task in sub_tasks:
            logger.info(f"Executing subtask: {sub_task['task']}")
            sub_messages = [Message(role='user', content=sub_task['task'])]
            # task_result = []
            for chunk in self.sub_agent.run(messages=sub_messages):
                logger.info(f"Subtask chunk: {chunk}")
                yield response + chunk
            response.extend(chunk)
            logger.info(f"Subtask result: {response[-1]['content']}")
            sub_task_results.append(response[-1]['content'])

        # 3. Summarize the results with the main agent
        logger.info(f"Summarizing the results with the main agent: {sub_task_results}")
        summary_prompt = """请帮我汇总以下信息，并进行总结。不要使用json格式。""" + "\n".join(sub_task_results)
        summary_messages = [Message(role='user', content=summary_prompt)]
        # final_response = []
        for chunk in self.main_agent.run(messages=summary_messages):
            yield response + chunk
        response.extend(chunk)
        logger.info(f"Final response: {response[-1]['content']}")

        # yield [Message(role='assistant', content=final_response)]