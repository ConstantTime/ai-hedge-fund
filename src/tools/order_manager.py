#!/usr/bin/env python
"""
OrderManager: manage orders and PnL tracking via Zerodha KiteConnect.
"""
import os
from kiteconnect import KiteConnect
from loguru import logger
import pandas as pd

class OrderManager:
    def __init__(self):
        api_key = os.environ.get("ZERODHA_API_KEY")
        access_token = os.environ.get("ZERODHA_ACCESS_TOKEN")
        if not api_key or not access_token:
            logger.error("OrderManager: Missing Zerodha credentials")
            self.kite = None
        else:
            try:
                self.kite = KiteConnect(api_key=api_key)
                self.kite.set_access_token(access_token)
                logger.info("OrderManager: KiteConnect initialized successfully")
            except Exception as e:
                logger.error(f"OrderManager: Failed to init KiteConnect: {e}")
                self.kite = None

    def place_order(self, **kwargs) -> dict:
        """Place an order via KiteConnect. Pass in order params like:
        {"tradingsymbol":..., "exchange":..., "transaction_type":..., "quantity":..., "order_type":..., ...}
        """
        if not self.kite:
            raise Exception("OrderManager: Kite client not initialized")
        try:
            order_id = self.kite.place_order(**kwargs)
            logger.info(f"Order placed: {order_id}")
            return {"order_id": order_id}
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            raise

    def get_positions(self) -> pd.DataFrame:
        """Fetch current positions and return a DataFrame."""
        if not self.kite:
            return pd.DataFrame()
        try:
            pos = self.kite.positions()
            # pos['net'] contains list of positions
            data = []
            for p in pos.get('net', []):
                data.append({
                    'tradingsymbol': p['tradingsymbol'],
                    'quantity': p['quantity'],
                    'average_price': p['average_price'],
                    'pnl': p['pnl']
                })
            return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Failed to fetch positions: {e}")
            return pd.DataFrame()

    def get_orders(self) -> pd.DataFrame:
        """Fetch order history and return a DataFrame."""
        if not self.kite:
            return pd.DataFrame()
        try:
            orders = self.kite.orders()
            return pd.DataFrame(orders)
        except Exception as e:
            logger.error(f"Failed to fetch orders: {e}")
            return pd.DataFrame()

    def get_pnl(self) -> float:
        """Calculate total PnL across positions."""
        df = self.get_positions()
        if df.empty:
            return 0.0
        return df['pnl'].sum() 