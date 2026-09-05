#!/bin/bash

# Exit on error
set -e

echo "======================================"
echo " Generating TradeKaro Documentation"
echo "======================================"

# 1. Python Documentation (pdoc)
echo "Generating Python documentation for backend..."
cd backend
# Ensure pdoc is installed
if ! command -v pdoc &> /dev/null
then
    echo "pdoc could not be found, installing..."
    pip install pdoc
fi

# Generate documentation for the main backend modules
pdoc ./api ./services ./strategy_parser ./db -o ../documentation/python_docs

echo "Python documentation generated at documentation/python_docs"
cd ..

# 2. TypeScript Documentation (TypeDoc)
echo "Generating TypeScript documentation for frontend..."
cd frontend

# Install typedoc if it's not in package.json
if ! grep -q "\"typedoc\":" package.json; then
    echo "TypeDoc not found in package.json, installing locally..."
    npm install --save-dev typedoc
fi

# Generate documentation for src/
npx typedoc src/ --out ../documentation/ts_docs --name "TradeKaro NLconverter Frontend" --readme none

echo "TypeScript documentation generated at documentation/ts_docs"
cd ..

echo "======================================"
echo " Documentation generation complete!"
echo "======================================"
