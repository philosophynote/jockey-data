import pickle
import csv
import pandas as pd
from pathlib import Path

def pickle_to_csv(pickle_file, csv_file=None):
    """
    Convert a pickle file to CSV format.

    Args:
        pickle_file (str): Path to the input pickle file
        csv_file (str, optional): Path to the output CSV file.
                                 If None, uses same name with .csv extension
    """
    # Set output filename if not provided
    if csv_file is None:
        csv_file = Path(pickle_file).with_suffix('.csv')

    # Load pickle file
    with open(pickle_file, 'rb') as f:
        data = pickle.load(f)

    # Handle different data types
    if isinstance(data, pd.DataFrame):
        # If it's a DataFrame, use pandas to_csv
        data.to_csv(csv_file, index=False)
    elif isinstance(data, (list, tuple)):
        # If it's a list/tuple, assume it's rows of data
        if len(data) > 0 and isinstance(data[0], dict):
            # List of dictionaries
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
        else:
            # List of lists/tuples
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(data)
    elif isinstance(data, dict):
        # If it's a dictionary, convert to DataFrame
        df = pd.DataFrame(data)
        df.to_csv(csv_file, index=False)
    else:
        raise ValueError(f"Unsupported data type: {type(data)}")

    print(f"Converted {pickle_file} to {csv_file}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python pickle_to_csv.py <pickle_file> [csv_file]")
        sys.exit(1)

    pickle_file = sys.argv[1]
    csv_file = sys.argv[2] if len(sys.argv) > 2 else None

    pickle_to_csv(pickle_file, csv_file)
