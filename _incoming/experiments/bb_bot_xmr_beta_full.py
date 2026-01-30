import backtrader as bt


class BB_BOT_XMR_BETA(bt.Strategy):
    """
    Bollinger Bands and Average Directional Movement Index (ADX) Strategy

    A Bollinger Bands (BB) strategy is a popular technical analysis method used by traders to
    identify potential entry and exit points in the market.

    The Average Directional Index (ADX) is a technical indicator used to measure the strength
    of a trend. By incorporating ADX into our Bollinger Bands strategy, we can filter out
    trades during weak or non-trending market conditions.

    Buy Signal (Long Position)

        Condition 1: Price crosses below the lower Bollinger Band.
        Condition 2: A confirmation candle closes above the lower Bollinger Band after the cross.
        Condition 3: ADX is above a certain threshold (e.g., 25), indicating a strong trend.

    Sell Signal (Short Position)

        Condition 1: Price crosses above the upper Bollinger Band.
        Condition 2: A confirmation candle closes below the upper Bollinger Band after the cross.
        Condition 3: ADX is above a certain threshold (e.g., 25), indicating a strong trend.

    Exit Strategy

        Take Profit: Exit the trade when the price reaches the middle Bollinger Band or shows signs of reversal.
        Stop Loss: Set a stop loss just below the recent swing low for a long position and just above the recent swing high for a short position.

    Example Rules Implementation with ADX

        Buy Signal:
            If the closing price of the current candle is less than the lower Bollinger Band, then wait for the next candle.
            If the next candle closes above the lower Bollinger Band and ADX is above 25, enter a long position.

        Sell Signal:
            If the closing price of the current candle is greater than the upper Bollinger Band, then wait for the next candle.
            If the next candle closes below the upper Bollinger Band and ADX is above 25, enter a short position.

        Exit Long Position:
            If the price reaches the middle Bollinger Band or set a predefined profit target.
            Use a stop loss just below the recent swing low.

        Exit Short Position:
            If the price reaches the middle Bollinger Band or set a predefined profit target.
            Use a stop loss just above the recent swing high.
    """

    params = {
        "bb_period": 24,  # Bollinger Bands period
        "bb_dev": 1.7,  # Bollinger Bands standard deviation
        "adx_period": 14,  # ADX period
        "adx_threshold": 25,  # ADX threshold for strong trend
        "swing_lookback": 8,  # Look back period for recent swing high/low
        "take_profit": 0.2414,  # Take profit as a percentage of entry price
        "sizer": "FixedLotSizer",  # Sizers docs: https://tradelocker.com/how-to/use-a-bot-sizer/
        "sizer_lots": 0.01,
        "sizer_cash": 100,
        "sizer_assigned_margin_percent": 1.0,
    }

    def __init__(self):
        # Bollinger Bands
        self.bb = bt.indicators.BollingerBands(
            period=self.params.bb_period, devfactor=self.params.bb_dev
        )
        # ADX
        self.adx = bt.indicators.AverageDirectionalMovementIndex(period=self.params.adx_period)
        # Bottom BB Line Cross Over
        self.cross_bot = bt.indicators.CrossOver(self.data.close, self.bb.lines.bot)
        # Top BB Line Cross Over
        self.cross_top = bt.indicators.CrossOver(self.data.close, self.bb.lines.top)

        self.order = None  # To keep track of pending orders
        self.stop_loss_order = None
        self.take_profit_order = None
        self.stop_loss_price = None
        self.take_profit_price = None
        self.lastlen = -1

    def next(self) -> None:
        if (
            hasattr(self.data, "isdelayed") and self.data.isdelayed()
        ):  # prevents from live trading on delayed data
            return
        if self.lastlen == len(self.data):
            return
        self.lastlen = len(self.data)
        if self.order:
            return

        buy_signal = False
        sell_signal = False
        exit_signal = False
        buy_stop_loss_price = None
        buy_take_profit_price = None
        sell_stop_loss_price = None
        sell_take_profit_price = None

        # buy signal
        if (
            # bb cross and close below bottom bb line
            (self.cross_bot[0] < 0 and self.data[0] < self.bb.bot[0])
            # bb cross on previous candle and current close below bottom bb line
            or (self.cross_bot[-1] < 0 and self.data[0] < self.bb.bot[0])
        ):
            # adx filter
            if self.adx[0] > self.params.adx_threshold:
                buy_signal = True
                buy_stop_loss_price = min(self.data.low.get(size=self.params.swing_lookback))
                buy_take_profit_price = self.data.close[0] * (1.0 + self.params.take_profit)

        # sell signal
        if (
            # bb cross and close above top bb line
            (self.cross_top[0] > 0 and self.data[0] > self.bb.top[0])
            # bb cross on previous candle and current close above top bb line
            or (self.cross_top[-1] > 0 and self.data[0] > self.bb.top[0])
        ):
            # adx filter
            if self.adx[0] > self.params.adx_threshold:
                sell_signal = True
                sell_stop_loss_price = max(self.data.high.get(size=self.params.swing_lookback))
                sell_take_profit_price = self.data.close[0] * (1.0 - self.params.take_profit)

        # exit signal
        position = self.getposition()
        if position.size > 0:  # Long position
            if self.data.close[0] > self.bb.mid[0] and self.data.close[-1] > self.bb.mid[-1]:
                exit_signal = True
        elif position.size < 0:  # Short position
            if self.data.close[0] < self.bb.mid[0] and self.data.close[-1] < self.bb.mid[-1]:
                exit_signal = True

        if not position.size:
            # check for entry
            if buy_signal:
                self.stop_loss_price = buy_stop_loss_price
                self.take_profit_price = buy_take_profit_price
                (
                    self.order,
                    self.stop_loss_order,
                    self.take_profit_order,
                ) = self.buy_bracket(
                    exectype=bt.Order.Market,
                    limitprice=self.take_profit_price,
                    stopprice=self.stop_loss_price,
                )
            elif sell_signal:
                self.stop_loss_price = sell_stop_loss_price
                self.take_profit_price = sell_take_profit_price
                (
                    self.order,
                    self.stop_loss_order,
                    self.take_profit_order,
                ) = self.sell_bracket(
                    exectype=bt.Order.Market,
                    limitprice=self.take_profit_price,
                    stopprice=self.stop_loss_price,
                )
        else:
            # check for exit
            if exit_signal:
                self.order = self.close()

    def notify_order(self, order: bt.Order) -> None:
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [
            order.Completed,
            order.Canceled,
            order.Margin,
            order.Rejected,
        ]:
            self.order = None

    def notify_trade(self, trade: bt.Trade) -> None:
        if not trade.isclosed:
            return
        self.log(f"OPERATION PROFIT, GROSS {trade.pnl}, NET {trade.pnlcomm}")

    # Define a helper function to include date/time in logs
    def log(self, txt: str) -> None:
        dt = self.data.datetime.date(0)
        t = self.data.datetime.time(0)
        print(f"{dt} {t} {txt}")

    # ------------------------------------------------------------------------------------
    # params_metadata is optional -- it is used to configure the "Run Backtest/Bot" modal.
    params_metadata = {
        "bb_period": {
            "label": "Bollinger Bands Period",
            "helper_text": "Number of periods for the Simple Moving Average calculation of the Bollinger Bands",
            "value_type": "int",
        },
        "bb_dev": {
            "label": "Bollinger Bands Deviation",
            "helper_text": "Multiplier for standard deviation to set band width",
            "value_type": "float",
        },
        "adx_period": {
            "label": "Average Directional Index Period",
            "helper_text": "Number of periods for the ADX calculation",
            "value_type": "int",
        },
        "adx_threshold": {
            "label": "Average Directional Index Threshold",
            "helper_text": "Minimum ADX value required to confirm a strong trend before entering trades.",
            "value_type": "float",
        },
        "swing_lookback": {
            "label": "Swing Lookback Period",
            "helper_text": "Number of periods to look back for identifying swing highs and lows",
            "value_type": "int",
        },
        "take_profit": {
            "label": "Take Profit",
            "helper_text": "Percentage gain target for closing profitable trades",
            "value_type": "float",
        },
        "sizer": {
            "label": "Sizer",
            "helper_text": "All trades will be done according to the selected sizer",
            "value_type": "str",
            "enum_values": ["FixedLotSizer", "FixedCashSizer", "AssignedMarginPercentSizer"],
        },
        "sizer_assigned_margin_percent": {
            "label": "Sizer assigned margin percent",
            "helper_text": "Percentage of assigned bot margin used for each trade (between 0 and 100)",
            "value_type": "float",
            "display_if_param_has_value": {"sizer": ["AssignedMarginPercentSizer"]},
        },
        "sizer_lots": {
            "label": "Sizer lots",
            "helper_text": "Amount of lots used for each trade",
            "value_type": "float",
            "display_if_param_has_value": {"sizer": ["FixedLotSizer"]},
        },
        "sizer_cash": {
            "label": "Sizer cash",
            "helper_text": "Amount of cash used for each trade",
            "value_type": "float",
            "display_if_param_has_value": {"sizer": ["FixedCashSizer"]},
        },
    }

