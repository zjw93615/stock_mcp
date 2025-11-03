"""
MCP历史数据工具
获取股票历史价格数据，包括开盘价、收盘价、最高价、最低价和成交量
"""

import yfinance as yf
from typing import Any, Dict
from .base_tool import MCPBaseTool
from logger import get_logger

# 获取日志记录器
logger = get_logger()

# 详细数据期间
DETAIL_PERIOD = 5


class MCPHistoricalDataTool(MCPBaseTool):
    """MCP历史数据工具"""

    def __init__(self):
        super().__init__(
            name="get_historical_data",
            description="获取股票历史价格数据，包括开盘价、收盘价、最高价、最低价和成交量",
            input_schema={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "股票代码，如AAPL"},
                    "start_date": {
                        "type": "string",
                        "description": "开始日期，格式YYYY-MM-DD",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "结束日期，格式YYYY-MM-DD",
                    },
                },
                "required": ["ticker", "start_date", "end_date"],
            },
        )

    async def execute(
        self, ticker: str, start_date: str, end_date: str
    ) -> Dict[str, Any]:
        """获取股票历史价格数据"""
        logger.info(
            f"获取历史数据: 股票={ticker}, 开始日期={start_date}, 结束日期={end_date}"
        )

        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(start=start_date, end=end_date)

            if len(hist) == 0:
                return self._error_response("未获取到数据")

            # 计算关键统计信息
            summary = {
                "ticker": ticker,
                "period_summary": {
                    "start_date": start_date or hist.index[0].strftime("%Y-%m-%d"),
                    "end_date": end_date or hist.index[-1].strftime("%Y-%m-%d"),
                    "total_days": len(hist),
                    "current_price": float(hist["Close"].iloc[-1]),
                    "period_high": float(hist["High"].max()),
                    "period_low": float(hist["Low"].min()),
                    "period_return": float(
                        (hist["Close"].iloc[-1] / hist["Close"].iloc[0] - 1) * 100
                    ),
                    "avg_volume": float(hist["Volume"].mean()),
                    "volatility": float(hist["Close"].pct_change().std() * 100),
                },
                "recent_data": [],
            }

            # 最近几天的详细数据
            recent_hist = (
                hist.tail(DETAIL_PERIOD) if len(hist) > DETAIL_PERIOD else hist
            )
            for date, row in recent_hist.iterrows():
                summary["recent_data"].append(
                    {
                        "date": date.strftime("%Y-%m-%d"),
                        "open": float(row["Open"]),
                        "high": float(row["High"]),
                        "low": float(row["Low"]),
                        "close": float(row["Close"]),
                        "volume": int(row["Volume"]),
                    }
                )

            logger.info(f"成功获取{ticker}的历史数据，记录数: {len(hist)}")
            return self._success_response(summary)

        except Exception as e:
            logger.error(f"获取历史数据失败: {str(e)}")
            return self._error_response(str(e))
