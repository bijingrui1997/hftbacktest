import pandas as pd
import numpy as np
from datetime import datetime, timezone
import psycopg2
import os

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'trading',
    'user': 'admin',
    'password': 'qwer80661059'
}

def load_and_save_market_data(symbol, start_time, end_time, output_file):
    """从PostgreSQL加载市场数据并保存为npz格式"""
    
    # 检查文件是否已存在
    if os.path.exists(output_file):
        print(f"发现已存在的数据文件: {output_file}")
        print("直接使用已有数据文件...")
        return output_file
        
    print(f"开始加载{symbol}从{start_time}到{end_time}的市场数据...")
    
    # [数据加载和转换的代码保持不变...]
    
    return output_file 