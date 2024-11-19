from datetime import datetime, timezone
from hftbacktest import BacktestAsset, HashMapMarketDepthBacktest, Recorder
from data_processor import load_and_save_market_data
from strategy import aggressive_trend_following
import numpy as np

def run_backtest():
    """运行回测"""
    symbol = 'BTC_USDT'
    start_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
    end_time = datetime(2024, 1, 2, tzinfo=timezone.utc)
    
    try:
        # 加载数据
        data_file = load_and_save_market_data(symbol, start_time, end_time, 'market_data.npz')
        
        # 配置回测参数
        tick_size = 0.1
        lot_size = 0.001
        
        # 创建回测实例
        asset = (
            BacktestAsset()
            .data([data_file])
            .linear_asset(1.0)
            .power_prob_queue_model(2.0)
            .no_partial_fill_exchange()
            .trading_value_fee_model(-0.00005, 0.0007)
            .tick_size(tick_size)
            .lot_size(lot_size)
        )
        
        hbt = HashMapMarketDepthBacktest([asset])
        
        # 创建记录器,增加缓冲区大小
        recorder = Recorder(1, 10_000_000)  # 增加缓冲区到1000万
        
        # 运行回测
        print("\n=== 开始回测 ===")
        success = aggressive_trend_following(hbt, recorder.recorder)
        
        if success:
            # 计算统计数据
            from hftbacktest.stats import LinearAssetRecord
            stats = LinearAssetRecord(recorder.get(0)).stats()
            summary = stats.summary()
            
            # 输出结果
            print("\n=== 回测结果 ===")
            print(summary)
        
        hbt.close()
        return success
        
    except Exception as e:
        print(f"\n回测过程中发生错误: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    try:
        result = run_backtest()
        print(f"\n回测完成: {'成功' if result else '失败'}")
    except Exception as e:
        print(f"\n回测发生错误: {str(e)}") 