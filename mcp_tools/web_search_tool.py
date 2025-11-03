"""
MCP网络搜索工具
搜索网络信息
"""

import requests
import os
from typing import Any, Dict
from urllib.parse import quote
from .base_tool import MCPBaseTool
from logger import get_logger

# 获取日志记录器
logger = get_logger()


class MCPWebSearchTool(MCPBaseTool):
    """MCP网络搜索工具"""

    def __init__(self):
        super().__init__(
            name="search_web_info",
            description="搜索网络信息",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索查询"},
                    "max_results": {
                        "type": "integer",
                        "description": "最大结果数，默认5",
                    },
                },
                "required": ["query"],
            },
        )
        self.serp_api_key = os.getenv("SERP_API_KEY")
        self.serpapi_api_key = os.getenv("SERPAPI_API_KEY")

    def _search_with_serpapi(self, query: str, max_results: int = 5):
        """使用SerpAPI进行搜索"""
        try:
            api_key = self.serpapi_api_key or self.serp_api_key
            if not api_key:
                return None

            url = "https://serpapi.com/search"
            params = {
                "q": query,
                "api_key": api_key,
                "engine": "google",
                "num": min(max_results, 10),
                "gl": "us",
                "hl": "en",
            }

            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if "error" in data:
                logger.error(f"SerpAPI错误: {data['error']}")
                return None

            search_results = {
                "query": query,
                "search_engine": "Google (via SerpAPI)",
                "total_results": len(data.get("organic_results", [])),
                "results": [],
            }

            # 处理有机搜索结果
            for result in data.get("organic_results", [])[:max_results]:
                search_result = {
                    "title": result.get("title", ""),
                    "link": result.get("link", ""),
                    "snippet": result.get("snippet", ""),
                    "displayed_link": result.get("displayed_link", ""),
                    "position": result.get("position", 0),
                }

                if search_result["title"] and search_result["link"]:
                    search_results["results"].append(search_result)

            # 添加知识图谱信息（如果有）
            if "knowledge_graph" in data:
                kg = data["knowledge_graph"]
                search_results["knowledge_graph"] = {
                    "title": kg.get("title", ""),
                    "type": kg.get("type", ""),
                    "description": kg.get("description", ""),
                    "source": kg.get("source", {}).get("name", ""),
                }

            # 添加答案框信息（如果有）
            if "answer_box" in data:
                ab = data["answer_box"]
                search_results["answer_box"] = {
                    "answer": ab.get("answer", ""),
                    "title": ab.get("title", ""),
                    "source": ab.get("source", ""),
                }

            return search_results

        except Exception as e:
            logger.error(f"SerpAPI搜索失败: {str(e)}")
            return None

    def _search_with_duckduckgo(self, query: str, max_results: int = 5):
        """使用DuckDuckGo搜索（作为备用）"""
        try:
            from duckduckgo_search import DDGS

            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))

            search_results = {
                "query": query,
                "search_engine": "DuckDuckGo",
                "total_results": len(results),
                "results": [],
            }

            for i, result in enumerate(results):
                search_result = {
                    "title": result.get("title", ""),
                    "link": result.get("href", ""),
                    "snippet": result.get("body", ""),
                    "position": i + 1,
                }

                if search_result["title"] and search_result["link"]:
                    search_results["results"].append(search_result)

            return search_results

        except ImportError:
            logger.warning("duckduckgo_search包未安装，无法使用DuckDuckGo搜索")
            return None
        except Exception as e:
            logger.error(f"DuckDuckGo搜索失败: {str(e)}")
            return None

    def _enhance_financial_search(self, query: str, search_results: dict):
        """增强金融类搜索结果"""
        # 检查是否是金融相关查询
        financial_keywords = [
            "stock",
            "stocks",
            "share",
            "shares",
            "ticker",
            "earnings",
            "revenue",
            "profit",
            "financial",
            "investment",
            "market",
            "trading",
            "portfolio",
            "dividend",
            "pe ratio",
            "market cap",
        ]

        is_financial = any(keyword in query.lower() for keyword in financial_keywords)

        if is_financial:
            # 为金融搜索添加相关性评分
            for result in search_results.get("results", []):
                title_text = result.get("title", "").lower()
                snippet_text = result.get("snippet", "").lower()

                relevance_score = 0

                # 检查金融关键词
                for keyword in financial_keywords:
                    if keyword in title_text:
                        relevance_score += 2
                    if keyword in snippet_text:
                        relevance_score += 1

                # 检查权威财经网站
                financial_domains = [
                    "bloomberg.com",
                    "reuters.com",
                    "cnbc.com",
                    "marketwatch.com",
                    "yahoo.com/finance",
                    "wsj.com",
                    "ft.com",
                    "sec.gov",
                ]

                link = result.get("link", "").lower()
                for domain in financial_domains:
                    if domain in link:
                        relevance_score += 3
                        break

                result["relevance_score"] = relevance_score
                result["is_financial_source"] = any(
                    domain in link for domain in financial_domains
                )

            # 按相关性重新排序
            search_results["results"].sort(
                key=lambda x: x.get("relevance_score", 0), reverse=True
            )
            search_results["enhanced_for_finance"] = True

        return search_results

    async def execute(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """搜索网络信息"""
        logger.info(f"搜索网络信息: 查询={query}, 最大结果数={max_results}")

        search_results = None

        # 尝试使用SerpAPI
        if self.serp_api_key or self.serpapi_api_key:
            logger.info("尝试使用SerpAPI搜索...")
            search_results = self._search_with_serpapi(query, max_results)

        # 如果SerpAPI失败，尝试DuckDuckGo
        if not search_results:
            logger.info("尝试使用DuckDuckGo搜索...")
            search_results = self._search_with_duckduckgo(query, max_results)

        # 如果都失败，返回搜索失败的错误
        if not search_results:
            logger.error("所有搜索方法都失败")
            return self._error_response(
                "搜索失败：无法连接到搜索引擎API或网络服务不可用。请检查网络连接或配置有效的搜索API密钥。"
            )

        # 增强金融搜索结果
        search_results = self._enhance_financial_search(query, search_results)

        # 添加元数据
        search_results["metadata"] = {
            "query": query,
            "requested_results": max_results,
            "actual_results": len(search_results.get("results", [])),
            "search_timestamp": "实时搜索",
            "api_used": search_results.get("search_engine", "Unknown"),
            "note": "搜索结果实时性和准确性取决于搜索引擎和API可用性",
        }

        logger.info(
            f"搜索完成: {query}, 返回{len(search_results.get('results', []))}个结果"
        )
        return self._success_response(search_results)
