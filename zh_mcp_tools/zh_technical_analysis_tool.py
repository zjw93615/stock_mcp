"""
中文股票技术分析工具
使用akshare数据计算技术指标
"""

import traceback
import akshare as ak
import pandas as pd
import numpy as np
from typing import Any, Dict
from .base_tool import ZHMCPBaseTool
from logger import get_logger

# 获取日志记录器
logger = get_logger()


class ZHMCPTechnicalAnalysisTool(ZHMCPBaseTool):
    """中文股票技术分析工具"""

    def __init__(self):
        super().__init__(
            name="calculate_zh_technical_indicators",
            description="计算A股技术指标，包括移动平均线(MA)、相对强弱指数(RSI)、MACD等",
            input_schema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "股票代码，如000001或000001.SZ"},
                    "start_date": {"type": "string", "description": "开始日期，格式YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "结束日期，格式YYYY-MM-DD"},
                    "indicators": {"type": "array", "items": {"type": "string"}, 
                                 "description": "要计算的指标列表，可选：MA, RSI, MACD, BOLL, KDJ", 
                                 "default": ["MA", "RSI", "MACD"]}
                },
                "required": ["code", "start_date", "end_date"],
            },
        )

    def _calculate_ma(self, df: pd.DataFrame, periods=[5, 10, 20, 60]) -> pd.DataFrame:
        """计算移动平均线"""
        for period in periods:
            df[f'MA{period}'] = df['close'].rolling(window=period).mean()
        return df
    
    def _calculate_rsi(self, df: pd.DataFrame, period=14) -> pd.DataFrame:
        """计算相对强弱指数"""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        return df
    
    def _calculate_macd(self, df: pd.DataFrame, fast=12, slow=26, signal=9) -> pd.DataFrame:
        """计算MACD指标"""
        ema_fast = df['close'].ewm(span=fast).mean()
        ema_slow = df['close'].ewm(span=slow).mean()
        df['MACD'] = ema_fast - ema_slow
        df['MACD_signal'] = df['MACD'].ewm(span=signal).mean()
        df['MACD_histogram'] = df['MACD'] - df['MACD_signal']
        return df
    
    def _calculate_bollinger_bands(self, df: pd.DataFrame, period=20, std_dev=2) -> pd.DataFrame:
        """计算布林带"""
        df['BOLL_middle'] = df['close'].rolling(window=period).mean()
        std = df['close'].rolling(window=period).std()
        df['BOLL_upper'] = df['BOLL_middle'] + (std * std_dev)
        df['BOLL_lower'] = df['BOLL_middle'] - (std * std_dev)
        return df
    
    def _calculate_kdj(self, df: pd.DataFrame, period=9) -> pd.DataFrame:
        """计算KDJ指标"""
        high_n = df['high'].rolling(window=period).max()
        low_n = df['low'].rolling(window=period).min()
        
        rsv = ((df['close'] - low_n) / (high_n - low_n)) * 100
        df['K'] = rsv.ewm(com=2).mean()
        df['D'] = df['K'].ewm(com=2).mean()
        df['J'] = 3 * df['K'] - 2 * df['D']
        return df

    async def execute(self, code: str, start_date: str, end_date: str, 
                     indicators: list = None) -> Dict[str, Any]:
        """计算技术指标"""
        if indicators is None:
            indicators = ["MA", "RSI", "MACD"]
        
        logger.info(f"计算A股技术指标: {code}, 指标: {indicators}")

        try:
            # 标准化股票代码，移除交易所后缀
            clean_code = code.split('.')[0]
            
            # 获取历史数据
            df = ak.stock_zh_a_hist(symbol=clean_code, period="daily", 
                                  start_date=start_date.replace('-', ''), 
                                  end_date=end_date.replace('-', ''), 
                                  adjust="qfq")

            if df is None or df.empty:
                return self._error_response(f"未找到股票代码 {code} 的历史数据")

            # 重命名列
            column_mapping = {
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close', 
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume'
            }
            df = df.rename(columns=column_mapping)
            
            # 确保数据类型正确
            for col in ['open', 'close', 'high', 'low', 'volume']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 计算指定的技术指标
            calculated_indicators = {}
            
            if "MA" in indicators:
                df = self._calculate_ma(df)
                calculated_indicators['MA'] = {
                    'MA5': df['MA5'].dropna().tail(10).to_dict() if 'MA5' in df.columns else {},
                    'MA10': df['MA10'].dropna().tail(10).to_dict() if 'MA10' in df.columns else {},
                    'MA20': df['MA20'].dropna().tail(10).to_dict() if 'MA20' in df.columns else {},
                    'MA60': df['MA60'].dropna().tail(10).to_dict() if 'MA60' in df.columns else {}
                }
            
            if "RSI" in indicators:
                df = self._calculate_rsi(df)
                calculated_indicators['RSI'] = df['RSI'].dropna().tail(10).to_dict() if 'RSI' in df.columns else {}
            
            if "MACD" in indicators:
                df = self._calculate_macd(df)
                calculated_indicators['MACD'] = {
                    'MACD': df['MACD'].dropna().tail(10).to_dict() if 'MACD' in df.columns else {},
                    'Signal': df['MACD_signal'].dropna().tail(10).to_dict() if 'MACD_signal' in df.columns else {},
                    'Histogram': df['MACD_histogram'].dropna().tail(10).to_dict() if 'MACD_histogram' in df.columns else {}
                }
            
            if "BOLL" in indicators:
                df = self._calculate_bollinger_bands(df)
                calculated_indicators['Bollinger_Bands'] = {
                    'Upper': df['BOLL_upper'].dropna().tail(10).to_dict() if 'BOLL_upper' in df.columns else {},
                    'Middle': df['BOLL_middle'].dropna().tail(10).to_dict() if 'BOLL_middle' in df.columns else {},
                    'Lower': df['BOLL_lower'].dropna().tail(10).to_dict() if 'BOLL_lower' in df.columns else {}
                }
            
            if "KDJ" in indicators:
                df = self._calculate_kdj(df)
                calculated_indicators['KDJ'] = {
                    'K': df['K'].dropna().tail(10).to_dict() if 'K' in df.columns else {},
                    'D': df['D'].dropna().tail(10).to_dict() if 'D' in df.columns else {},
                    'J': df['J'].dropna().tail(10).to_dict() if 'J' in df.columns else {}
                }
            
            # 生成技术分析摘要
            summary = self._generate_technical_summary(df, indicators)
            
            result = {
                'stock_code': code,
                'period': f"{start_date} 到 {end_date}",
                'calculated_indicators': list(indicators),
                'indicators_data': calculated_indicators,
                'technical_summary': summary,
                'latest_values': self._get_latest_values(df),
                'data_points': len(df)
            }

            logger.info(f"成功计算{code}的技术指标")
            return self._success_response(result)

        except Exception as e:
            error_message = traceback.format_exc()
            logger.error(f"计算A股技术指标失败: {str(e)}")
            logger.error(f"Error: {error_message}")
            return self._error_response(f"技术分析失败: {str(e)}")
    
    def _generate_technical_summary(self, df: pd.DataFrame, indicators: list) -> Dict[str, Any]:
        """生成技术分析摘要"""
        summary = {}
        
        if len(df) == 0:
            return summary
        
        latest_data = df.iloc[-1]
        
        # MA趋势分析
        if "MA" in indicators and all(col in df.columns for col in ['MA5', 'MA10', 'MA20']):
            ma5 = latest_data.get('MA5', 0)
            ma10 = latest_data.get('MA10', 0)
            ma20 = latest_data.get('MA20', 0)
            close = latest_data.get('close', 0)
            
            if close > ma5 > ma10 > ma20:
                summary['MA_trend'] = '多头排列，上涨趋势'
            elif close < ma5 < ma10 < ma20:
                summary['MA_trend'] = '空头排列，下跌趋势'
            else:
                summary['MA_trend'] = '趋势不明确'
        
        # RSI超买超卖分析
        if "RSI" in indicators and 'RSI' in df.columns:
            rsi = latest_data.get('RSI', 50)
            if rsi > 80:
                summary['RSI_signal'] = '超买区域，可能回调'
            elif rsi < 20:
                summary['RSI_signal'] = '超卖区域，可能反弹'
            else:
                summary['RSI_signal'] = '正常区域'
        
        # MACD信号分析
        if "MACD" in indicators and all(col in df.columns for col in ['MACD', 'MACD_signal']):
            macd = latest_data.get('MACD', 0)
            signal = latest_data.get('MACD_signal', 0)
            
            if macd > signal and macd > 0:
                summary['MACD_signal'] = '金叉向上，买入信号'
            elif macd < signal and macd < 0:
                summary['MACD_signal'] = '死叉向下，卖出信号'
            else:
                summary['MACD_signal'] = '观望'
        
        return summary
    
    def _get_latest_values(self, df: pd.DataFrame) -> Dict[str, Any]:
        """获取最新的技术指标数值"""
        if len(df) == 0:
            return {}
        
        latest = df.iloc[-1]
        latest_values = {}
        
        # 基本价格信息
        for col in ['close', 'volume']:
            if col in df.columns:
                latest_values[col] = float(latest[col]) if pd.notna(latest[col]) else None
        
        # 技术指标
        indicator_cols = [col for col in df.columns if col not in 
                         ['date', 'open', 'close', 'high', 'low', 'volume']]
        
        for col in indicator_cols:
            if col in df.columns:
                latest_values[col] = float(latest[col]) if pd.notna(latest[col]) else None
        
        return latest_values