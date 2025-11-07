"""
中文股票新闻工具
使用akshare的stock_news_em获取个股新闻信息
"""

import traceback
import akshare as ak
import pandas as pd
from typing import Any, Dict
from .base_tool import ZHMCPBaseTool
from logger import get_logger

# 获取日志记录器
logger = get_logger()


class ZHMCPNewsTool(ZHMCPBaseTool):
    """中文股票新闻工具"""

    def __init__(self):
        super().__init__(
            name="get_stock_news",
            description="获取个股新闻信息，使用东方财富数据源",
            input_schema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "股票代码，如000001、600000等",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "新闻数量限制，默认10条",
                        "default": 10,
                    },
                },
                "required": ["symbol"],
            },
        )

    async def execute(self, symbol: str, limit: int = 10) -> Dict[str, Any]:
        """获取个股新闻信息"""
        logger.info(f"获取个股新闻: 股票代码={symbol}, 数量限制={limit}")

        try:
            # 使用stock_news_em获取个股新闻
            news_df = ak.stock_news_em(symbol=symbol)

            if news_df.empty:
                logger.warning(f"未找到股票 {symbol} 的新闻信息")
                return self._success_response(
                    {
                        "symbol": symbol,
                        "limit": limit,
                        "query_time": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "news": [],
                        "news_count": 0,
                    }
                )

            # 格式化新闻数据
            news_list = []
            for idx, row in news_df.head(limit).iterrows():
                news_item = {
                    "title": str(row.get("新闻标题", "")),
                    "content": str(row.get("新闻内容", "")),
                    "publish_time": str(row.get("发布时间", "")),
                    "source": "东方财富",
                    "url": str(row.get("新闻链接", "")),
                }
                news_list.append(news_item)

            result = {
                "symbol": symbol,
                "limit": limit,
                "query_time": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                "news": news_list,
                "news_count": len(news_list),
            }

            logger.info(f"成功获取{len(news_list)}条新闻")
            return self._success_response(result)

        except Exception as e:
            error_message = traceback.format_exc()
            logger.error(f"获取个股新闻失败: {str(e)}")
            logger.error(f"Error: {error_message}")
            return self._error_response(f"获取个股新闻失败: {str(e)}")
