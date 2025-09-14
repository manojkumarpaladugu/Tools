import csv
from datetime import datetime
from foreign_stock import ForeignStock
import json
import os

def find_start_and_end_years(input_csv_file):
    """
    Parses a CSV file to find the start and end years based on purchase and sale dates.

    Args:
        input_csv_file (str): The name of the input CSV file.

    Returns:
        tuple: A tuple containing the start year and end year.
    """
    try:
        with open(input_csv_file, 'r', encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            all_dates = []
            for row in csv_reader:
                # Add purchase date
                purchase_date_str = row.get("Purchase date (MM/DD/YYYY)")
                if purchase_date_str:
                    all_dates.append(datetime.strptime(purchase_date_str, '%m/%d/%Y'))
                
                # Add sale date if it exists
                sale_date_str = row.get("Sale date (MM/DD/YYYY)")
                if sale_date_str:
                    all_dates.append(datetime.strptime(sale_date_str, '%m/%d/%Y'))
            
            if not all_dates:
                return None, None
            
            min_date = min(all_dates)
            max_date = max(all_dates)
            
            return min_date.year, max_date.year

    except FileNotFoundError:
        print(f"Error: The file '{input_csv_file}' was not found.")
        return None, None
    except ValueError as e:
            print(f"Error parsing dates: {e}. Please ensure dates are in 'MM/DD/YYYY' format.")
            return None, None

class Form1:
    def __init__(self, ticker: str, start_date: str, end_date: str):
        """
        Initializes the Form1 object.

        Args:
            ticker (str): Stock ticker symbol (e.g., 'MRVL').
            start_date (str): Start date in 'MM-DD-YYYY' format.
            end_date (str): End date in 'MM-DD-YYYY' format.
        """
        if not start_date or not end_date:
            raise RuntimeError("Invalid start or end date provided.")

        self.fs = ForeignStock(ticker, start_date, end_date)
        self.ticker = ticker

    def generate_form(self, input_json_file, input_csv_file, output_csv_file):
        """
        Reads a JSON file and a CSV file, then generates a new CSV file
        by combining data from both sources.

        Args:
            input_json_file (str): The name of the input JSON file (e.g., 'form1.json').
            input_csv_file (str): The name of the input CSV file (e.g., 'input.csv').
            output_file (str): The name of the output CSV file (e.g., 'form1.csv').
        """
        try:
            # Load data from the JSON file
            with open(input_json_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)

            # Load data from the CSV file into a list of dictionaries
            with open(input_csv_file, 'r', encoding='utf-8') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                csv_records = [row for row in csv_reader]

            # Ensure required keys exist
            if "Output Header" not in json_data or not isinstance(json_data["Output Header"], list):
                print("Error: 'Output Header' key not found or is not a list in the JSON data.")
                return
            if self.ticker not in json_data or not isinstance(json_data[self.ticker], dict):
                print(f"Error: {self.ticker} key not found or is not a dictionary.")
                return

            # Get CSV header fields for output
            output_header = json_data["Output Header"]
            ticker_template = json_data[self.ticker]

            # Process each CSV record and generate the output records
            final_records = []
            for csv_record in csv_records:
                print(f"--> Processing CSV record: {csv_record}")
                # Create a new record dictionary for the output CSV
                record = {}

                # Populate the input data
                num_shares = float(csv_record.get("Number of shares", None)) if csv_record.get("Number of shares", None) else None
                purchase_date = csv_record.get("Purchase date (MM/DD/YYYY)", None) if csv_record.get("Purchase date (MM/DD/YYYY)", None) else None
                purchase_price = float(csv_record.get("Purchase price (USD)", None)) if csv_record.get("Purchase price (USD)", None) else None
                purchase_exchange_rate = self.fs.get_exchange_rate(datetime.strptime(purchase_date, '%m/%d/%Y').strftime('%m-%d-%Y')) if purchase_date else None
                sale_date = csv_record.get("Sale date (MM/DD/YYYY)", None) if csv_record.get("Sale date (MM/DD/YYYY)", None) else None
                sale_price = float(csv_record.get("Sale price (USD)", None)) if csv_record.get("Sale price (USD)", None) else None
                sale_exchange_rate = self.fs.get_exchange_rate(datetime.strptime(sale_date, '%m/%d/%Y').strftime('%m-%d-%Y')) if sale_date else None

                # Populate the output data in CSV record
                for field in output_header:
                    record[field] = ""

                    # 1. Use values from the JSON template if available
                    if field in ticker_template:
                        record[field] = ticker_template[field]
                    # 2. Use values from the input CSV for specific fields
                    elif field == "Date of acquiring the interest" and purchase_date:
                        record[field] = purchase_date
                    elif field == "Initial value of the investment" and num_shares and purchase_price and purchase_exchange_rate:
                        record[field] = f"{num_shares * purchase_price * purchase_exchange_rate:.2f}"
                        print(f"Initial value calculated: ₹{record[field]} (Shares: {num_shares}, Purchase Price: ${purchase_price}, Exchange Rate: ₹{purchase_exchange_rate})")
                    elif field == "Peak value of investment during the Period" and num_shares:
                        peak_price, peak_date = self.fs.find_peak_price()
                        exchange_rate = self.fs.get_exchange_rate(peak_date)
                        record[field] = f"{num_shares * peak_price * exchange_rate:.2f}"
                        print(f"Peak value calculated: ₹{record[field]} (Shares: {num_shares}, Peak Price: ${peak_price}, Exchange Rate: ₹{exchange_rate})")
                    elif field == "Closing balance" and num_shares and not sale_date:
                        closing_price, closing_date = self.fs.find_closing_price()
                        exchange_rate = self.fs.get_exchange_rate(closing_date)
                        record[field] = f"{num_shares * closing_price * exchange_rate:.2f}"
                        print(f"Closing balance calculated: ₹{record[field]} (Shares: {num_shares}, Closing Price: ${closing_price}, Exchange Rate: ₹{exchange_rate})")
                    elif field == "Total gross amount paid/credited with respect to the holding during the period":
                        record[field] = ""
                    elif field == "Total gross proceeds from sale or redemption of investment during the period" and num_shares and sale_price and sale_exchange_rate:
                        record[field] = f"{num_shares * sale_price * sale_exchange_rate:.2f}"
                        print(f"Gross proceeds calculated: ₹{record[field]} (Shares: {num_shares}, Sale Price: ${sale_price}, Exchange Rate: ₹{exchange_rate})")
                    else:
                        record[field] = ""

                final_records.append(record)
                print("--> Done processing record.\n")

            # Open the CSV file in write mode
            with open(output_csv_file, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=output_header)
                writer.writeheader()
                writer.writerows(final_records)

            # Print a success message
            full_path = os.path.abspath(output_csv_file)
            print(f"Successfully dumped the data to '{full_path}'")

        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from the file '{input_json_file}'. Please check the file's format.")

if __name__ == "__main__":
    json_file = "input/form1.json"
    csv_input_file = "input/input.csv"
    csv_output_file = "output/form1.csv"

    # Create the output directory if it doesn't exist.
    os.makedirs(os.path.dirname(csv_output_file), exist_ok=True)

    ticker = input("Enter stock ticker symbol (e.g., 'MRVL'): ")

    # Find the start and end years from the CSV
    start_year, end_year = find_start_and_end_years(csv_input_file)

    start_date = f"01-01-{start_year}"
    end_date = f"12-31-{end_year}"
    form1 = Form1(ticker, start_date, end_date)

    form1.generate_form(json_file, csv_input_file, csv_output_file)
