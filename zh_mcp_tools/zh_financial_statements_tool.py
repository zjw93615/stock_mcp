"""
中文股票财务报表工具
使用akshare获取A股财务报表数据
"""

import traceback
import akshare as ak
import pandas as pd
from typing import Any, Dict
from .base_tool import ZHMCPBaseTool
from logger import get_logger

# 获取日志记录器
logger = get_logger()


class ZHMCPFinancialStatementsTool(ZHMCPBaseTool):
    """中文股票财务报表工具"""

    def __init__(self):
        super().__init__(
            name="get_zh_financial_statements",
            description="获取A股公司财务报表数据，包括利润表、资产负债表和现金流量表",
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

    async def execute(self, code: str) -> Dict[str, Any]:
        """获取财务报表数据"""
        logger.info(f"获取A股财务报表: {code}")

        try:
            # 标准化股票代码，移除交易所后缀
            clean_code = code.split(".")[0]

            result = {
                "stock_code": code,
                "data_source": "akshare",
            }

            try:
                income_df = ak.stock_financial_abstract_ths(symbol=clean_code)
                if not income_df.empty:
                    # 取最近4个报告期的数据
                    recent_income = income_df.head(4)
                    result["data"] = recent_income.to_dict("records")
            except Exception as e:
                logger.warning(f"获取利润表数据失败: {str(e)}")
                result["income_statement"] = {"error": f"获取利润表数据失败: {str(e)}"}

            # 添加查询时间
            result["query_time"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")

            logger.info(f"成功获取{code}的财务报表数据")
            return self._success_response(result)

        except Exception as e:
            error_message = traceback.format_exc()
            logger.error(f"获取A股财务报表失败: {str(e)}")
            logger.error(f"Error: {error_message}")
            return self._error_response(f"获取财务报表失败: {str(e)}")

    def _extract_income_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """提取利润表关键指标"""
        if df.empty:
            return {}

        latest = df.iloc[0] if len(df) > 0 else {}
        metrics = {}

        # 提取关键财务指标
        key_fields = [
            "营业总收入",
            "营业收入",
            "营业总成本",
            "营业成本",
            "销售费用",
            "管理费用",
            "财务费用",
            "营业利润",
            "利润总额",
            "净利润",
            "每股收益",
            "净资产收益率",
            "销售毛利率",
            "销售净利率",
        ]

        for field in key_fields:
            if field in latest:
                metrics[field] = latest[field]

        return metrics

    def _extract_balance_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """提取资产负债表关键指标"""
        if df.empty:
            return {}

        latest = df.iloc[0] if len(df) > 0 else {}
        metrics = {}

        # 提取关键指标
        key_fields = [
            "总资产",
            "流动资产",
            "非流动资产",
            "总负债",
            "流动负债",
            "非流动负债",
            "股东权益合计",
            "资产负债率",
        ]

        for field in key_fields:
            if field in latest:
                metrics[field] = latest[field]

        return metrics

    def _extract_cashflow_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """提取现金流量表关键指标"""
        if df.empty:
            return {}

        latest = df.iloc[0] if len(df) > 0 else {}
        metrics = {}

        # 提取关键指标
        key_fields = [
            "经营活动产生的现金流量净额",
            "投资活动产生的现金流量净额",
            "筹资活动产生的现金流量净额",
            "现金及现金等价物净增加额",
            "期末现金及现金等价物余额",
        ]

        for field in key_fields:
            if field in latest:
                metrics[field] = latest[field]

        return metrics

    def _calculate_financial_ratios(self, df: pd.DataFrame) -> Dict[str, Any]:
        """计算财务比率"""
        if df.empty:
            return {}

        latest = df.iloc[0] if len(df) > 0 else {}
        ratios = {}

        # 盈利能力指标
        if "净资产收益率" in latest:
            ratios["ROE"] = latest["净资产收益率"]
        if "总资产收益率" in latest:
            ratios["ROA"] = latest["总资产收益率"]
        if "销售净利率" in latest:
            ratios["净利率"] = latest["销售净利率"]

        # 偿债能力指标
        if "资产负债率" in latest:
            ratios["资产负债率"] = latest["资产负债率"]

        # 成长性指标
        if len(df) >= 2:
            current = df.iloc[0]
            previous = df.iloc[1]

            # 计算同比增长率
            for field in ["营业收入", "净利润"]:
                if field in current and field in previous:
                    try:
                        current_val = float(current[field]) if current[field] else 0
                        previous_val = float(previous[field]) if previous[field] else 0
                        if previous_val != 0:
                            growth_rate = (
                                (current_val - previous_val) / previous_val
                            ) * 100
                            ratios[f"{field}同比增长率"] = growth_rate
                    except (ValueError, TypeError):
                        continue

        return ratios

    def _extract_summary_ratios(self, df: pd.DataFrame) -> Dict[str, Any]:
        """从财务摘要中提取比率"""
        if df.empty:
            return {}

        latest = df.iloc[0] if len(df) > 0 else {}
        ratios = {}

        # 提取可用的财务比率
        ratio_fields = [
            "净资产收益率",
            "总资产收益率",
            "销售毛利率",
            "销售净利率",
            "资产负债率",
            "每股收益",
            "每股净资产",
        ]

        for field in ratio_fields:
            if field in latest:
                ratios[field] = latest[field]

        return ratios
