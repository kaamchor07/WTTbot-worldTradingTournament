"""
Main Trading Competition Bot
"""
import time
import argparse
from datetime import datetime
from scanner import MultiTimeframeScanner
from dashboard import Dashboard
from config import STRATEGY_CONFIG, load_symbols


def main():
    parser = argparse.ArgumentParser(description='Trading Competition Scanner')
    parser.add_argument('--test', action='store_true', help='Test mode with only 10 symbols')
    parser.add_argument('--once', action='store_true', help='Run once and exit (no continuous loop)')
    parser.add_argument('--interval', type=int, default=60, help='Scan interval in seconds (default: 60)')
    parser.add_argument('--top', type=int, default=20, help='Number of top signals to display (default: 20)')
    args = parser.parse_args()
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║          🏆  TRADING COMPETITION SCANNER  🏆                 ║
║                                                              ║
║        Multi-Timeframe Analysis & Signal Generation         ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    print(f"⚙️  Configuration:")
    print(f"   • Scan Timeframe: {STRATEGY_CONFIG['scan_timeframe']}")
    print(f"   • Confirm Timeframe: {STRATEGY_CONFIG['confirm_timeframe']}")
    print(f"   • Trend Timeframe: {STRATEGY_CONFIG['trend_timeframe']}")
    print(f"   • Top N Signals: {args.top}")
    print(f"   • Scan Interval: {args.interval}s")
    print(f"   • Test Mode: {'Yes (10 symbols)' if args.test else 'No (ALL symbols)'}")
    print()
    
    # Load symbols
    symbols = load_symbols()
    print(f"📊 Loaded {len(symbols)} symbols")
    
    # Initialize scanner and dashboard
    scanner = MultiTimeframeScanner()
    dashboard = Dashboard()
    
    scan_count = 0
    
    while True:
        scan_count += 1
        
        try:
            print(f"\n{'='*80}")
            print(f"🔄 Scan #{scan_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*80}\n")
            
            # Run the scan
            if args.test:
                signals = scanner.scan_all(max_symbols=10)
            else:
                signals = scanner.scan_all()
            
            # Display top signals
            top_signals = signals[:args.top]
            
            if top_signals:
                dashboard.clear_screen()
                dashboard.display_signals(top_signals)
                dashboard.display_summary(signals)
                
                # Save to file in logs folder
                import os
                os.makedirs('logs', exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"logs/signals_{timestamp}.txt"
                
                with open(filename, 'w') as f:
                    f.write(f"Trading Signals - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"{'='*100}\n\n")
                    
                    for i, signal in enumerate(top_signals, 1):
                        f.write(f"{i}. {signal.ticker} - {signal.signal_type} (Score: {signal.score:.1f})\n")
                        f.write(f"   Entry: {signal.entry_price:.4f}\n")
                        f.write(f"   Stop Loss: {signal.stop_loss:.4f}\n")
                        f.write(f"   Take Profit: {signal.take_profit:.4f}\n")
                        f.write(f"   Timeframes: {signal.timeframe_alignment}\n")
                        f.write(f"   Reasons: {', '.join(signal.reason)}\n\n")
                
                print(f"\n💾 Signals saved to: {filename}")
            else:
                print("\n⚠️  No signals found in this scan")
            
            # Exit if running once
            if args.once:
                print("\n✓ Single scan complete. Exiting.")
                break
            
            # Wait for next scan
            print(f"\n⏳ Next scan in {args.interval} seconds... (Press Ctrl+C to stop)")
            time.sleep(args.interval)
            
        except KeyboardInterrupt:
            print("\n\n👋 Scanner stopped by user")
            break
        except Exception as e:
            print(f"\n❌ Error during scan: {e}")
            import traceback
            traceback.print_exc()
            
            if args.once:
                break
            
            print(f"\n⏳ Retrying in {args.interval} seconds...")
            time.sleep(args.interval)
    
    print("\n" + "="*80)
    print(f"📊 Total scans completed: {scan_count}")
    print("="*80)
    print("\n✓ Trading Competition Scanner finished\n")


if __name__ == "__main__":
    main()
