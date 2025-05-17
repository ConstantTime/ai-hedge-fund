"""
Zerodha order executor for Indian stocks.
"""

import os
from typing import List, Dict, Any
from loguru import logger

class Order:
    """Class representing an order."""
    
    def __init__(self, ticker: str, qty: int, side: str, reason: str, price: float = None):
        """
        Initialize an order.
        
        Args:
            ticker: The stock ticker symbol
            qty: Quantity of shares
            side: "buy" or "sell"
            reason: Reason for this order
            price: Optional limit price
        """
        self.ticker = ticker
        self.qty = qty
        self.side = side
        self.reason = reason
        self.price = price


class ZerodhaExecutor:
    """Handles order execution using Zerodha's API."""
    
    def __init__(self, api_key: str = None, api_secret: str = None, access_token: str = None, dry_run: bool = True):
        """
        Initialize the Zerodha executor.
        
        Args:
            api_key: Zerodha API key
            api_secret: Zerodha API secret
            access_token: Zerodha access token
            dry_run: If True, just log orders instead of actually placing them
        """
        self.dry_run = dry_run
        
        # Store credentials
        self.api_key = api_key or os.environ.get("ZERODHA_API_KEY")
        self.api_secret = api_secret or os.environ.get("ZERODHA_API_SECRET")
        self.access_token = access_token or os.environ.get("ZERODHA_ACCESS_TOKEN")
        
        # Initialize KiteConnect
        self.kite = None
        if not self.dry_run and self.api_key and self.access_token:
            try:
                from kiteconnect import KiteConnect
                self.kite = KiteConnect(api_key=self.api_key)
                self.kite.set_access_token(self.access_token)
                logger.info("ZerodhaExecutor initialized successfully with KiteConnect")
            except Exception as e:
                logger.error(f"Error initializing KiteConnect: {e}")
                logger.warning("Switching to dry_run mode")
                self.dry_run = True
        else:
            logger.info(f"ZerodhaExecutor initialized (dry_run={dry_run})")
            
    def place_orders(self, orders: List[Order]):
        """
        Place a list of orders.
        
        Args:
            orders: List of Order objects
        """
        for order in orders:
            if self.dry_run:
                logger.info(f"DRY-RUN ORDER: {order.side} {order.qty} {order.ticker} | Reason: {order.reason}")
            else:
                try:
                    if not self.kite:
                        logger.error("KiteConnect not initialized, cannot place real order")
                        continue
                        
                    logger.info(f"Placing order: {order.side} {order.qty} {order.ticker}")
                    
                    # Set transaction type based on side
                    transaction_type = "BUY" if order.side.lower() == "buy" else "SELL"
                    
                    # Determine order type (market or limit)
                    order_type = "MARKET"
                    price = None
                    if order.price:
                        order_type = "LIMIT"
                        price = order.price
                    
                    # Place the order
                    order_id = self.kite.place_order(
                        variety="regular",
                        exchange="NSE",
                        tradingsymbol=order.ticker,
                        transaction_type=transaction_type,
                        quantity=order.qty,
                        price=price,
                        product="CNC",  # Cash and Carry (delivery)
                        order_type=order_type
                    )
                    
                    logger.info(f"Order placed successfully: {order_id}")
                    
                except Exception as e:
                    logger.error(f"Error placing order for {order.ticker}: {e}")
    
    def cancel_all(self):
        """Cancel all open orders."""
        if self.dry_run:
            logger.info("DRY-RUN: Cancelling all orders")
            return
            
        try:
            if not self.kite:
                logger.error("KiteConnect not initialized, cannot cancel orders")
                return
                
            # Get all open orders
            orders = self.kite.orders()
            
            # Cancel each open order
            for order in orders:
                if order["status"] in ["OPEN", "PENDING"]:
                    logger.info(f"Cancelling order: {order['order_id']}")
                    self.kite.cancel_order(
                        variety="regular",
                        order_id=order["order_id"]
                    )
                    
            logger.info("All open orders cancelled")
            
        except Exception as e:
            logger.error(f"Error cancelling orders: {e}")
            
    def get_positions(self):
        """Get current positions."""
        if self.dry_run:
            logger.info("DRY-RUN: Cannot get real positions in dry run mode")
            return {}
            
        try:
            if not self.kite:
                logger.error("KiteConnect not initialized, cannot get positions")
                return {}
                
            # Get positions from Kite
            positions = self.kite.positions()
            
            # Format positions in a more usable way
            formatted_positions = {}
            if "net" in positions:
                for position in positions["net"]:
                    ticker = position["tradingsymbol"]
                    formatted_positions[ticker] = {
                        "quantity": position["quantity"],
                        "average_price": position["average_price"],
                        "pnl": position["pnl"]
                    }
                    
            return formatted_positions
            
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return {} 