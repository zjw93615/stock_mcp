"""
MCP财务报表工具
获取公司财务报表数据，包括损益表、资产负债表和现金流量表
"""

import yfinance as yf
import pandas as pd
from typing import Any, Dict
from .base_tool import MCPBaseTool
from logger import get_logger

# 获取日志记录器
logger = get_logger()


class MCPFinancialStatementsTool(MCPBaseTool):
    """MCP财务报表工具"""

    def __init__(self):
        super().__init__(
            name="get_financial_statements",
            description="获取公司完整财务报表数据，包括损益表、资产负债表和现金流量表",
            input_schema={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "股票代码，如AAPL"},
                },
                "required": ["ticker"],
            },
        )

    def _process_financial_data(self, financials, statement_type, ticker):
        """处理财务数据，转换为可序列化格式"""
        if financials.empty:
            return None

        financial_data = {
            "ticker": ticker,
            "statement_type": statement_type,
            "periods": [],
            "data": {},
        }

        # 获取可用的时间期间（最多4个最近期间）
        periods = financials.columns[:4]

        for period in periods:
            period_str = period.strftime("%Y-%m-%d")
            financial_data["periods"].append(period_str)
            financial_data["data"][period_str] = {}

            # 根据报表类型选择重要指标
            if statement_type == "income":
                important_fields = [
                    "Total Revenue",
                    "Revenue",
                    "Net Income",
                    "Gross Profit",
                    "Operating Income",
                    "EBITDA",
                    "Basic EPS",
                    "Diluted EPS",
                    "Operating Revenue",
                    "Cost Of Revenue",
                    "Operating Expense",
                    "Interest Expense",
                    "Tax Provision",
                    "Net Income Common Stockholders",
                ]
            elif statement_type == "balance":
                important_fields = [
                    "Total Assets",
                    "Total Liabilities Net Minority Interest",
                    "Stockholders Equity",
                    "Current Assets",
                    "Current Liabilities",
                    "Cash And Cash Equivalents",
                    "Total Debt",
                    "Net Debt",
                    "Working Capital",
                    "Retained Earnings",
                    "Total Capitalization",
                ]
            else:  # cash flow
                important_fields = [
                    "Operating Cash Flow",
                    "Investing Cash Flow",
                    "Financing Cash Flow",
                    "Net Income From Continuing Ops",
                    "Capital Expenditure",
                    "Free Cash Flow",
                    "Change In Cash",
                    "Depreciation And Amortization",
                    "Stock Based Compensation",
                    "Change In Working Capital",
                ]

            # 获取所有可用字段，优先选择重要字段
            available_fields = list(financials.index)
            selected_fields = []

            # 先添加重要字段
            for field in important_fields:
                if field in available_fields:
                    selected_fields.append(field)

            # 如果重要字段不足，添加其他字段（最多20个）
            remaining_fields = [f for f in available_fields if f not in selected_fields]
            selected_fields.extend(
                remaining_fields[: max(0, 20 - len(selected_fields))]
            )

            # 提取数据
            for field in selected_fields:
                try:
                    value = financials.loc[field, period]
                    if pd.notna(value):
                        financial_data["data"][period_str][field] = float(value)
                except (KeyError, ValueError):
                    continue

        return financial_data

    async def execute(self, ticker: str) -> Dict[str, Any]:
        """获取公司完整财务报表数据"""
        logger.info(f"获取完整财务报表: 股票={ticker}")

        try:
            stock = yf.Ticker(ticker)

            # 定义要获取的财务报表类型
            statement_configs = [
                {"type": "income", "data": stock.financials, "title": "损益表"},
                {"type": "balance", "data": stock.balance_sheet, "title": "资产负债表"},
                {"type": "cash", "data": stock.cashflow, "title": "现金流量表"},
            ]

            # 存储所有财务报表数据
            all_statements = {
                "ticker": ticker,
                "statements": {},
                "metadata": {
                    "available_statements": [],
                    "total_statements": 0,
                },
            }

            # 获取每种类型的财务数据
            for config in statement_configs:
                statement_type = config["type"]
                financials = config["data"]
                title = config["title"]

                if not financials.empty:
                    # 处理财务数据
                    processed_data = self._process_financial_data(
                        financials, statement_type, ticker
                    )

                    if processed_data:
                        all_statements["statements"][statement_type] = {
                            "title": title,
                            "data": processed_data,
                        }
                        all_statements["metadata"]["available_statements"].append(
                            statement_type
                        )
                        logger.info(f"成功获取{ticker}的{title}数据")
                    else:
                        logger.warning(f"处理{ticker}的{title}数据失败")
                else:
                    logger.warning(f"未获取到{ticker}的{title}数据")

            # 更新元数据
            all_statements["metadata"]["total_statements"] = len(
                all_statements["statements"]
            )

            # 如果有损益表数据，计算一些基本比率
            if "income" in all_statements["statements"]:
                income_data = all_statements["statements"]["income"]["data"]
                if income_data["periods"]:
                    latest_period = income_data["periods"][0]
                    latest_data = income_data["data"][latest_period]

                    ratios = {}
                    if "Total Revenue" in latest_data and "Net Income" in latest_data:
                        if latest_data["Total Revenue"] != 0:
                            ratios["net_profit_margin"] = (
                                latest_data["Net Income"] / latest_data["Total Revenue"]
                            ) * 100

                    if "Total Revenue" in latest_data and "Gross Profit" in latest_data:
                        if latest_data["Total Revenue"] != 0:
                            ratios["gross_profit_margin"] = (
                                latest_data["Gross Profit"]
                                / latest_data["Total Revenue"]
                            ) * 100

                    if ratios:
                        all_statements["calculated_ratios"] = ratios

            # 检查是否获取到任何数据
            if not all_statements["statements"]:
                return self._error_response("未获取到任何财务报表数据")

            logger.info(
                f"成功获取{ticker}的完整财务报表数据，包含{len(all_statements['statements'])}种报表"
            )
            return self._success_response(all_statements)

        except Exception as e:
            logger.error(f"获取完整财务报表失败: {str(e)}")
            return self._error_response(str(e))
