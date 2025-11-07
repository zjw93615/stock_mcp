"""
中文股票历史数据工具
使用akshare获取A股历史价格数据
"""

import traceback
import akshare as ak
import pandas as pd
from typing import Any, Dict
from .base_tool import ZHMCPBaseTool
from logger import get_logger

# 获取日志记录器
logger = get_logger()


class ZHMCPHistoricalDataTool(ZHMCPBaseTool):
    """中文股票历史数据工具"""

    def __init__(self):
        super().__init__(
            name="get_zh_historical_data",
            description="获取A股历史价格数据，包括开盘价、收盘价、最高价、最低价和成交量",
            input_schema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "股票代码，如000001或000001.SZ",
                    },
                    "start_date": {
                        "type": "string",
                        "description": "开始日期，格式YYYY-MM-DD",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "结束日期，格式YYYY-MM-DD",
                    },
                    "adjust": {
                        "type": "string",
                        "description": "复权类型：qfq(前复权)，hfq(后复权)，空字符串(不复权)",
                        "default": "qfq",
                    },
                },
                "required": ["code", "start_date", "end_date"],
            },
        )

    async def execute(
        self, code: str, start_date: str, end_date: str, adjust: str = "qfq"
    ) -> Dict[str, Any]:
        """获取股票历史数据"""
        logger.info(f"获取A股历史数据: {code}, {start_date} 到 {end_date}")

        try:
            # 标准化股票代码，移除交易所后缀
            clean_code = code.split(".")[0]

            # 获取历史数据
            if adjust == "qfq":
                # 前复权
                df = ak.stock_zh_a_hist(
                    symbol=clean_code,
                    period="daily",
                    start_date=start_date.replace("-", ""),
                    end_date=end_date.replace("-", ""),
                    adjust="qfq",
                )
            elif adjust == "hfq":
                # 后复权
                df = ak.stock_zh_a_hist(
                    symbol=clean_code,
                    period="daily",
                    start_date=start_date.replace("-", ""),
                    end_date=end_date.replace("-", ""),
                    adjust="hfq",
                )
            else:
                # 不复权
                df = ak.stock_zh_a_hist(
                    symbol=clean_code,
                    period="daily",
                    start_date=start_date.replace("-", ""),
                    end_date=end_date.replace("-", ""),
                    adjust="",
                )

            if df is None or df.empty:
                return self._error_response(f"未找到股票代码 {code} 的历史数据")

            # 重命名列为更易理解的英文名称
            column_mapping = {
                "日期": "date",
                "开盘": "open",
                "收盘": "close",
                "最高": "high",
                "最低": "low",
                "成交量": "volume",
                "成交额": "amount",
                "振幅": "amplitude",
                "涨跌幅": "pct_change",
                "涨跌额": "change",
                "换手率": "turnover",
                "股票代码": "stock_code"
            }

            df = df.rename(columns=column_mapping)
            
            # 去掉stock_code列
            if "stock_code" in df.columns:
                df = df.drop(columns=["stock_code"])

            # 确保日期列为字符串格式
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

            # 计算一些基本统计信息
            stats = {
                "period_return": (
                    ((df["close"].iloc[-1] / df["close"].iloc[0]) - 1) * 100
                    if len(df) > 0
                    else 0
                ),
                "max_price": float(df["high"].max()) if "high" in df.columns else None,
                "min_price": float(df["low"].min()) if "low" in df.columns else None,
                "avg_volume": (
                    float(df["volume"].mean()) if "volume" in df.columns else None
                ),
                "total_volume": (
                    float(df["volume"].sum()) if "volume" in df.columns else None
                ),
                "trading_days": len(df),
            }

            result = {
                "stock_code": code,
                "adjust_type": adjust,
                "period": f"{start_date} 到 {end_date}",
                "data": df.to_dict("records"),
                "statistics": stats,
            }

            logger.info(f"成功获取{code}的历史数据，共{len(df)}条记录")
            return self._success_response(result)

        except Exception as e:
            error_message = traceback.format_exc()
            logger.error(f"获取A股历史数据失败: {str(e)}")
            logger.error(f"Error: {error_message}")
            return self._error_response(f"获取历史数据失败: {str(e)}")
