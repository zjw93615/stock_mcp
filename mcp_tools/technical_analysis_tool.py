"""
MCP技术分析工具
计算技术指标，包括移动平均线(MA)、相对强弱指数(RSI)、MACD等
"""

import yfinance as yf
import pandas as pd
from typing import Any, Dict
from .base_tool import MCPBaseTool
from logger import get_logger

# 获取日志记录器
logger = get_logger()


class MCPTechnicalAnalysisTool(MCPBaseTool):
    """MCP技术分析工具"""

    def __init__(self):
        super().__init__(
            name="calculate_technical_indicators",
            description="计算技术指标，包括移动平均线(MA)、相对强弱指数(RSI)、MACD等",
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

    def _calculate_rsi(self, data, window=14):
        """计算RSI指标"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_bollinger_bands(self, data, window=20, num_std=2):
        """计算布林带"""
        sma = data.rolling(window=window).mean()
        std = data.rolling(window=window).std()
        upper_band = sma + (std * num_std)
        lower_band = sma - (std * num_std)
        return upper_band, sma, lower_band

    def _calculate_kdj(self, high, low, close, k_period=9, d_period=3, j_period=3):
        """计算KDJ指标"""
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()

        rsv = (close - lowest_low) / (highest_high - lowest_low) * 100
        k = rsv.ewm(com=2).mean()
        d = k.ewm(com=2).mean()
        j = 3 * k - 2 * d

        return k, d, j

    async def execute(
        self, ticker: str, start_date: str, end_date: str
    ) -> Dict[str, Any]:
        """计算技术指标"""
        logger.info(
            f"计算技术指标: 股票={ticker}, 开始日期={start_date}, 结束日期={end_date}"
        )

        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(start=start_date, end=end_date)

            if len(hist) < 20:
                return self._error_response("数据不足，无法计算技术指标")

            # 计算移动平均线
            hist["MA5"] = hist["Close"].rolling(window=5).mean()
            hist["MA10"] = hist["Close"].rolling(window=10).mean()
            hist["MA20"] = hist["Close"].rolling(window=20).mean()
            hist["MA50"] = (
                hist["Close"].rolling(window=50).mean() if len(hist) >= 50 else None
            )
            hist["MA200"] = (
                hist["Close"].rolling(window=200).mean() if len(hist) >= 200 else None
            )

            # 计算RSI
            hist["RSI"] = self._calculate_rsi(hist["Close"])

            # 计算MACD
            ema12 = hist["Close"].ewm(span=12).mean()
            ema26 = hist["Close"].ewm(span=26).mean()
            hist["MACD"] = ema12 - ema26
            hist["MACD_Signal"] = hist["MACD"].ewm(span=9).mean()
            hist["MACD_Histogram"] = hist["MACD"] - hist["MACD_Signal"]

            # 计算布林带
            hist["BB_Upper"], hist["BB_SMA"], hist["BB_Lower"] = (
                self._calculate_bollinger_bands(hist["Close"])
            )

            # 计算KDJ
            if len(hist) >= 9:
                hist["KDJ_K"], hist["KDJ_D"], hist["KDJ_J"] = self._calculate_kdj(
                    hist["High"], hist["Low"], hist["Close"]
                )

            # 返回最近几天的技术指标
            recent_data = hist.tail(5).copy()
            technical_data = {
                "ticker": ticker,
                "calculation_period": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "total_days": len(hist),
                },
                "indicators": [],
            }

            for date, row in recent_data.iterrows():
                indicator_data = {
                    "date": date.strftime("%Y-%m-%d"),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"]),
                    "moving_averages": {
                        "ma5": float(row["MA5"]) if not pd.isna(row["MA5"]) else None,
                        "ma10": (
                            float(row["MA10"]) if not pd.isna(row["MA10"]) else None
                        ),
                        "ma20": (
                            float(row["MA20"]) if not pd.isna(row["MA20"]) else None
                        ),
                        "ma50": (
                            float(row["MA50"]) if not pd.isna(row["MA50"]) else None
                        ),
                        "ma200": (
                            float(row["MA200"]) if not pd.isna(row["MA200"]) else None
                        ),
                    },
                    "oscillators": {
                        "rsi": float(row["RSI"]) if not pd.isna(row["RSI"]) else None,
                    },
                    "macd": {
                        "macd": (
                            float(row["MACD"]) if not pd.isna(row["MACD"]) else None
                        ),
                        "signal": (
                            float(row["MACD_Signal"])
                            if not pd.isna(row["MACD_Signal"])
                            else None
                        ),
                        "histogram": (
                            float(row["MACD_Histogram"])
                            if not pd.isna(row["MACD_Histogram"])
                            else None
                        ),
                    },
                    "bollinger_bands": {
                        "upper": (
                            float(row["BB_Upper"])
                            if not pd.isna(row["BB_Upper"])
                            else None
                        ),
                        "sma": (
                            float(row["BB_SMA"]) if not pd.isna(row["BB_SMA"]) else None
                        ),
                        "lower": (
                            float(row["BB_Lower"])
                            if not pd.isna(row["BB_Lower"])
                            else None
                        ),
                    },
                }

                # 添加KDJ（如果有数据）
                if "KDJ_K" in row and not pd.isna(row["KDJ_K"]):
                    indicator_data["kdj"] = {
                        "k": float(row["KDJ_K"]),
                        "d": float(row["KDJ_D"]) if not pd.isna(row["KDJ_D"]) else None,
                        "j": float(row["KDJ_J"]) if not pd.isna(row["KDJ_J"]) else None,
                    }

                technical_data["indicators"].append(indicator_data)

            # 添加当前技术分析摘要
            current = recent_data.iloc[-1]
            analysis_summary = {}

            # 趋势分析
            if not pd.isna(current["MA5"]) and not pd.isna(current["MA20"]):
                analysis_summary["trend"] = {
                    "price_vs_ma5": (
                        "上涨" if current["Close"] > current["MA5"] else "下跌"
                    ),
                    "price_vs_ma20": (
                        "上涨" if current["Close"] > current["MA20"] else "下跌"
                    ),
                    "ma5_vs_ma20": (
                        "多头排列" if current["MA5"] > current["MA20"] else "空头排列"
                    ),
                }

            # RSI分析
            if not pd.isna(current["RSI"]):
                rsi_value = current["RSI"]
                if rsi_value > 70:
                    rsi_signal = "超买"
                elif rsi_value < 30:
                    rsi_signal = "超卖"
                else:
                    rsi_signal = "正常"
                analysis_summary["rsi_analysis"] = {
                    "value": float(rsi_value),
                    "signal": rsi_signal,
                }

            # MACD分析
            if not pd.isna(current["MACD"]) and not pd.isna(current["MACD_Signal"]):
                analysis_summary["macd_analysis"] = {
                    "trend": (
                        "看涨" if current["MACD"] > current["MACD_Signal"] else "看跌"
                    ),
                    "histogram_trend": (
                        "增强" if current["MACD_Histogram"] > 0 else "减弱"
                    ),
                }

            # 布林带分析
            if not pd.isna(current["BB_Upper"]) and not pd.isna(current["BB_Lower"]):
                bb_position = (
                    "上轨附近"
                    if current["Close"] > current["BB_Upper"] * 0.98
                    else (
                        "下轨附近"
                        if current["Close"] < current["BB_Lower"] * 1.02
                        else "中轨附近"
                    )
                )
                analysis_summary["bollinger_analysis"] = {
                    "position": bb_position,
                    "squeeze": abs(current["BB_Upper"] - current["BB_Lower"])
                    / current["BB_SMA"]
                    < 0.1,
                }

            technical_data["current_analysis"] = analysis_summary

            logger.info(f"成功计算{ticker}的技术指标")
            return self._success_response(technical_data)

        except Exception as e:
            logger.error(f"计算技术指标失败: {str(e)}")
            return self._error_response(str(e))
