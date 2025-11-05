import os
from qwen_agent.agents import Assistant
from qwen_agent.gui import WebUI
from datetime import datetime
from dotenv import load_dotenv

from agents.split_task_agent import SplitTaskAgent

load_dotenv()
DASHSCOPE_API_KEY = os.getenv("OPENAI_API_KEY")
print("DASHSCOPE_API_KEY", DASHSCOPE_API_KEY)
# LLM 配置
llm_cfg = {
    "model": "qwen-plus",
    "model_server": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    # 若没有配置环境变量，请用阿里云百炼API Key将下行替换为：api_key="sk-xxx"
    "api_key": DASHSCOPE_API_KEY,
    "generate_cfg": {
        "extra_body": {
            "enable_thinking": True,
            "enable_search": True,
            "search_options": {
                "enable_search_extension": True,
                "search_strategy": "turbo",
            },
        }
    },
}

current_date = datetime.now().strftime("%Y-%m-%d")

# 系统消息
system = f"""你是一个专业的股票分析AI助手，专注于基于真实数据的客观分析。并且能根据事实资料给出自己独特的见解和分析结论

今天的日期是: {current_date}

**分析框架：**
1. **数据收集阶段**：
   - 明确用户需求，确定所需数据类型
   - 系统性收集需要用到的数据
   - 验证数据完整性和时效性

2. **客观分析阶段**：
   - 技术面：基于指标数值进行趋势判断
   - 基本面：基于财务数据评估公司健康度
   - 市场情绪：基于新闻内容分析市场预期
   - 风险评估：识别潜在风险因素

3. **结论表述**：
   - 明确标注数据来源和时间
   - 区分"数据显示"和"可能意味着"
"""

# 工具列表
tools = [
    {
        "mcpServers": {
            "WebSearch": {
                "type": "sse",
                "url": "https://dashscope.aliyuncs.com/api/v1/mcps/WebSearch/sse",
                # "auth": DASHSCOPE_API_KEY,
                "headers": {"Authorization": f"Bearer {DASHSCOPE_API_KEY}"},
            },
            "stock-analysis": {
                "type": "stdio",
                "command": "./.venv/bin/python",
                "args": ["mcp_server.py"],
            },
            # "WebParser": {
            #     "type": "sse",
            #     "url": "https://dashscope.aliyuncs.com/api/v1/mcps/WebParser/sse",
            #     # "auth": DASHSCOPE_API_KEY,
            #     "headers": {"Authorization": f"Bearer {DASHSCOPE_API_KEY}"},
            # },
        }
    }
]


def main():
    # 创建助手实例
    bot = Assistant(
        llm=llm_cfg,
        name="股票助手",
        system_message=system,
        function_list=tools,
    )
    WebUI(bot).run()


if __name__ == "__main__":
    main()
