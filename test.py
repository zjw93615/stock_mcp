
from dotenv import load_dotenv
load_dotenv()
from qwen_agent import settings
import yfinance as yf
import json
print("settings", settings.MAX_LLM_CALL_PER_RUN)


def _get_yfinance_news(ticker: str, limit: int = 10):
        """使用yfinance获取新闻"""
        try:
            stock = yf.Ticker(ticker)
            # print("stock.news", stock.news, hasattr(stock, "news"))
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
                
                print("news_item", json.dumps(news_item))
                # 清理和验证数据
                if news_item["title"] and news_item["title"].strip():
                    news_data["news"].append(news_item)

            return news_data

        except Exception as e:
            print(str(e))
            # logger.error(f"使用yfinance获取新闻失败: {str(e)}")
            return None
        

# print(_get_yfinance_news("AAPL"))