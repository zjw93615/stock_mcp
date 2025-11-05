"""
MCP新闻工具
获取股票相关新闻
"""

import yfinance as yf
import requests
import os
from typing import Any, Dict
from .base_tool import MCPBaseTool
from logger import get_logger

# 获取日志记录器
logger = get_logger()


class MCPNewsTool(MCPBaseTool):
    """MCP新闻工具"""

    def __init__(self):
        super().__init__(
            name="get_news",
            description="获取股票相关新闻",
            input_schema={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "股票代码，如AAPL"},
                    "limit": {
                        "type": "integer",
                        "description": "新闻数量限制，默认10条",
                    },
                },
                "required": ["ticker"],
            },
        )
        self.news_api_key = os.getenv("NEWS_API_KEY")

    def _get_yfinance_news(self, ticker: str, limit: int = 10):
        """使用yfinance获取新闻"""
        try:
            stock = yf.Ticker(ticker)
            news = stock.news[:limit] if hasattr(stock, "news") and stock.news else []

            news_data = {
                "ticker": ticker,
                "source": "Yahoo Finance",
                "total_count": len(news),
                "news": [],
            }

            for item in news:
                content = item.get("content", {})
                news_item = {
                    "title": content.get("title", ""),
                    "summary": content.get("summary", ""),
                    "publisher": content.get("publisher", ""),
                    "link": content.get("canonicalUrl", {}).get("url", ""),
                    "published_time": content.get("pubDate", ""),
                }

                # 清理和验证数据
                if news_item["title"] and news_item["title"].strip():
                    news_data["news"].append(news_item)

            return news_data

        except Exception as e:
            logger.error(f"使用yfinance获取新闻失败: {str(e)}")
            return None

    def _get_newsapi_news(self, ticker: str, limit: int = 10):
        """使用News API获取新闻"""
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": f"{ticker} stock OR {ticker} company OR {ticker} earnings",
                "apiKey": self.news_api_key,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": min(limit, 100),  # API限制
                "sources": "bloomberg,reuters,cnbc,the-wall-street-journal,financial-times",
            }

            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if data.get("status") != "ok":
                logger.error(f"News API错误: {data.get('message', '未知错误')}")
                return None

            news_data = {
                "ticker": ticker,
                "source": "News API",
                "total_count": data.get("totalResults", 0),
                "news": [],
            }

            for article in data.get("articles", []):
                news_item = {
                    "title": article.get("title", ""),
                    "description": article.get("description", ""),
                    "source": article.get("source", {}).get("name", ""),
                    "author": article.get("author", ""),
                    "url": article.get("url", ""),
                    "published_at": article.get("publishedAt", ""),
                    "url_to_image": article.get("urlToImage", ""),
                }

                # 过滤掉无关或低质量的新闻
                if (
                    news_item["title"]
                    and news_item["title"].strip()
                    and ticker.upper() in news_item["title"].upper()
                ):
                    news_data["news"].append(news_item)

            return news_data

        except Exception as e:
            logger.error(f"使用News API获取新闻失败: {str(e)}")
            return None

    def _get_gnews_fallback(self, ticker: str, limit: int = 10):
        """使用GNews作为备用新闻源"""
        try:
            from gnews import GNews

            google_news = GNews(
                language="en", country="US", period="7d", max_results=limit  # 最近7天
            )

            # 搜索股票相关新闻
            search_queries = [
                f"{ticker} stock",
                f"{ticker} earnings",
                f"{ticker} company news",
            ]

            all_news = []
            for query in search_queries:
                try:
                    news = google_news.get_news(query)
                    all_news.extend(news[: limit // len(search_queries)])
                except Exception as e:
                    logger.warning(f"GNews查询 '{query}' 失败: {str(e)}")
                    continue

            news_data = {
                "ticker": ticker,
                "source": "Google News",
                "total_count": len(all_news),
                "news": [],
            }

            for item in all_news[:limit]:
                news_item = {
                    "title": item.get("title", ""),
                    "description": item.get("description", ""),
                    "publisher": (
                        item.get("publisher", {}).get("title", "")
                        if isinstance(item.get("publisher"), dict)
                        else str(item.get("publisher", ""))
                    ),
                    "url": item.get("url", ""),
                    "published_date": item.get("published date", ""),
                }

                if news_item["title"] and news_item["title"].strip():
                    news_data["news"].append(news_item)

            return news_data

        except ImportError:
            logger.warning("GNews包未安装，跳过Google News备用源")
            return None
        except Exception as e:
            logger.error(f"使用GNews获取新闻失败: {str(e)}")
            return None

    async def execute(self, ticker: str, limit: int = 10) -> Dict[str, Any]:
        """获取股票相关新闻"""
        logger.info(f"获取新闻: 股票={ticker}, 限制数量={limit}")

        news_data = None

        # 尝试多个新闻源
        # if self.news_api_key:
        #     logger.info("尝试使用News API获取新闻...")
        #     news_data = self._get_newsapi_news(ticker, limit)

        if not news_data or not news_data.get("news"):
            logger.info("使用Yahoo Finance获取新闻...")
            news_data = self._get_yfinance_news(ticker, limit)

        if not news_data or not news_data.get("news"):
            logger.info("尝试使用Google News作为备用...")
            news_data = self._get_gnews_fallback(ticker, limit)

        if not news_data:
            return self._error_response("无法从任何新闻源获取数据")

        if not news_data.get("news"):
            return self._error_response(f"未找到关于 {ticker} 的相关新闻")

        # 添加元数据
        news_data["metadata"] = {
            "query_ticker": ticker,
            "requested_limit": limit,
            "actual_count": len(news_data["news"]),
            "data_source": news_data.get("source", "Unknown"),
            "note": "新闻数据实时性取决于数据源，建议结合多个来源进行分析",
        }

        # 对新闻进行基本的相关性评分（简单实现）
        for news_item in news_data["news"]:
            title_text = news_item.get("title", "").upper()
            desc_text = (
                news_item.get("description", "").upper()
                if news_item.get("description")
                else ""
            )

            relevance_score = 0
            ticker_upper = ticker.upper()

            # 标题中包含股票代码
            if ticker_upper in title_text:
                relevance_score += 3

            # 描述中包含股票代码
            if ticker_upper in desc_text:
                relevance_score += 2

            # 包含关键财经词汇
            financial_keywords = [
                "EARNINGS",
                "REVENUE",
                "PROFIT",
                "STOCK",
                "SHARES",
                "QUARTERLY",
                "ANNUAL",
            ]
            for keyword in financial_keywords:
                if keyword in title_text or keyword in desc_text:
                    relevance_score += 1
                    break

            news_item["relevance_score"] = relevance_score

        # 按相关性排序
        news_data["news"].sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

        logger.info(f"成功获取{ticker}的新闻，共{len(news_data['news'])}条")
        return self._success_response(news_data)
