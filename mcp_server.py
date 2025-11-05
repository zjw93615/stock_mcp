import asyncio
import os
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from logger import get_logger

# 导入MCP工具
from mcp_tools import (
    MCPHistoricalDataTool,
    MCPStockInfoTool,
    MCPTechnicalAnalysisTool,
    MCPFinancialStatementsTool,
    MCPNewsTool,
    MCPWebSearchTool,
)

# 加载环境变量
load_dotenv()

# 获取日志记录器
logger = get_logger()

import os
proxy = os.getenv("HTTP_PROXY")
https_proxy = os.getenv("HTTPS_PROXY")
if proxy:
    os.environ['HTTP_PROXY'] = proxy
if https_proxy:
    os.environ['HTTPS_PROXY'] = https_proxy

# 创建FastMCP应用
mcp = FastMCP("stock-analysis")

# 初始化所有工具
tools = {
    "get_historical_data": MCPHistoricalDataTool(),
    "get_stock_info": MCPStockInfoTool(),
    "calculate_technical_indicators": MCPTechnicalAnalysisTool(),
    "get_financial_statements": MCPFinancialStatementsTool(),
    "get_news": MCPNewsTool(),
    "search_web_info": MCPWebSearchTool(),
}


@mcp.tool()
async def get_historical_data(
    ticker: str, start_date: str, end_date: str
) -> Dict[str, Any]:
    """
    获取股票历史价格数据，包括开盘价、收盘价、最高价、最低价和成交量

    Args:
        ticker: 股票代码，如AAPL
        start_date: 开始日期，格式YYYY-MM-DD
        end_date: 结束日期，格式YYYY-MM-DD
    """
    return await tools["get_historical_data"].execute(
        ticker=ticker, start_date=start_date, end_date=end_date
    )


@mcp.tool()
async def get_stock_info(ticker: str) -> Dict[str, Any]:
    """
    获取股票基本信息，包括公司概况、市值、PE比率等关键指标

    Args:
        ticker: 股票代码，如AAPL
    """
    return await tools["get_stock_info"].execute(ticker=ticker)


@mcp.tool()
async def calculate_technical_indicators(
    ticker: str, start_date: str, end_date: str
) -> Dict[str, Any]:
    """
    计算技术指标，包括移动平均线(MA)、相对强弱指数(RSI)、MACD等

    Args:
        ticker: 股票代码，如AAPL
        start_date: 开始日期，格式YYYY-MM-DD
        end_date: 结束日期，格式YYYY-MM-DD
    """
    return await tools["calculate_technical_indicators"].execute(
        ticker=ticker, start_date=start_date, end_date=end_date
    )


@mcp.tool()
async def get_financial_statements(ticker: str) -> Dict[str, Any]:
    """
    获取公司财务报表数据，包括损益表、资产负债表和现金流量表

    Args:
        ticker: 股票代码，如AAPL
    """
    return await tools["get_financial_statements"].execute(ticker=ticker)


@mcp.tool()
async def get_news(ticker: str, limit: int = 10) -> Dict[str, Any]:
    """
    获取股票相关新闻

    Args:
        ticker: 股票代码，如AAPL
        limit: 新闻数量限制，默认10条
    """
    return await tools["get_news"].execute(ticker=ticker, limit=limit)


# @mcp.tool()
# async def search_web_info(query: str, max_results: int = 5) -> Dict[str, Any]:
#     """
#     搜索网络信息

#     Args:
#         query: 搜索查询
#         max_results: 最大结果数，默认5
#     """
#     return await tools["search_web_info"].execute(query=query, max_results=max_results)


@mcp.prompt()
async def stock_analysis(ticker: str, analysis_type: str = "comprehensive") -> str:
    """
    分析股票的综合模板

    Args:
        ticker: 股票代码
        analysis_type: 分析类型：technical, fundamental, news, comprehensive
    """
    prompt_text = f"""
请对股票 {ticker} 进行{analysis_type}分析。

分析框架：
1. 获取基本信息和当前价格
2. 分析历史价格表现
3. 计算技术指标
4. 查看财务状况
5. 获取相关新闻
6. 综合评估和投资建议

请确保：
- 基于真实数据进行分析
- 明确标注数据来源和时间
- 提供风险提示
- 避免绝对预测
"""
    return prompt_text


@mcp.prompt()
async def market_comparison(tickers: str) -> str:
    """
    比较多只股票的模板

    Args:
        tickers: 股票代码列表，用逗号分隔
    """
    tickers_list = [t.strip() for t in tickers.split(",")]
    tickers_str = ", ".join(tickers_list)

    prompt_text = f"""
请比较以下股票的表现和投资价值：{tickers_str}

比较维度：
1. 基本信息对比（市值、PE、PB等）
2. 价格表现对比
3. 技术指标对比
4. 财务健康度对比
5. 行业地位和前景
6. 投资建议排序

请确保比较客观公正，基于数据说话。
"""
    return prompt_text


if __name__ == "__main__":
    logger.info("启动Stock Analysis FastMCP服务器")
    mcp.run(transport="stdio")
