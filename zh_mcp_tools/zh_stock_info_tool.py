"""
中文股票信息工具
使用akshare获取A股股票基本信息
"""

import traceback
import akshare as ak
import pandas as pd
from typing import Any, Dict
from .base_tool import ZHMCPBaseTool
from logger import get_logger

# 获取日志记录器
logger = get_logger()


class ZHMCPStockInfoTool(ZHMCPBaseTool):
    """中文股票信息工具"""

    def __init__(self):
        super().__init__(
            name="get_zh_stock_info",
            description="获取A股股票基本信息，包括公司概况、市值、估值指标等",
            input_schema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "股票代码，如000001或000001.SZ",
                    }
                },
                "required": ["code"],
            },
        )

    def _convert_to_xq_symbol(self, code: str) -> str:
        """
        将标准股票代码转换为雪球格式
        上海股票：6开头 -> SH前缀
        深圳股票：0开头、3开头 -> SZ前缀
        """
        if code.startswith("6"):
            return f"SH{code}"
        elif code.startswith(("0", "3")):
            return f"SZ{code}"
        else:
            # 默认返回原代码，让API自己处理
            return code

    async def execute(self, code: str) -> Dict[str, Any]:
        """获取股票基本信息"""
        logger.info(f"获取A股基本信息: {code}")

        try:
            # 标准化股票代码，移除交易所后缀
            clean_code = code.split(".")[0]

            result = {}

            # 1. 获取实时行情数据 - 使用雪球接口
            try:
                # 转换为雪球格式的股票代码
                xq_symbol = self._convert_to_xq_symbol(clean_code)
                stock_realtime = ak.stock_individual_spot_xq(symbol=xq_symbol)
                if not stock_realtime.empty:
                    # 雪球数据格式: DataFrame with 'item' and 'value' columns
                    # 转换为字典格式以便查找
                    data_dict = dict(
                        zip(stock_realtime["item"], stock_realtime["value"])
                    )

                    def safe_float(value, default=0):
                        """安全转换为浮点数"""
                        try:
                            if pd.isna(value) or value == "" or value is None:
                                return default
                            return float(value)
                        except (ValueError, TypeError):
                            return default

                    result["realtime_data"] = {
                        "symbol": data_dict.get("代码", ""),
                        "name": data_dict.get("名称", ""),
                        "current_price": safe_float(data_dict.get("现价", 0)),
                        "change_percent": safe_float(data_dict.get("涨幅", 0)),
                        "change_amount": safe_float(data_dict.get("涨跌", 0)),
                        "volume": safe_float(data_dict.get("成交量", 0)),
                        "amount": safe_float(data_dict.get("成交额", 0)),
                        "turnover_rate": safe_float(data_dict.get("周转率", 0)),
                        "pe_ratio_ttm": safe_float(data_dict.get("市盈率(TTM)", 0)),
                        "pe_ratio_dynamic": safe_float(data_dict.get("市盈率(动)", 0)),
                        "pe_ratio_static": safe_float(data_dict.get("市盈率(静)", 0)),
                        "pb_ratio": safe_float(data_dict.get("市净率", 0)),
                        "market_cap": safe_float(data_dict.get("资产净值/总市值", 0)),
                        "circulation_market_cap": safe_float(
                            data_dict.get("流通值", 0)
                        ),
                        "week_52_high": safe_float(data_dict.get("52周最高", 0)),
                        "week_52_low": safe_float(data_dict.get("52周最低", 0)),
                        "year_to_date_change": safe_float(
                            data_dict.get("今年以来涨幅", 0)
                        ),
                        "eps": safe_float(data_dict.get("每股收益", 0)),
                        "bps": safe_float(data_dict.get("每股净资产", 0)),
                        "dividend_ttm": safe_float(data_dict.get("股息(TTM)", 0)),
                        "dividend_yield_ttm": safe_float(
                            data_dict.get("股息率(TTM)", 0)
                        ),
                        "total_shares": safe_float(data_dict.get("基金份额/总股本", 0)),
                        "float_shares": safe_float(data_dict.get("流通股", 0)),
                    }
            except Exception as e:
                logger.warning(f"获取实时行情失败: {str(e)}")
                result["realtime_data"] = {"error": f"获取实时行情失败: {str(e)}"}

            # 2. 获取股票基本信息
            try:
                stock_info_df = ak.stock_individual_info_em(symbol=clean_code)
                print("stock_info_df", stock_info_df)
                if not stock_info_df.empty:
                    info_dict = dict(zip(stock_info_df["item"], stock_info_df["value"]))
                    result["company_info"] = {
                        "total_share_capital": info_dict.get("总股本", ""),
                        "circulation_share": info_dict.get("流通股", ""),
                        "industry": info_dict.get("行业", ""),
                        "listing_date": info_dict.get("上市时间", ""),
                        "company_name": info_dict.get("股票简称", ""),
                    }
            except Exception as e:
                logger.warning(f"获取公司基本信息失败: {str(e)}")
                result["company_info"] = {"error": f"获取公司基本信息失败: {str(e)}"}

            # 3. 获取财务指标
            try:
                # 获取最新的财务指标
                financial_df = ak.stock_financial_abstract_ths(symbol=clean_code)
                if not financial_df.empty:
                    # 取最新的财务数据
                    latest_financial = (
                        financial_df.iloc[-1] if len(financial_df) > 0 else None
                    )
                    if latest_financial is not None:
                        result["financial_indicators"] = {
                            "report_date": str(latest_financial.get("报告期", "")),
                            "eps": latest_financial.get("基本每股收益", 0),
                            "roe": latest_financial.get("净资产收益率", 0),
                            "net_profit_margin": latest_financial.get("销售净利率", 0),
                            "debt_to_asset_ratio": latest_financial.get(
                                "资产负债率", 0
                            ),
                        }
            except Exception as e:
                logger.warning(f"获取财务指标失败: {str(e)}")
                result["financial_indicators"] = {
                    "error": f"获取财务指标失败: {str(e)}"
                }

            # 添加元数据
            result["metadata"] = {
                "stock_code": code,
                "query_time": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data_source": "akshare",
            }

            logger.info(f"成功获取{code}的基本信息")
            return self._success_response(result)

        except Exception as e:
            error_message = traceback.format_exc()
            logger.error(f"获取A股基本信息失败: {str(e)}")
            logger.error(f"Error: {error_message}")
            return self._error_response(f"获取股票信息失败: {str(e)}")
