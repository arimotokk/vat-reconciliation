# VAT Reconciliation Agent

A web-based tool for calculating VAT position from sales and purchases transactions. Built for Irish tax compliance workflows.

## Features

- **Multi-format support**: Upload CSV, Excel (.xlsx), or JSON files
- **Automatic calculation**: Computes sales VAT, purchases VAT, and net position
- **Flexible data parsing**: Handles various column naming conventions
- **Smart validation**: Detects missing data, negative amounts, and parsing errors
- **Clean interface**: Simple drag-and-drop file upload

## Installation

```bash
# Clone the repository
git clone https://github.com/arimotokk/vat-reconciliation.git
cd vat-reconciliation

# Install dependencies
pip3 install flask pandas openpyxl

# Run the application
python3 vat_reconciliation.py
```

Open `http://localhost:8080` in your browser.

## Data Format

Your file should contain:

- **Amount column**: Named `amount`, `value`, or `total`
- **Type column**: Named `type` or `category` with values `sales` or `purchases`
- **VAT column** (optional): Named `vat` - if missing, calculated at 23% Irish standard rate

### Example CSV

```csv
amount,type,vat
1000,sales,230
500,purchases,115
2000,sales,460
```

## Output

The tool calculates:

- **Total Sales VAT**: Sum of all VAT from sales transactions
- **Total Purchases VAT**: Sum of all VAT from purchases transactions
- **Net VAT Position**: Sales VAT - Purchases VAT
  - Positive = Amount owed to Revenue
  - Negative = Refund due

## Use Cases

- Cash flow planning for VAT payments
- Quarterly/monthly VAT return preparation
- Client reporting for accounting firms
- Audit preparation and verification

## Built With

- Python 3
- Flask
- Pandas
- HTML/CSS/JavaScript

## Author

Built by a Tax Associate with experience in finance and accounting roles.

## License

MIT
