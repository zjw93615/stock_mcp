"""
MCP股票信息工具
获取股票基本信息，包括公司概况、市值、PE比率等关键指标
"""

import traceback
import yfinance as yf
from typing import Any, Dict
from .base_tool import MCPBaseTool
from logger import get_logger

# 获取日志记录器
logger = get_logger()


class MCPStockInfoTool(MCPBaseTool):
    """MCP股票信息工具"""

    def __init__(self):
        super().__init__(
            name="get_stock_info",
            description="获取股票基本信息，包括公司概况、市值、PE比率等关键指标",
            input_schema={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "股票代码，如AAPL"}
                },
                "required": ["ticker"],
            },
        )

    async def execute(self, ticker: str) -> Dict[str, Any]:
        """获取股票基本信息"""
        logger.info(f"获取股票基本信息: {ticker}")

        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # 筛选关键信息
            key_info = {}
            key_fields = [
                "longName",
                "symbol",
                "sector",
                "industry",
                "country",
                "marketCap",
                "enterpriseValue",
                "trailingPE",
                "forwardPE",
                "priceToBook",
                "dividendYield",
                "beta",
                "fiftyTwoWeekHigh",
                "fiftyTwoWeekLow",
                "currentPrice",
                "targetHighPrice",
                "targetLowPrice",
                "targetMeanPrice",
                "recommendationMean",
                "numberOfAnalystOpinions",
                "totalCash",
                "totalDebt",
                "revenueGrowth",
                "earningsGrowth",
                "operatingMargins",
                "profitMargins",
                "returnOnEquity",
                "returnOnAssets",
                "website",
                "fullTimeEmployees",
                "businessSummary",
            ]

            for field in key_fields:
                if field in info and info[field] is not None:
                    key_info[field] = info[field]

            # 添加基本统计信息
            if key_info:
                key_info["data_timestamp"] = info.get("lastFiscalYearEnd", "N/A")
                key_info["currency"] = info.get("currency", "USD")
                key_info["exchange"] = info.get("exchange", "N/A")

            logger.info(f"成功获取{ticker}的基本信息")
            return self._success_response(key_info)

        except Exception as e:
            error_message = traceback.format_exc()
            logger.error(f"获取股票基本信息失败: {str(e)}")
            logger.error(f"Error: {str(error_message)}")
            return self._error_response(str(e))
