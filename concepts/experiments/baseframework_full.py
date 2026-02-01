"""
BaseFrameworkStrategy
Crash-test bot used to validate BAWSBetaBotZ repo structure.

This is NOT a real trading edge. It’s just a clean template
the other bots can copy from and extend.
"""

import backtrader as bt  # swap to TradeLocker SDK later if needed


class BaseFrameworkStrategy(bt.Strategy):
    params = dict(
        risk_per_trade=0.01,
        max_positions=1,
        enable_logging=True,
    )

    def __init__(self):
        self.order = None
        self.position_size = 0

        if self.p.enable_logging:
            print("[BaseFramework] init complete")

    def log(self, msg: str) -> None:
        if self.p.enable_logging:
            print(f"[BaseFramework] {msg}")

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status == order.Completed:
            side = "BUY" if order.isbuy() else "SELL"
            self.log(
                f"ORDER {side} EXECUTED @ {order.executed.price}, "
                f"SIZE={order.executed.size}"
            )

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f"ORDER problem: status={order.getstatusname()}")

        self.order = None

    def next(self):
        # placeholder logic: no real entries yet
        self.log(f"next() bar: close={self.data.close[0]}")
