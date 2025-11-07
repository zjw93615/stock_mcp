"""
中文股票MCP工具基类
提供MCP工具的基础结构和通用功能，针对中文股票市场优化
"""

import json
from typing import Any, Dict, List
from logger import get_logger

# 获取日志记录器
logger = get_logger()

class ZHMCPBaseTool:
    """中文股票MCP工具基类"""
    
    def __init__(self, name: str, description: str, input_schema: Dict[str, Any]):
        self.name = name
        self.description = description
        self.input_schema = input_schema
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """执行工具，子类必须实现此方法"""
        raise NotImplementedError("子类必须实现execute方法")
    
    def _success_response(self, data: Any) -> Dict[str, Any]:
        """创建成功响应"""
        try:
            # 确保数据可以JSON序列化
            return self._json_serializable(data)
        except Exception as e:
            logger.error(f"处理响应数据失败: {str(e)}")
            return {"error": f"数据处理失败: {str(e)}"}
    
    def _error_response(self, error_msg: str) -> Dict[str, Any]:
        """创建错误响应"""
        return {"error": error_msg}
    
    def _json_serializable(self, obj):
        """处理JSON序列化问题"""
        import pandas as pd
        import numpy as np
        from datetime import datetime, date
        
        if isinstance(obj, dict):
            return {str(k): self._json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._json_serializable(i) for i in obj]
        elif isinstance(obj, (pd.Timestamp, datetime, date)):
            return str(obj)
        elif isinstance(obj, (np.int64, np.int32, np.int16)):
            return int(obj)
        elif isinstance(obj, (np.float64, np.float32)):
            return float(obj)
        elif pd.isna(obj) or obj is None:
            return None
        else:
            return obj
    
    def _normalize_stock_code(self, code: str) -> str:
        """标准化股票代码格式
        
        Args:
            code: 股票代码，支持多种格式如：000001, 000001.SZ, 600000.SH等
            
        Returns:
            标准化后的股票代码
        """
        # 移除空格并转换为大写
        code = code.strip().upper()
        
        # 如果已经包含交易所后缀，直接返回
        if '.' in code:
            return code
            
        # 根据股票代码规律添加交易所后缀
        if code.startswith(('000', '001', '002', '003', '300')):
            # 深交所
            return f"{code}.SZ"
        elif code.startswith(('600', '601', '603', '605', '688')):
            # 上交所
            return f"{code}.SH"
        elif code.startswith(('430', '831', '832', '833', '834', '835', '836', '837', '838', '839')):
            # 北交所
            return f"{code}.BJ"
        else:
            # 默认返回原始代码
            logger.warning(f"无法识别股票代码格式: {code}")
            return code
    
    def _get_market_from_code(self, code: str) -> str:
        """根据股票代码获取市场类型
        
        Args:
            code: 股票代码
            
        Returns:
            市场类型：sz(深交所), sh(上交所), bj(北交所)
        """
        normalized_code = self._normalize_stock_code(code)
        
        if normalized_code.endswith('.SZ'):
            return 'sz'
        elif normalized_code.endswith('.SH'):
            return 'sh'
        elif normalized_code.endswith('.BJ'):
            return 'bj'
        else:
            # 默认判断
            code_num = code[:3]
            if code_num in ['000', '001', '002', '003', '300']:
                return 'sz'
            elif code_num in ['600', '601', '603', '605', '688']:
                return 'sh'
            else:
                return 'sz'  # 默认深交所