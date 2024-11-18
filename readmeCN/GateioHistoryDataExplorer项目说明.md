# Gate.io历史数据说明文档

> 本文档面向高频交易策略开发人员，介绍如何使用GateioHistoryDataExplorer项目存储的历史数据。


## 0. 数据范围说明

项目支持两种类型的历史数据，它们的覆盖范围如下：

| 数据类型                  | 支持的交易对 |
|-----------------------|------------|
| trades (成交记录)          | 所有USDT本位永续合约 |
| orderbook_snapshot (订单簿快照) | 仅BTC_USDT、ETH_USDT |



## 1. 数据库连接信息

```python
import psycopg2
from datetime import datetime, timezone

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'trading',
    'user': 'admin',
    'password': 'qwer80661059'
}

# 连接示例
def get_connection():
    return psycopg2.connect(**DB_CONFIG)

# 使用示例
with get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT * FROM orderbook_snapshot 
            WHERE symbol = 'BTC_USDT' 
            LIMIT 1;
        """)
        print(cur.fetchone())
```

## 2. 数据表结构

### 2.1 orderbook_snapshot (订单簿快照)
每秒记录一次完整的订单簿状态，包含买卖双方各10档深度数据。

```sql
CREATE TABLE orderbook_snapshot (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    symbol VARCHAR(20) NOT NULL,                -- 交易对
    record_timestamp TIMESTAMPTZ NOT NULL,      -- 数据记录时间
    orderbook_timestamp TIMESTAMPTZ NOT NULL,   -- 订单簿更新时间
    orderbook_id BIGINT NOT NULL,              -- 订单簿ID
    asks_raw JSONB NOT NULL,                   -- 原始卖单数据 [{s:数量,p:价格}]
    bids_raw JSONB NOT NULL,                   -- 原始买单数据 [{s:数量,p:价格}]
    
    CONSTRAINT pk_orderbook_id PRIMARY KEY (id, record_timestamp),
    CONSTRAINT uq_orderbook_snapshot UNIQUE (symbol, record_timestamp, orderbook_id)
);

-- 索引
CREATE INDEX idx_orderbook_symbol_time 
ON orderbook_snapshot(symbol, record_timestamp DESC);
```

**数据格式说明:**
- asks_raw/bids_raw: JSONB数组，每个元素包含:
  - s: size(数量)
  - p: price(价格)
- 深度数据按价格排序:
  - asks_raw: 价格从低到高
  - bids_raw: 价格从高到低
- 每个时间点固定10档深度

### 2.2 trades (成交记录)
记录每笔实际成交的信息。

```sql
CREATE TABLE trades (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    symbol VARCHAR(20) NOT NULL,                -- 交易对
    trade_timestamp TIMESTAMPTZ NOT NULL,       -- 成交时间
    trade_id VARCHAR(50) NOT NULL,             -- 成交ID
    price DECIMAL NOT NULL,                    -- 成交价格
    size DECIMAL NOT NULL,                     -- 成交数量(正:做多,负:做空)
    
    CONSTRAINT pk_trades_id PRIMARY KEY (id, trade_timestamp),
    CONSTRAINT uq_trades_id UNIQUE (symbol, trade_id, trade_timestamp)
);

-- 索引
CREATE INDEX idx_trades_time_symbol ON trades(trade_timestamp DESC, symbol);
CREATE INDEX idx_trades_price ON trades(price);
CREATE INDEX idx_trades_size ON trades(size);
```

**数据说明:**
- trade_timestamp: 精确到微秒
- size: 正数表示做多，负数表示做空
- price: 成交价格
- trade_id: 成交ID，全局唯一

## 3. 数据特点

### 3.1 OrderBookSlice
- 每秒一条记录
- 买卖盘各10档深度
- 精确到毫秒级
- 包含完整的价格和数量信息
- 适合分析市场深度、流动性和价格压力

### 3.2 Trades
- 每笔成交一条记录
- 精确到微秒级
- 包含方向信息(size正负)
- 成交量大小不等
- 适合分析成交趋势、大单行为

## 4. 注意事项

1. **时区处理**
   - 数据库中所有时间均为UTC时间
   - 查询时注意时区转换
   - 建议统一使用UTC时间

2. **性能优化**
   - 使用时间范围过滤
   - 合理使用索引
   - 避免过大的结果集
   - 考虑使用连接池

3. **数据质量**
   - 可能存在数据空缺
   - 注意处理异常值
   - 验证数据连续性

## 5. 联系方式

如有数据相关问题，请联系数据库管理员或参考原项目文档：
[GateioHistoryDataExplorer](https://github.com/bijingrui1997/GateioHistoryDataExplorer)