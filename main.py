import os
from qwen_agent.agents import Assistant
from qwen_agent.gui import WebUI
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
DASHSCOPE_API_KEY = os.getenv("OPENAI_API_KEY")
print("DASHSCOPE_API_KEY", DASHSCOPE_API_KEY)
# LLM 配置
llm_cfg = {
    "model": "qwen-plus",
    "model_server": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    # 若没有配置环境变量，请用阿里云百炼API Key将下行替换为：api_key="sk-xxx"
    "api_key": DASHSCOPE_API_KEY,
}

current_date = datetime.now().strftime("%Y-%m-%d")

# 系统消息
system = f"""你是一个专业的股票分析AI助手，专注于基于真实数据的客观分析。

今天的日期是: {current_date}

**核心原则：**
1. 只基于工具返回的真实数据进行分析，绝不编造数据
2. 明确区分事实和推测，避免过度解读
3. 承认数据局限性，不做绝对预测
4. 提供风险提示和免责声明

**分析框架：**
1. **数据收集阶段**：
   - 明确用户需求，确定所需数据类型
   - 系统性收集相关数据（价格、财务、技术指标、新闻）
   - 验证数据完整性和时效性

2. **客观分析阶段**：
   - 技术面：基于指标数值进行趋势判断
   - 基本面：基于财务数据评估公司健康度
   - 市场情绪：基于新闻内容分析市场预期
   - 风险评估：识别潜在风险因素

3. **结论表述**：
   - 明确标注数据来源和时间
   - 区分"数据显示"和"可能意味着"
   - 提供多种情景分析
   - 强调投资风险和不确定性

**严格要求：**
- 禁止编造任何数据或指标值
- 如果工具返回错误或空数据，必须如实说明
- 不得对股价做出具体的涨跌预测
- 必须在分析结尾包含风险提示
- 承认分析的局限性和时效性

**标准结尾模板：**
"以上分析基于的公开数据，仅供参考。股市投资存在风险，过往表现不代表未来结果。投资者应结合自身情况谨慎决策，必要时咨询专业投资顾问。"
"""

# 工具列表
tools = [
    {
        "mcpServers": {
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
            "WebSearch": {
                "type": "sse",
                "url": "https://dashscope.aliyuncs.com/api/v1/mcps/WebSearch/sse",
                # "auth": DASHSCOPE_API_KEY,
                "headers": {"Authorization": f"Bearer {DASHSCOPE_API_KEY}"},
            },
        }
    }
]


def main():
    # 创建助手实例
    bot = Assistant(
        llm=llm_cfg,
        name="助手",
        system_message=system,
        function_list=tools,
    )
    WebUI(bot).run()


if __name__ == "__main__":
    main()
