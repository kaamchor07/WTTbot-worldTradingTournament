"""
Real-time Dashboard for Trading Signals
"""
import time
import os
from typing import List
from datetime import datetime

try:
    from rich.console import Console
    from rich.table import Table
    from rich.live import Live
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("⚠️  'rich' library not available. Install with: pip install rich")
    print("    Falling back to simple text display")

from scanner import TradingSignal


class Dashboard:
    """Real-time dashboard for displaying trading opportunities"""
    
    def __init__(self):
        if RICH_AVAILABLE:
            self.console = Console()
        self.use_rich = RICH_AVAILABLE
    
    def display_signals_rich(self, signals: List[TradingSignal], title: str = "🎯 TOP TRADING OPPORTUNITIES"):
        """Display signals using rich library"""
        table = Table(title=title, show_header=True, header_style="bold magenta")
        
        table.add_column("#", style="dim", width=3)
        table.add_column("Ticker", style="cyan bold", width=8)
        table.add_column("Signal", width=6)
        table.add_column("Score", justify="right", width=6)
        table.add_column("Entry", justify="right", width=12)
        table.add_column("SL Points", justify="right", width=10)
        table.add_column("TP Points", justify="right", width=10)
        table.add_column("R:R", justify="center", width=8)
        table.add_column("Timeframes", width=15)
        table.add_column("Reason", width=30)
        
        for i, signal in enumerate(signals, 1):
            # Color code the signal type
            if signal.signal_type == 'BUY':
                signal_color = "[green]BUY[/green]"
            elif signal.signal_type == 'SELL':
                signal_color = "[red]SELL[/red]"
            else:
                signal_color = "[yellow]WATCH[/yellow]"
            
            # Calculate points difference
            if signal.signal_type == 'BUY':
                sl_points = signal.entry_price - signal.stop_loss
                tp_points = signal.take_profit - signal.entry_price
            else:  # SELL
                sl_points = signal.stop_loss - signal.entry_price
                tp_points = signal.entry_price - signal.take_profit
            
            risk_reward = f"{abs(tp_points)/abs(sl_points):.1f}:1" if sl_points != 0 else "N/A"
            
            # Score color
            if signal.score >= 70:
                score_str = f"[bold green]{signal.score:.0f}[/bold green]"
            elif signal.score >= 50:
                score_str = f"[yellow]{signal.score:.0f}[/yellow]"
            else:
                score_str = f"[dim]{signal.score:.0f}[/dim]"
            
            # Compact reason
            reason_short = ", ".join(signal.reason[:2])
            if len(signal.reason) > 2:
                reason_short += f" +{len(signal.reason)-2}"
            
            table.add_row(
                str(i),
                signal.ticker,
                signal_color,
                score_str,
                f"{signal.entry_price:.4f}",
                f"{sl_points:.4f}",
                f"{tp_points:.4f}",
                risk_reward,
                signal.timeframe_alignment,
                reason_short
            )
        
        self.console.print(table)
        self.console.print("\n[dim]💡 SL/TP Points = Enter these values directly in your platform's point fields[/dim]\n")
    
    def display_signals_simple(self, signals: List[TradingSignal], title: str = "TOP TRADING OPPORTUNITIES"):
        """Display signals using simple text (fallback)"""
        print(f"\n{'='*120}")
        print(f"{title:^120}")
        print(f"{'='*120}")
        print(f"{'#':<3} {'Ticker':<8} {'Signal':<6} {'Score':<6} {'Entry':<12} {'SL Points':<10} {'TP Points':<10} {'R:R':<8} {'Timeframes':<15}")
        print(f"{'-'*120}")
        
        for i, signal in enumerate(signals, 1):
            # Calculate points difference
            if signal.signal_type == 'BUY':
                sl_points = signal.entry_price - signal.stop_loss
                tp_points = signal.take_profit - signal.entry_price
            else:  # SELL
                sl_points = signal.stop_loss - signal.entry_price
                tp_points = signal.entry_price - signal.take_profit
            
            risk_reward = f"{abs(tp_points)/abs(sl_points):.1f}:1" if sl_points != 0 else "N/A"
            
            # Format points with appropriate decimals based on size
            if signal.entry_price > 100:
                sl_pts_str = f"{sl_points:.1f}"
                tp_pts_str = f"{tp_points:.1f}"
            else:
                sl_pts_str = f"{sl_points:.4f}"
                tp_pts_str = f"{tp_points:.4f}"
            
            print(f"{i:<3} {signal.ticker:<8} {signal.signal_type:<6} {signal.score:<6.0f} "
                  f"{signal.entry_price:<12.4f} {sl_pts_str:<10} {tp_pts_str:<10} {risk_reward:<8} "
                  f"{signal.timeframe_alignment:<15}")
        
        print(f"{'='*120}")
        print(f"NOTE: SL Points = Stop-Loss distance in points, TP Points = Take-Profit distance in points")
        print(f"      Enter these point values directly in your platform's SL/TP fields")
        print(f"{'='*120}\n")
    
    def display_signals(self, signals: List[TradingSignal], title: str = None):
        """Display signals (auto-detect rich/simple)"""
        if not title:
            title = f"🎯 TOP TRADING OPPORTUNITIES - {datetime.now().strftime('%H:%M:%S')}"
        
        if self.use_rich:
            self.display_signals_rich(signals, title)
        else:
            self.display_signals_simple(signals, title)
    
    def display_summary(self, signals: List[TradingSignal]):
        """Display summary statistics"""
        if not signals:
            print("No signals to display")
            return
        
        buy_signals = [s for s in signals if s.signal_type == 'BUY']
        sell_signals = [s for s in signals if s.signal_type == 'SELL']
        avg_score = sum(s.score for s in signals) / len(signals)
        
        if self.use_rich:
            summary = f"""
[bold]Summary:[/bold]
  • Total Signals: {len(signals)}
  • Buy Signals: [green]{len(buy_signals)}[/green]
  • Sell Signals: [red]{len(sell_signals)}[/red]
  • Average Score: {avg_score:.1f}
  • Top Score: {signals[0].score:.1f} ({signals[0].ticker})
            """
            self.console.print(Panel(summary, title="📊 Scan Summary", border_style="blue"))
        else:
            print(f"\n{'='*60}")
            print(f"SUMMARY")
            print(f"{'='*60}")
            print(f"Total Signals: {len(signals)}")
            print(f"Buy Signals: {len(buy_signals)}")
            print(f"Sell Signals: {len(sell_signals)}")
            print(f"Average Score: {avg_score:.1f}")
            print(f"Top Score: {signals[0].score:.1f} ({signals[0].ticker})")
            print(f"{'='*60}\n")
    
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('clear' if os.name != 'nt' else 'cls')


if __name__ == "__main__":
    from scanner import TradingSignal
    
    # Create sample signals for testing
    print("Testing Dashboard with sample signals...")
    
    sample_signals = [
        TradingSignal(
            symbol_id="123",
            ticker="BTCUSD",
            signal_type="BUY",
            score=85.5,
            entry_price=95000.0,
            stop_loss=94000.0,
            take_profit=98000.0,
            timeframe_alignment="5m↑ 15m↑ 1h↑",
            reason=["1h uptrend", "15m uptrend", "Strong momentum (75)", "High volume (2.3x)"],
            timestamp="2024-01-25 10:00:00"
        ),
        TradingSignal(
            symbol_id="456",
            ticker="ETHUSD",
            signal_type="SELL",
            score=72.3,
            entry_price=3500.0,
            stop_loss=3550.0,
            take_profit=3350.0,
            timeframe_alignment="5m↓ 15m↓ 1h→",
            reason=["15m downtrend", "RSI overbought (78)", "High volume (1.8x)"],
            timestamp="2024-01-25 10:00:00"
        ),
        TradingSignal(
            symbol_id="789",
            ticker="XAUUSD",
            signal_type="BUY",
            score=68.0,
            entry_price=2050.0,
            stop_loss=2040.0,
            take_profit=2075.0,
            timeframe_alignment="5m↑ 15m→ 1h↑",
            reason=["1h uptrend", "RSI oversold (28)"],
            timestamp="2024-01-25 10:00:00"
        ),
    ]
    
    dashboard = Dashboard()
    dashboard.display_signals(sample_signals)
    dashboard.display_summary(sample_signals)
    
    print("\n✓ Dashboard test complete!")
