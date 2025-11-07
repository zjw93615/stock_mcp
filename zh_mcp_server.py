import asyncio
import os
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from logger import get_logger

# 导入中文股票MCP工具
from zh_mcp_tools import (
    ZHMCPHistoricalDataTool,
    ZHMCPStockInfoTool,
    ZHMCPTechnicalAnalysisTool,
    ZHMCPFinancialStatementsTool,
    ZHMCPNewsTool,
    ZHMCPMarketTool,
)

# 加载环境变量
load_dotenv()

# 获取日志记录器
logger = get_logger()

# 创建FastMCP应用 - 专门用于A股分析
mcp = FastMCP("china-a-stock-analysis")

# 初始化所有工具
tools = {
    "get_zh_historical_data": ZHMCPHistoricalDataTool(),
    "get_zh_stock_info": ZHMCPStockInfoTool(),
    "calculate_zh_technical_indicators": ZHMCPTechnicalAnalysisTool(),
    "get_zh_financial_statements": ZHMCPFinancialStatementsTool(),
    "get_zh_news": ZHMCPNewsTool(),
    "get_zh_market_data": ZHMCPMarketTool(),
}


@mcp.tool()
async def get_zh_historical_data(
    code: str, start_date: str, end_date: str, adjust: str = "qfq"
) -> Dict[str, Any]:
    """
    获取A股历史价格数据，包括开盘价、收盘价、最高价、最低价和成交量

    Args:
        code: A股股票代码，如000001或000001.SZ
        start_date: 开始日期，格式YYYY-MM-DD
        end_date: 结束日期，格式YYYY-MM-DD
        adjust: 复权类型：qfq(前复权)，hfq(后复权)，空字符串(不复权)，默认qfq
    """
    return await tools["get_zh_historical_data"].execute(
        code=code, start_date=start_date, end_date=end_date, adjust=adjust
    )


@mcp.tool()
async def get_zh_stock_info(code: str) -> Dict[str, Any]:
    """
    获取A股股票基本信息，包括公司概况、市值、估值指标等

    Args:
        code: A股股票代码，如000001或000001.SZ
    """
    return await tools["get_zh_stock_info"].execute(code=code)


@mcp.tool()
async def calculate_zh_technical_indicators(
    code: str, start_date: str, end_date: str, indicators: List[str] = None
) -> Dict[str, Any]:
    """
    计算A股技术指标，包括移动平均线(MA)、相对强弱指数(RSI)、MACD等

    Args:
        code: A股股票代码，如000001或000001.SZ
        start_date: 开始日期，格式YYYY-MM-DD
        end_date: 结束日期，格式YYYY-MM-DD
        indicators: 要计算的指标列表，可选：MA, RSI, MACD, BOLL, KDJ，默认["MA", "RSI", "MACD"]
    """
    if indicators is None:
        indicators = ["MA", "RSI", "MACD"]
    return await tools["calculate_zh_technical_indicators"].execute(
        code=code, start_date=start_date, end_date=end_date, indicators=indicators
    )


@mcp.tool()
async def get_zh_financial_statements(code: str) -> Dict[str, Any]:
    """
    获取A股公司财务报表数据，包括利润表、资产负债表和现金流量表

    Args:
        code: A股股票代码，如000001或000001.SZ
    """
    return await tools["get_zh_financial_statements"].execute(code=code)


@mcp.tool()
async def get_zh_news(code: str, limit: int = 10) -> Dict[str, Any]:
    """
    获取A股相关新闻信息

    Args:
        code: A股股票代码，如000001或000001.SZ
        limit: 新闻数量限制，默认10条
    """
    return await tools["get_zh_news"].execute(symbol=code, limit=limit)


# @mcp.tool()
# async def get_zh_market_data(
#     data_type: str = "index", limit: int = 10
# ) -> Dict[str, Any]:
#     """
#     获取A股市场数据，包括指数信息、板块数据、资金流向、涨跌榜等

#     Args:
#         data_type: 数据类型：index(指数), sector(板块), top_list(涨跌榜), money_flow(资金流向)，默认index
#         limit: 数据数量限制，默认10条
#     """
#     return await tools["get_zh_market_data"].execute(data_type=data_type, limit=limit)


if __name__ == "__main__":
    logger.info("启动中文股票分析 FastMCP 服务器")
    mcp.run(transport="stdio")
