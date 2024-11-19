import numpy as np
from numba import njit, uint64
from numba.typed import Dict
from hftbacktest import BUY, SELL, GTX, LIMIT
from datetime import datetime, timezone

# 用于记录交易日志的全局变量
trade_logs = []

@njit
def log_trade(timestamp, action, price, size):
    """记录交易日志(numba兼容)"""
    # 在numba函数中,我们只能返回数值
    # 我们将返回一个代码来表示不同的交易动作
    # 1: 做多开仓, 2: 做空开仓, 3: 多仓止损, 4: 多仓止盈, 5: 空仓止损, 6: 空仓止盈
    return timestamp, action, price, size

@njit
def aggressive_trend_following(hbt, recorder):
    """激进的趋势追踪策略"""
    asset_no = 0
    tick_size = hbt.depth(asset_no).tick_size
    lot_size = hbt.depth(asset_no).lot_size
    
    # 策略参数
    lookback = 5  # 短周期趋势
    leverage = 5  # 5倍杠杆
    stop_loss = 0.02  # 2%止损
    take_profit = 0.05  # 5%止盈
    
    # 资金管理
    initial_capital = 1000  # 初始资金
    risk_per_trade = 0.3  # 每次用30%资金
    
    # 价格历史
    prices = np.zeros(lookback)
    idx = 0
    
    # 交易状态
    position = 0.0
    entry_price = 0.0
    last_order_id = -1
    
    while hbt.elapse(10_000_000) == 0:  # 10ms
        # 清理失效订单
        hbt.clear_inactive_orders(asset_no)
        
        # 获取市场数据
        depth = hbt.depth(asset_no)
        if depth.best_bid <= 0 or depth.best_ask <= 0:
            continue
            
        mid_price = (depth.best_bid + depth.best_ask) / 2.0
        
        # 更新价格序列
        prices[idx] = mid_price
        idx = (idx + 1) % lookback
        
        if idx < lookback-1:
            continue
            
        # 计算趋势
        price_change = (prices[-1] - prices[0]) / prices[0]
        
        # 获取当前持仓
        position = hbt.position(asset_no)
        
        # 处理时间
        if hbt.elapse(1_000_000) != 0:  # 1ms处理时间
            break
            
        # 没有持仓时寻找入场机会
        if position == 0:
            # 强势上涨趋势
            if price_change > 0.01:  # 1%的短期涨幅
                pos_size = (initial_capital * risk_per_trade * leverage) / mid_price
                pos_size = round(pos_size / lot_size) * lot_size  # 调整为lot_size的整数倍
                
                # 使用当前价格下单
                order_id = int(depth.best_ask / tick_size)
                if hbt.submit_buy_order(asset_no, order_id, depth.best_ask, pos_size, GTX, LIMIT, False):
                    entry_price = depth.best_ask
                    last_order_id = order_id
                    recorder.record(hbt)
                    
            # 强势下跌趋势
            elif price_change < -0.01:
                pos_size = (initial_capital * risk_per_trade * leverage) / mid_price
                pos_size = round(pos_size / lot_size) * lot_size  # 调整为lot_size的整数倍
                
                # 使用当前价格下单
                order_id = int(depth.best_bid / tick_size)
                if hbt.submit_sell_order(asset_no, order_id, depth.best_bid, pos_size, GTX, LIMIT, False):
                    entry_price = depth.best_bid
                    last_order_id = order_id
                    recorder.record(hbt)
                    
        # 持仓状态检查止盈止损
        else:
            pnl = (mid_price - entry_price) / entry_price if position > 0 else (entry_price - mid_price) / entry_price
            
            # 多仓
            if position > 0:
                # 止损
                if pnl < -stop_loss:
                    order_id = int(depth.best_bid / tick_size)
                    if hbt.submit_sell_order(asset_no, order_id, depth.best_bid, abs(position), GTX, LIMIT, False):
                        last_order_id = order_id
                        recorder.record(hbt)
                # 止盈
                elif pnl > take_profit:
                    order_id = int(depth.best_bid / tick_size)
                    if hbt.submit_sell_order(asset_no, order_id, depth.best_bid, abs(position), GTX, LIMIT, False):
                        last_order_id = order_id
                        recorder.record(hbt)
                        
            # 空仓
            else:
                # 止损
                if pnl < -stop_loss:
                    order_id = int(depth.best_ask / tick_size)
                    if hbt.submit_buy_order(asset_no, order_id, depth.best_ask, abs(position), GTX, LIMIT, False):
                        last_order_id = order_id
                        recorder.record(hbt)
                # 止盈
                elif pnl > take_profit:
                    order_id = int(depth.best_ask / tick_size)
                    if hbt.submit_buy_order(asset_no, order_id, depth.best_ask, abs(position), GTX, LIMIT, False):
                        last_order_id = order_id
                        recorder.record(hbt)
        
        # 等待订单响应
        if last_order_id >= 0:
            if not hbt.wait_order_response(asset_no, last_order_id, 5_000_000_000):  # 5秒超时
                break
            last_order_id = -1
        
        # 记录状态
        recorder.record(hbt)
    
    return True

def print_trade_log(timestamp, action, price, size):
    """打印交易日志"""
    action_map = {
        1: "做多开仓",
        2: "做空开仓", 
        3: "多仓止损",
        4: "多仓止盈",
        5: "空仓止损",
        6: "空仓止盈"
    }
    action_str = action_map.get(action, "未知动作")
    time_str = datetime.fromtimestamp(timestamp/1e9, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f')
    print(f"[{time_str}] {action_str}: 价格={price:.2f} 数量={size:.4f}")