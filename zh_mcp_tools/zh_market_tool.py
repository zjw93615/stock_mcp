"""
中文股票市场工具
使用akshare获取A股市场数据，包括指数、板块、资金流向等
"""

import traceback
import akshare as ak
import pandas as pd
from typing import Any, Dict
from .base_tool import ZHMCPBaseTool
from logger import get_logger

# 获取日志记录器
logger = get_logger()


class ZHMCPMarketTool(ZHMCPBaseTool):
    """中文股票市场工具"""

    def __init__(self):
        super().__init__(
            name="get_zh_market_data",
            description="获取A股市场数据，包括指数信息、板块数据、资金流向、涨跌榜等",
            input_schema={
                "type": "object",
                "properties": {
                    "data_type": {
                        "type": "string",
                        "description": "数据类型：index(指数), sector(板块), top_list(涨跌榜), money_flow(资金流向)",
                        "default": "index",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "数据数量限制，默认10条",
                        "default": 10,
                    },
                },
                "required": ["data_type"],
            },
        )

    async def execute(
        self, data_type: str = "index", limit: int = 10
    ) -> Dict[str, Any]:
        """获取市场数据"""
        logger.info(f"获取A股市场数据: 数据类型={data_type}, 数量限制={limit}")

        try:
            result = {
                "data_type": data_type,
                "limit": limit,
                "query_time": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            # 根据数据类型获取不同的市场数据
            if data_type == "index":
                result["data"] = await self._get_index_data(limit)
            elif data_type == "sector":
                result["data"] = await self._get_sector_data(limit)
            elif data_type == "top_list":
                result["data"] = await self._get_top_list_data(limit)
            elif data_type == "money_flow":
                result["data"] = await self._get_money_flow_data(limit)
            else:
                result["data"] = await self._get_index_data(limit)

            logger.info(f"成功获取{data_type}市场数据")
            return self._success_response(result)

        except Exception as e:
            error_message = traceback.format_exc()
            logger.error(f"获取A股市场数据失败: {str(e)}")
            logger.error(f"Error: {error_message}")
            return self._error_response(f"获取市场数据失败: {str(e)}")

    async def _get_index_data(self, limit: int) -> Dict[str, Any]:
        """获取指数数据"""
        try:
            # 直接使用深证交易所汇总数据获取指数信息，使用当前日期
            current_date = pd.Timestamp.now().strftime("%Y%m%d")
            szse_summary = ak.stock_szse_summary(date=current_date)

            if szse_summary.empty:
                logger.warning("深证交易所汇总数据为空，使用备用方案")

            indices_data = []

            # 从深证汇总数据中提取指数信息
            for _, row in szse_summary.head(limit).iterrows():
                try:
                    index_item = {
                        "name": row.get("证券类别", ""),
                        "num": row.get("数量", ""),
                        "transaction_amount": float(row.get("成交金额", 0)),
                        "total_market_capitalization": float(row.get("总市值", 0)),
                        "circulating_market_capitalization": float(
                            row.get("流通市值", 0)
                        ),
                    }
                    indices_data.append(index_item)

                except Exception as idx_error:
                    logger.warning(f"处理指数数据失败: {str(idx_error)}")
                    continue

            # 如果没有获取到数据，使用备用方案
            if not indices_data:
                logger.warning("处理深证汇总数据失败，使用备用方案")

            return {
                "indices": indices_data,
                "market_summary": self._generate_market_summary(indices_data),
                "data_source": "深证交易所汇总数据",
            }

        except Exception as e:
            logger.warning(f"获取指数数据失败: {str(e)}")
            return {"error": "无法获取指数数据，建议检查网络连接"}
            # 备用方案：返回固定的主要指数信息

    async def _get_sector_data(self, limit: int) -> Dict[str, Any]:
        """获取板块数据"""
        try:
            # 获取行业板块数据
            sector_df = ak.stock_board_industry_name_em()

            if sector_df.empty:
                return {"error": "获取板块数据为空"}

            sectors_data = []
            for _, row in sector_df.head(limit).iterrows():
                sector_item = {
                    "name": str(row.get("板块名称", "")),
                    "code": str(row.get("板块代码", "")),
                    "stock_count": int(row.get("公司家数", 0)),
                    "average_price": float(row.get("平均价格", 0)),
                    "change_percent": float(row.get("涨跌幅", 0)),
                    "change_amount": float(row.get("涨跌额", 0)),
                    "amount": float(row.get("总成交量", 0)),
                    "net_inflow": float(row.get("净流入", 0)),
                    "leading_stock": str(row.get("领涨股票", "")),
                    "leading_stock_change": float(row.get("领涨股票涨跌幅", 0)),
                }
                sectors_data.append(sector_item)

            return {
                "sectors": sectors_data,
                "top_sectors": self._get_top_sectors(sectors_data),
            }

        except Exception as e:
            logger.warning(f"获取板块数据失败: {str(e)}")
            return {"error": f"获取板块数据失败: {str(e)}"}

    async def _get_top_list_data(self, limit: int) -> Dict[str, Any]:
        """获取涨跌榜数据"""
        try:
            # 获取涨幅榜
            up_df = ak.stock_zh_a_spot_em()
            if not up_df.empty:
                # 按涨跌幅排序
                up_sorted = up_df.sort_values("涨跌幅", ascending=False)
                down_sorted = up_df.sort_values("涨跌幅", ascending=True)

                # 涨幅榜前N名
                top_gainers = []
                for _, row in up_sorted.head(limit).iterrows():
                    stock_item = {
                        "code": str(row.get("代码", "")),
                        "name": str(row.get("名称", "")),
                        "current_price": float(row.get("最新价", 0)),
                        "change_percent": float(row.get("涨跌幅", 0)),
                        "change_amount": float(row.get("涨跌额", 0)),
                        "volume": float(row.get("成交量", 0)),
                        "amount": float(row.get("成交额", 0)),
                        "turnover_rate": float(row.get("换手率", 0)),
                        "pe_ratio": float(row.get("市盈率-动态", 0)),
                        "market_cap": float(row.get("总市值", 0)),
                    }
                    top_gainers.append(stock_item)

                # 跌幅榜前N名
                top_losers = []
                for _, row in down_sorted.head(limit).iterrows():
                    stock_item = {
                        "code": str(row.get("代码", "")),
                        "name": str(row.get("名称", "")),
                        "current_price": float(row.get("最新价", 0)),
                        "change_percent": float(row.get("涨跌幅", 0)),
                        "change_amount": float(row.get("涨跌额", 0)),
                        "volume": float(row.get("成交量", 0)),
                        "amount": float(row.get("成交额", 0)),
                        "turnover_rate": float(row.get("换手率", 0)),
                        "pe_ratio": float(row.get("市盈率-动态", 0)),
                        "market_cap": float(row.get("总市值", 0)),
                    }
                    top_losers.append(stock_item)

                return {
                    "top_gainers": top_gainers,
                    "top_losers": top_losers,
                    "market_statistics": self._calculate_market_stats(up_df),
                }

            return {"error": "获取涨跌榜数据为空"}

        except Exception as e:
            logger.warning(f"获取涨跌榜数据失败: {str(e)}")
            return {"error": f"获取涨跌榜数据失败: {str(e)}"}

    async def _get_money_flow_data(self, limit: int) -> Dict[str, Any]:
        """获取资金流向数据"""
        try:
            # 获取个股资金流向数据
            money_flow_df = ak.stock_individual_fund_flow_rank(indicator="今日")

            if money_flow_df.empty:
                return {"error": "获取资金流向数据为空"}

            money_flow_data = []
            for _, row in money_flow_df.head(limit).iterrows():
                flow_item = {
                    "code": str(row.get("代码", "")),
                    "name": str(row.get("名称", "")),
                    "current_price": float(row.get("最新价", 0)),
                    "change_percent": float(row.get("涨跌幅", 0)),
                    "main_net_inflow": float(row.get("主力净流入-净额", 0)),
                    "main_net_inflow_percent": float(row.get("主力净流入-净占比", 0)),
                    "super_large_inflow": float(row.get("超大单净流入-净额", 0)),
                    "super_large_inflow_percent": float(
                        row.get("超大单净流入-净占比", 0)
                    ),
                    "large_inflow": float(row.get("大单净流入-净额", 0)),
                    "large_inflow_percent": float(row.get("大单净流入-净占比", 0)),
                    "medium_inflow": float(row.get("中单净流入-净额", 0)),
                    "medium_inflow_percent": float(row.get("中单净流入-净占比", 0)),
                    "small_inflow": float(row.get("小单净流入-净额", 0)),
                    "small_inflow_percent": float(row.get("小单净流入-净占比", 0)),
                }
                money_flow_data.append(flow_item)

            return {
                "money_flow_ranking": money_flow_data,
                "flow_summary": self._analyze_money_flow(money_flow_data),
            }

        except Exception as e:
            logger.warning(f"获取资金流向数据失败: {str(e)}")
            return {"error": f"获取资金流向数据失败: {str(e)}"}

    def _generate_market_summary(self, indices_data: list) -> Dict[str, Any]:
        """生成市场摘要"""
        if not indices_data:
            return {}

        up_count = sum(1 for idx in indices_data if idx["change_percent"] > 0)
        down_count = sum(1 for idx in indices_data if idx["change_percent"] < 0)
        flat_count = len(indices_data) - up_count - down_count

        return {
            "total_indices": len(indices_data),
            "up_count": up_count,
            "down_count": down_count,
            "flat_count": flat_count,
            "market_sentiment": (
                "偏多"
                if up_count > down_count
                else "偏空" if down_count > up_count else "平衡"
            ),
        }

    def _get_top_sectors(self, sectors_data: list) -> Dict[str, Any]:
        """获取表现最好和最差的板块"""
        if not sectors_data:
            return {}

        # 按涨跌幅排序
        sorted_sectors = sorted(
            sectors_data, key=lambda x: x["change_percent"], reverse=True
        )

        return {
            "top_3_gainers": sorted_sectors[:3],
            "top_3_losers": sorted_sectors[-3:],
        }

    def _calculate_market_stats(self, market_df: pd.DataFrame) -> Dict[str, Any]:
        """计算市场统计数据"""
        if market_df.empty:
            return {}

        up_count = len(market_df[market_df["涨跌幅"] > 0])
        down_count = len(market_df[market_df["涨跌幅"] < 0])
        flat_count = len(market_df[market_df["涨跌幅"] == 0])

        limit_up = len(
            market_df[market_df["涨跌幅"] >= 9.5]
        )  # 涨停数量（考虑不同涨停幅度）
        limit_down = len(market_df[market_df["涨跌幅"] <= -9.5])  # 跌停数量

        return {
            "total_stocks": len(market_df),
            "up_count": up_count,
            "down_count": down_count,
            "flat_count": flat_count,
            "limit_up_count": limit_up,
            "limit_down_count": limit_down,
            "up_down_ratio": (
                round(up_count / down_count, 2) if down_count > 0 else float("inf")
            ),
        }

    def _analyze_money_flow(self, flow_data: list) -> Dict[str, Any]:
        """分析资金流向"""
        if not flow_data:
            return {}

        # 统计主力净流入为正的股票数量
        main_inflow_positive = sum(
            1 for item in flow_data if item["main_net_inflow"] > 0
        )
        main_inflow_negative = len(flow_data) - main_inflow_positive

        # 计算总的主力净流入
        total_main_inflow = sum(item["main_net_inflow"] for item in flow_data)

        return {
            "main_inflow_positive_count": main_inflow_positive,
            "main_inflow_negative_count": main_inflow_negative,
            "total_main_net_inflow": total_main_inflow,
            "market_fund_sentiment": (
                "资金净流入" if total_main_inflow > 0 else "资金净流出"
            ),
        }
