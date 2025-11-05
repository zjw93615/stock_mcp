"""
MCP工具基类
提供MCP工具的基础结构和通用功能
"""

import json
from typing import Any, Dict, List
from logger import get_logger

# 获取日志记录器
logger = get_logger()

class MCPBaseTool:
    """MCP工具基类"""
    
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
        
        if isinstance(obj, dict):
            return {str(k): self._json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._json_serializable(i) for i in obj]
        elif isinstance(obj, pd.Timestamp):
            return str(obj)
        elif pd.isna(obj):
            return None
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj