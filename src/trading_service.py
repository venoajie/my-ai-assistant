
# src/trading_service.py

"""
This is a monolithic service for handling trades.
It connects to the market, processes orders, and logs results.
"""

class MarketConnector:
    def connect(self):
        print("Connecting to market...")

class OrderProcessor:
    def process(self, order):
        print(f"Processing order: {order}")

class TradeLogger:
    def log(self, result):
        print(f"Logging trade: {result}")

def main():
    connector = MarketConnector()
    processor = OrderProcessor()
    logger = TradeLogger()
    
    connector.connect()
    processor.process("BUY 100 AAPL")
    logger.log("SUCCESS")

if __name__ == "__main__":
    main()