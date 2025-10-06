#!/bin/bash

# ESG Preprocessing Pipeline Execution Script
# This script automates the execution of the preprocessing pipeline

set -e  # Exit on any error

echo "=== ESG Preprocessing Pipeline Execution ==="
echo "Starting at: $(date)"

# Configuration
DATA_PATH="../Data/company_esg_financial_dataset.csv"
CONFIG_PATH="preprocessing_config.yaml"
OUTPUT_DIR="../Data"
MODELS_DIR="../Models"

# Create directories if they don't exist
mkdir -p "$OUTPUT_DIR"
mkdir -p "$MODELS_DIR"

# Check if input data exists
if [ ! -f "$DATA_PATH" ]; then
    echo "Error: Input data file not found at $DATA_PATH"
    echo "Please ensure the data file exists before running the pipeline."
    exit 1
fi

# Check if config exists, create if not
if [ ! -f "$CONFIG_PATH" ]; then
    echo "Configuration file not found. Creating default configuration..."
    python -c "from preprocessing_pipeline import create_config_file; create_config_file('$CONFIG_PATH', 'yaml')"
fi

echo "Using configuration: $CONFIG_PATH"
echo "Input data: $DATA_PATH"
echo "Output directory: $OUTPUT_DIR"
echo "Models directory: $MODELS_DIR"

# Run preprocessing pipeline
echo "Running preprocessing pipeline..."
python -c "
from preprocessing_pipeline import run_pipeline_example
try:
    run_pipeline_example('$DATA_PATH', '$CONFIG_PATH')
    print('✓ Preprocessing pipeline completed successfully!')
except Exception as e:
    print(f'✗ Pipeline failed: {e}')
    exit(1)
"

# Run tests if requested
if [ "$1" = "--test" ]; then
    echo "Running tests..."
    python test_preprocessing_pipeline.py
    echo "✓ Tests completed!"
fi

# Generate summary report
echo "Generating summary report..."
python -c "
import pandas as pd
import os
from pathlib import Path

print('\\n=== PREPROCESSING SUMMARY REPORT ===')
print(f'Generated at: {pd.Timestamp.now()}')

# Check output files
output_dir = Path('$OUTPUT_DIR')
files_created = list(output_dir.glob('*.csv'))

print(f'\\nOutput files created: {len(files_created)}')
for file in sorted(files_created):
    if file.exists():
        df = pd.read_csv(file)
        print(f'  ✓ {file.name}: {df.shape}')
    else:
        print(f'  ✗ {file.name}: Not found')

# Check model files
models_dir = Path('$MODELS_DIR')
model_files = list(models_dir.glob('esg_preprocessing_pipeline*'))

print(f'\\nModel files saved: {len(model_files)}')
for file in sorted(model_files):
    print(f'  ✓ {file.name}')

print('\\n=== PIPELINE EXECUTION COMPLETE ===')
"

echo "Pipeline execution completed at: $(date)"