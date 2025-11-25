#!/bin/bash

echo "=== dbt Setup Verification ==="
echo ""

# Check if dbt is installed
echo "1. Checking dbt installation..."
if command -v dbt &> /dev/null; then
    echo "✓ dbt is installed: $(dbt --version | head -n 1)"
else
    echo "✗ dbt is not installed. Install with: pip install dbt-snowflake"
    exit 1
fi

echo ""
echo "2. Checking environment variables..."
required_vars=("SNOWFLAKE_ACCOUNT" "SNOWFLAKE_USER" "SNOWFLAKE_PASSWORD" "SNOWFLAKE_ROLE" "SNOWFLAKE_WAREHOUSE" "SNOWFLAKE_DATABASE")

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "✗ $var is not set"
    else
        echo "✓ $var is set"
    fi
done

echo ""
echo "3. Checking dbt project files..."
files=("dbt_project.yml" "profiles.yml" "models/input/_sources.yml")

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file exists"
    else
        echo "✗ $file is missing"
    fi
done

echo ""
echo "4. Checking dbt models..."
model_files=(
    "models/input/staging/stg_stock_prices.sql"
    "models/output/core/stock_moving_averages.sql"
    "models/output/core/stock_rsi.sql"
    "models/output/core/stock_technical_indicators.sql"
)

for file in "${model_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file exists"
    else
        echo "✗ $file is missing"
    fi
done

echo ""
echo "5. Testing dbt connection..."
dbt debug --profiles-dir .

echo ""
echo "=== Setup verification complete ==="
echo ""
echo "Next steps:"
echo "1. Set environment variables if not already set"
echo "2. Run: dbt deps --profiles-dir ."
echo "3. Run: dbt compile --profiles-dir ."
echo "4. Run: dbt run --profiles-dir ."
