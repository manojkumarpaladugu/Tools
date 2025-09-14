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

class Form2:
    def __init__(self, ticker: str, start_date: str, end_date: str):
        """
        Initializes the Form2 object.

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

            # Get CSV header fields for output
            output_header = json_data["Output Header"]

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
                bank_transaction_date = csv_record.get("Bank transaction date (MM/DD/YYYY)", None) if csv_record.get("Bank transaction date (MM/DD/YYYY)", None) else None
                amount_credited_in_bank = float(csv_record.get("Amount credited in bank (INR)", None)) if csv_record.get("Amount credited in bank (INR)", None) else None

                # Populate the output data in CSV record
                for field in output_header:
                    record[field] = ""
                    if field == "Number of shares" and num_shares:
                        record[field] = str(num_shares)
                    elif field == "Purchase date (MM/DD/YYYY)" and purchase_date:
                        record[field] = purchase_date
                    elif field == "Purchase price (USD)" and purchase_price:
                        record[field] = str(purchase_price)
                    elif field == "Purchase Amount (USD)" and num_shares and purchase_price:
                        record[field] = f"{num_shares * purchase_price:.2f}"
                    elif field == "USD to INR on purchase date" and purchase_exchange_rate:
                        record[field] = f"{purchase_exchange_rate:.2f}"
                    elif field == "Purchase amount (INR)" and num_shares and purchase_price and purchase_exchange_rate:
                        record[field] = f"{num_shares * purchase_price * purchase_exchange_rate:.2f}"
                        print(f"Purchase value calculated: ₹{record[field]} (Shares: {num_shares}, Purchase Price: ${purchase_price}, Exchange Rate: ₹{purchase_exchange_rate})")
                    elif field == "Holding Days" and purchase_date and sale_date:
                        record[field] = str((datetime.strptime(sale_date, '%m/%d/%Y') - datetime.strptime(purchase_date, '%m/%d/%Y')).days)
                    elif field == "Sale date (MM/DD/YYYY)" and sale_date:
                        record[field] = sale_date
                    elif field == "Sale price (USD)" and sale_price:
                        record[field] = str(sale_price)
                    elif field == "Sale amount (USD)" and num_shares and sale_price:
                        record[field] = f"{num_shares * sale_price:.2f}"
                    elif field == "USD to INR on sale date" and sale_exchange_rate:
                        record[field] = f"{sale_exchange_rate:.2f}"
                    elif field == "Sale amount (INR)" and num_shares and sale_price and sale_exchange_rate:
                        record[field] = f"{num_shares * sale_price * sale_exchange_rate:.2f}"
                        print(f"Sale value calculated: ₹{record[field]} (Shares: {num_shares}, Sale Price: ${sale_price}, Exchange Rate: ₹{sale_exchange_rate})")
                    elif field == "Bank transaction date (MM/DD/YYYY)" and bank_transaction_date:
                        record[field] = bank_transaction_date
                    elif field == "Capital gains (INR)" and num_shares and sale_price and sale_exchange_rate and purchase_price and purchase_exchange_rate:
                        capital_gains = (num_shares * sale_price * sale_exchange_rate) - (num_shares * purchase_price * purchase_exchange_rate)
                        record[field] = f"{capital_gains:.2f}"
                        print(f"Capital gains calculated: ₹{record[field]} (Shares: {num_shares}, Sale Price: ${sale_price}, Sale Exchange Rate: ₹{sale_exchange_rate}, Purchase Price: ${purchase_price}, Purchase Exchange Rate: ₹{purchase_exchange_rate})")
                    elif field == "Amount credited in bank (INR)" and amount_credited_in_bank:
                        record[field] = str(amount_credited_in_bank)
                    elif field == "Difference (INR)" and num_shares and sale_price and sale_exchange_rate and purchase_price and purchase_exchange_rate and amount_credited_in_bank:
                        difference = amount_credited_in_bank - (num_shares * sale_price * sale_exchange_rate)
                        record[field] = f"{difference:.2f}"
                        print(f"Difference calculated: ₹{record[field]} (Amount Credited: ₹{amount_credited_in_bank}, Sale Value: ₹{num_shares * sale_price * sale_exchange_rate})")
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
    json_file = "input/form2.json"
    csv_input_file = "input/input.csv"
    csv_output_file = "output/form2.csv"

    # Create the output directory if it doesn't exist.
    os.makedirs(os.path.dirname(csv_output_file), exist_ok=True)

    ticker = input("Enter stock ticker symbol (e.g., 'MRVL'): ")

    # Find the start and end years from the CSV
    start_year, end_year = find_start_and_end_years(csv_input_file)

    start_date = f"01-01-{start_year}"
    end_date = f"12-31-{end_year}"
    form2 = Form2(ticker, start_date, end_date)

    form2.generate_form(json_file, csv_input_file, csv_output_file)
