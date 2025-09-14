import csv
from datetime import datetime, timedelta
import io
import logging
import pandas
import requests
import yfinance
from sys import exit

class ForeignStock:
    """
    A class to fetch and analyze historical stock and currency exchange data.
    """
    def __init__(self, ticker: str, start_date: str, end_date: str):
        """
        Initializes the ForeignStock object, fetching all necessary data.

        Args:
            ticker (str): Stock ticker symbol (e.g., 'MRVL').
            start_date (str): Start date in 'MM-DD-YYYY' format.
            end_date (str): End date in 'MM-DD-YYYY' format.
        """
        if not start_date or not end_date:
            raise RuntimeError("Invalid start or end date provided.")

        self.logger = self.setup_logger()

        self.start_date = start_date
        self.end_date = end_date

        # Get historical USD to INR rates
        self.exchanges_rates = self.fetch_usd_to_inr_rates(self.start_date, self.end_date)

        # Get historical stock prices
        self.stock_data = self.fetch_stock_price_data(ticker, self.start_date, self.end_date)

    def setup_logger(self):
        """
        Set up the logger for the class. Checks if a handler already exists to prevent
        duplicate logs.
        """
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)

        # Prevent adding multiple handlers if the function is called more than once
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def fetch_usd_to_inr_rates(self, start_date: str, end_date: str) -> dict[str, float]:
        """
        Fetch historical RBI reference data for USD to INR rates.
        NOTE: This URL may not be a stable, long-term source and could change.
              For production use, consider a dedicated financial data API.

        Args:
            start_date (str): Start date in 'MM-DD-YYYY' format.
            end_date (str): End date in 'MM-DD-YYYY' format.

        Returns:
            dict: A dictionary with dates as keys and USD to INR rates as values, or None on error.
        """
        try:
            datetime.strptime(start_date, '%m-%d-%Y')
            datetime.strptime(end_date, '%m-%d-%Y')
        except ValueError:
            raise RuntimeError("Invalid date format. Please use 'MM-DD-YYYY'.")

        url_start_date = datetime.strptime(start_date, '%m-%d-%Y').strftime('%d-%m-%Y')
        url_end_date = datetime.strptime(end_date, '%m-%d-%Y').strftime('%d-%m-%Y')
        url = f"https://www.nseindia.com/api/historicalOR/rbi-reference-rate-stats?from={url_start_date}&to={url_end_date}&csv=true"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        try:
            with requests.get(url, headers=headers, stream=True, timeout=10) as response:
                response.raise_for_status()
                decoded_content = response.content.decode('utf-8-sig')
                usd_to_inr_rates = {}
                csv_file = io.StringIO(decoded_content)
                csv_reader = csv.reader(csv_file)
                next(csv_reader) # Skip header

                for row in csv_reader:
                    if len(row) > 1:
                        try:
                            trade_date = datetime.strptime(row[0].strip(), '%d-%b-%Y').strftime('%m-%d-%Y')
                            usd_to_inr_rate = float(row[1].strip())
                            usd_to_inr_rates[trade_date] = usd_to_inr_rate
                        except (ValueError, IndexError) as e:
                            self.logger.error(f"Skipping row due to data format error: {row}. Error: {e}")
                self.logger.debug(f"Fetched historical USD to INR rates from {start_date} to {end_date}.")
                return usd_to_inr_rates
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Error fetching exchange rates: {e}")

    def get_exchange_rate(self, date: str) -> float | None:
        """
        Get the USD to INR rate for a specific date, falling back to previous days if needed.

        Args:
            date (str): The date in 'MM-DD-YYYY' format for which to find the rate.

        Returns:
            float or None: The rate for the given date, or None if not found.
        """
        try:
            target_date = datetime.strptime(date, '%m-%d-%Y')
        except ValueError:
            raise RuntimeError("Invalid date format. Please use 'MM-DD-YYYY'.")

        if not self.exchanges_rates:
            raise RuntimeError("Rates data is not available.")

        for _ in range(7):  # Check the target date and up to 6 previous days
            current_date_str = target_date.strftime('%m-%d-%Y')
            if current_date_str in self.exchanges_rates:
                rate = self.exchanges_rates[current_date_str]
                if _ > 0:
                    self.logger.warning(f"Exchange rate not found for {date}. Using rate from nearest previous date: {current_date_str}.")
                self.logger.debug(f"Exchange rate is ₹{rate} on {current_date_str}.")
                return rate
            target_date -= timedelta(days=1)

        raise RuntimeError(f"No rate found for {date} or in the preceding week.")

    def fetch_stock_price_data(self, ticker: str, start_date: str, end_date: str) -> pandas.DataFrame:
        """
        Fetch historical stock price data for a given ticker symbol.

        Args:
            ticker (str): Stock ticker symbol (e.g., 'MRVL').
            start_date (str): Start date in 'MM-DD-YYYY' format.
            end_date (str): End date in 'MM-DD-YYYY' format.

        Returns:
            DataFrame: Historical stock price data, or None on error.
        """
        try:
            start_date_obj = datetime.strptime(start_date, '%m-%d-%Y')
            # yfinance's end date is exclusive, so we add one day to get the end of the day.
            end_date_obj = datetime.strptime(end_date, '%m-%d-%Y') + timedelta(days=1)
        except ValueError:
            raise RuntimeError("Invalid date format. Please use 'MM-DD-YYYY'.")

        try:
            adjust_price = False
            self.logger.info(f"Note: Fetching {ticker} stock data with auto_adjust={adjust_price}.")
            stock_data = yfinance.download(ticker, start=start_date_obj, end=end_date_obj, auto_adjust=adjust_price)
            if stock_data.empty:
                raise RuntimeError(f"No data fetched for ticker {ticker}.")
            self.logger.debug(f"Fetched historical stock price data for {ticker} from {start_date} to {end_date}.")
            return stock_data
        except Exception as e:
            raise RuntimeError(f"Failed to fetch historical stock price data for {ticker}: {e}")

    def find_peak_price(self) -> tuple[float, str]:
        """
        Find the peak price and corresponding date from the stock data.

        Returns:
            tuple: Peak price and corresponding date, or (None, None) on error.
        """
        if self.stock_data is None or self.stock_data.empty:
            raise RuntimeError("No data available to determine the peak price.")

        # pandas.Series.max() always returns a scalar, and pandas.Series.idxmax() returns a Timestamp
        peak_price = self.stock_data['High'].max()
        peak_date = self.stock_data['High'].idxmax()
        # Ensure peak_price is a scalar value
        if isinstance(peak_price, pandas.Series):
            peak_price = peak_price.iloc[0]
        # Ensure peak_date is a scalar value
        if isinstance(peak_date, pandas.Series):
            peak_date = peak_date.iloc[0].strftime('%m-%d-%Y')
        self.logger.debug(f"Peak price found: ${peak_price:.2f} on {peak_date}.")
        return peak_price, peak_date

    def find_closing_price(self) -> tuple[float, str]:
        """
        Find the closing price on the last available trading day.

        Returns:
            tuple: Closing price and the corresponding date, or (None, None) on error.
        """
        if self.stock_data is None or self.stock_data.empty:
            raise RuntimeError("No data available to determine the closing price.")

        last_trading_day_result = self.stock_data.index[-1]
        if isinstance(last_trading_day_result, pandas.Series):
            last_trading_day = last_trading_day_result.iloc[0]
        else:
            last_trading_day = last_trading_day_result

        closing_price = self.stock_data.loc[last_trading_day, 'Close'].iloc[0]
        closing_date = last_trading_day.strftime('%m-%d-%Y')
        self.logger.debug(f"Closing price found: ${closing_price:.2f} on {closing_date}.")
        return closing_price, closing_date

if __name__ == '__main__':
    # Example usage
    # Create an instance for the year 2024
    stock_analyzer = ForeignStock(ticker='MRVL', start_date='01-01-2024', end_date='12-31-2024')

    # Find the peak price
    peak_price, peak_date = stock_analyzer.find_peak_price()
    if peak_price and peak_date:
        peak_rate = stock_analyzer.get_exchange_rate(peak_date)
        if peak_rate:
            peak_inr = peak_price * peak_rate
            print(f"Peak Price: ${peak_price:.2f} on {peak_date} (INR: ₹{peak_inr:.2f})")

    # Find the closing price
    closing_price, closing_date = stock_analyzer.find_closing_price()
    if closing_price and closing_date:
        closing_rate = stock_analyzer.get_exchange_rate(closing_date)
        if closing_rate:
            closing_inr = closing_price * closing_rate
            print(f"Closing Price: ${closing_price:.2f} on {closing_date} (INR: ₹{closing_inr:.2f})")
