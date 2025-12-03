#!/usr/bin/env python3
"""
VAT Reconciliation Agent - MVP
Handles CSV, Excel, and JSON uploads to calculate VAT position
"""

from flask import Flask, request, render_template_string, jsonify
import pandas as pd
import json
from io import StringIO, BytesIO
from decimal import Decimal, InvalidOperation

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VAT Reconciliation Agent</title>
    <link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --cream: #FFF8E7;
            --deep-green: #1B4332;
            --forest: #2D6A4F;
            --sage: #52B788;
            --coral: #E76F51;
            --gold: #F4A261;
        }

        body {
            font-family: 'Space Mono', monospace;
            background: linear-gradient(135deg, var(--cream) 0%, #FFE8CC 100%);
            min-height: 100vh;
            padding: 2rem;
            color: var(--deep-green);
        }

        .container {
            max-width: 900px;
            margin: 0 auto;
        }

        header {
            text-align: center;
            margin-bottom: 3rem;
            animation: fadeInDown 0.8s ease-out;
        }

        h1 {
            font-family: 'DM Serif Display', serif;
            font-size: 3.5rem;
            color: var(--deep-green);
            margin-bottom: 0.5rem;
            font-style: italic;
            text-shadow: 3px 3px 0 rgba(82, 183, 136, 0.2);
        }

        .subtitle {
            font-size: 0.9rem;
            color: var(--forest);
            letter-spacing: 2px;
            text-transform: uppercase;
        }

        .upload-card {
            background: white;
            border-radius: 20px;
            padding: 3rem;
            box-shadow: 0 10px 40px rgba(27, 67, 50, 0.15);
            margin-bottom: 2rem;
            animation: fadeInUp 0.8s ease-out 0.2s both;
            border: 3px solid var(--sage);
        }

        .upload-zone {
            border: 3px dashed var(--sage);
            border-radius: 15px;
            padding: 3rem;
            text-align: center;
            transition: all 0.3s ease;
            background: var(--cream);
            position: relative;
            overflow: hidden;
        }

        .upload-zone::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, var(--sage) 1px, transparent 1px);
            background-size: 30px 30px;
            opacity: 0.1;
            animation: float 20s linear infinite;
        }

        @keyframes float {
            0% { transform: translate(0, 0); }
            100% { transform: translate(30px, 30px); }
        }

        .upload-zone:hover {
            border-color: var(--coral);
            background: #FFF5F0;
            transform: scale(1.02);
        }

        .upload-zone.dragover {
            border-color: var(--gold);
            background: #FFF9E6;
            transform: scale(1.05);
        }

        input[type="file"] {
            display: none;
        }

        .upload-label {
            cursor: pointer;
            font-size: 1.1rem;
            color: var(--deep-green);
            position: relative;
            z-index: 1;
        }

        .upload-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
            display: block;
        }

        .btn {
            background: var(--deep-green);
            color: white;
            border: none;
            padding: 1rem 3rem;
            font-size: 1rem;
            font-family: 'Space Mono', monospace;
            font-weight: 700;
            border-radius: 50px;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 1.5rem;
            box-shadow: 0 5px 15px rgba(27, 67, 50, 0.3);
        }

        .btn:hover {
            background: var(--coral);
            transform: translateY(-3px);
            box-shadow: 0 8px 20px rgba(231, 111, 81, 0.4);
        }

        .btn:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }

        .results-card {
            background: white;
            border-radius: 20px;
            padding: 3rem;
            box-shadow: 0 10px 40px rgba(27, 67, 50, 0.15);
            animation: fadeInUp 0.8s ease-out;
            border: 3px solid var(--coral);
        }

        .result-header {
            font-family: 'DM Serif Display', serif;
            font-size: 2rem;
            color: var(--deep-green);
            margin-bottom: 2rem;
            text-align: center;
            font-style: italic;
        }

        .result-grid {
            display: grid;
            gap: 1.5rem;
        }

        .result-item {
            background: var(--cream);
            padding: 1.5rem;
            border-radius: 15px;
            border-left: 5px solid var(--sage);
            transition: all 0.3s ease;
        }

        .result-item:hover {
            transform: translateX(10px);
            border-left-color: var(--coral);
        }

        .result-label {
            font-size: 0.9rem;
            color: var(--forest);
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .result-value {
            font-size: 2rem;
            font-weight: 700;
            color: var(--deep-green);
        }

        .result-value.positive {
            color: var(--coral);
        }

        .result-value.negative {
            color: var(--sage);
        }

        .warning {
            background: #FFF3CD;
            border: 2px solid var(--gold);
            border-radius: 10px;
            padding: 1rem;
            margin-top: 1rem;
            color: var(--deep-green);
        }

        .error {
            background: #FFE8E8;
            border: 2px solid var(--coral);
            border-radius: 10px;
            padding: 1rem;
            margin-top: 1rem;
            color: var(--deep-green);
        }

        .spinner {
            border: 4px solid var(--cream);
            border-top: 4px solid var(--coral);
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 2rem auto;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        @keyframes fadeInDown {
            from {
                opacity: 0;
                transform: translateY(-30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .hidden {
            display: none;
        }

        .file-name {
            margin-top: 1rem;
            color: var(--forest);
            font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>VAT Reconciliation</h1>
            <p class="subtitle">Sales vs Purchases Analysis</p>
        </header>

        <div class="upload-card">
            <form id="uploadForm" enctype="multipart/form-data">
                <div class="upload-zone" id="dropZone">
                    <label for="fileInput" class="upload-label">
                        <span class="upload-icon">📊</span>
                        <div>Drop your file here or click to browse</div>
                        <div style="margin-top: 0.5rem; font-size: 0.85rem; color: var(--forest);">
                            Supports CSV, Excel (.xlsx), and JSON
                        </div>
                    </label>
                    <input type="file" id="fileInput" name="file" accept=".csv,.xlsx,.xls,.json">
                    <div class="file-name hidden" id="fileName"></div>
                </div>
                <div style="text-align: center;">
                    <button type="submit" class="btn" id="submitBtn" disabled>Calculate VAT Position</button>
                </div>
            </form>
        </div>

        <div id="loading" class="hidden">
            <div class="spinner"></div>
        </div>

        <div id="results" class="hidden"></div>
    </div>

    <script>
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        const fileName = document.getElementById('fileName');
        const submitBtn = document.getElementById('submitBtn');
        const uploadForm = document.getElementById('uploadForm');
        const loading = document.getElementById('loading');
        const results = document.getElementById('results');

        // Drag and drop handlers
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                fileInput.files = files;
                handleFileSelect();
            }
        });

        fileInput.addEventListener('change', handleFileSelect);

        function handleFileSelect() {
            const file = fileInput.files[0];
            if (file) {
                fileName.textContent = `Selected: ${file.name}`;
                fileName.classList.remove('hidden');
                submitBtn.disabled = false;
            }
        }

        uploadForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);

            loading.classList.remove('hidden');
            results.classList.add('hidden');
            submitBtn.disabled = true;

            try {
                const response = await fetch('/calculate', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (data.error) {
                    showError(data.error);
                } else {
                    showResults(data);
                }
            } catch (error) {
                showError('An error occurred while processing the file.');
            } finally {
                loading.classList.add('hidden');
                submitBtn.disabled = false;
            }
        });

        function showResults(data) {
            let warningHtml = '';
            if (data.warnings && data.warnings.length > 0) {
                warningHtml = `<div class="warning">
                    <strong>⚠️ Warnings:</strong>
                    <ul style="margin-top: 0.5rem; margin-left: 1.5rem;">
                        ${data.warnings.map(w => `<li>${w}</li>`).join('')}
                    </ul>
                </div>`;
            }

            const netClass = data.net_position >= 0 ? 'positive' : 'negative';
            const netLabel = data.net_position >= 0 ? 'Amount Owed to Revenue' : 'Refund Due';

            results.innerHTML = `
                <div class="results-card">
                    <div class="result-header">VAT Position</div>
                    <div class="result-grid">
                        <div class="result-item">
                            <div class="result-label">Total Sales VAT</div>
                            <div class="result-value">€${data.sales_vat.toFixed(2)}</div>
                        </div>
                        <div class="result-item">
                            <div class="result-label">Total Purchases VAT</div>
                            <div class="result-value">€${data.purchases_vat.toFixed(2)}</div>
                        </div>
                        <div class="result-item" style="border-left-color: var(--coral); border-left-width: 8px;">
                            <div class="result-label">${netLabel}</div>
                            <div class="result-value ${netClass}">€${Math.abs(data.net_position).toFixed(2)}</div>
                        </div>
                    </div>
                    ${warningHtml}
                </div>
            `;
            results.classList.remove('hidden');
        }

        function showError(message) {
            results.innerHTML = `
                <div class="error">
                    <strong>❌ Error:</strong> ${message}
                </div>
            `;
            results.classList.remove('hidden');
        }
    </script>
</body>
</html>
"""


def parse_file(file):
    """Parse uploaded file and return DataFrame"""
    filename = file.filename.lower()
    
    try:
        if filename.endswith('.csv'):
            content = file.read().decode('utf-8')
            df = pd.read_csv(StringIO(content))
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(BytesIO(file.read()))
        elif filename.endswith('.json'):
            content = file.read().decode('utf-8')
            data = json.loads(content)
            df = pd.DataFrame(data)
        else:
            return None, "Unsupported file format. Please upload CSV, Excel, or JSON."
        
        return df, None
    except Exception as e:
        return None, f"Error parsing file: {str(e)}"


def validate_and_process(df):
    """Validate data and calculate VAT position"""
    warnings = []
    
    # Normalize column names (case-insensitive, strip whitespace)
    df.columns = df.columns.str.strip().str.lower()
    
    # Look for required columns with flexible naming
    amount_col = None
    type_col = None
    vat_col = None
    
    for col in df.columns:
        if 'amount' in col or 'value' in col or 'total' in col:
            amount_col = col
        if 'type' in col or 'category' in col or 'kind' in col:
            type_col = col
        if 'vat' in col and amount_col != col:
            vat_col = col
    
    if not amount_col:
        return None, "No amount column found. Expected columns like 'amount', 'value', or 'total'."
    
    if not type_col:
        return None, "No type column found. Expected columns like 'type', 'category' with values 'sales' or 'purchases'."
    
    # If VAT column exists, use it; otherwise calculate from amount (assume amount includes VAT)
    if vat_col:
        df['vat_amount'] = pd.to_numeric(df[vat_col], errors='coerce')
    else:
        # Assume amount is VAT-inclusive, extract VAT (23% standard rate in Ireland)
        warnings.append("No VAT column found. Calculating VAT from amounts using 23% rate.")
        df['vat_amount'] = pd.to_numeric(df[amount_col], errors='coerce') * (23/123)
    
    # Normalize transaction types
    df['transaction_type'] = df[type_col].str.strip().str.lower()
    
    # Check for invalid data
    if df['vat_amount'].isna().any():
        count = df['vat_amount'].isna().sum()
        warnings.append(f"{count} row(s) with invalid VAT amounts (skipped).")
        df = df.dropna(subset=['vat_amount'])
    
    if df['vat_amount'].lt(0).any():
        count = df['vat_amount'].lt(0).sum()
        warnings.append(f"{count} row(s) with negative VAT amounts detected.")
    
    # Calculate totals
    sales_vat = df[df['transaction_type'].str.contains('sale', na=False)]['vat_amount'].sum()
    purchases_vat = df[df['transaction_type'].str.contains('purchase', na=False)]['vat_amount'].sum()
    
    if sales_vat == 0 and purchases_vat == 0:
        return None, "No valid sales or purchases transactions found. Check your type column values (should be 'sales' or 'purchases')."
    
    net_position = sales_vat - purchases_vat
    
    return {
        'sales_vat': float(sales_vat),
        'purchases_vat': float(purchases_vat),
        'net_position': float(net_position),
        'warnings': warnings
    }, None


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/calculate', methods=['POST'])
def calculate():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Parse file
    df, error = parse_file(file)
    if error:
        return jsonify({'error': error}), 400
    
    # Validate and process
    result, error = validate_and_process(df)
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify(result)


if __name__ == '__main__':
    print("🚀 VAT Reconciliation Agent starting...")
    print("📊 Open http://localhost:5000 in your browser")
    app.run(debug=True, host='0.0.0.0', port=8080)
