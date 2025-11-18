#!/bin/bash
# Setup script for Int Crucible backend environment

set -e

echo "Setting up Int Crucible backend environment..."

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python 3.11+ is required. Found: $python_version"
    exit 1
fi

echo "✓ Python version OK: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install Kosmos first (editable install from vendor directory)
echo "Installing Kosmos from vendor/kosmos..."
if [ -d "vendor/kosmos" ]; then
    # Workaround for chromadb/pydantic dependency conflict:
    # Install newer chromadb that supports pydantic 2.x first, then install Kosmos
    echo "Installing compatible chromadb version..."
    pip install "chromadb>=1.0.0" --no-deps || echo "⚠ chromadb installation skipped (optional dependency)"
    
    # Install Kosmos - it will use the already-installed chromadb if available
    echo "Installing Kosmos..."
    pip install -e vendor/kosmos || {
        echo "⚠ Standard Kosmos installation failed, trying with dependency workaround..."
        # If that fails, try installing core dependencies first
        pip install "pydantic>=2.0.0" "pydantic-settings>=2.0.0" "anthropic>=0.40.0" "openai>=1.0.0" \
            "sqlalchemy>=2.0.0" "alembic>=1.13.0" "httpx>=0.27.0" "tenacity>=8.2.0" \
            "python-dotenv>=1.0.0" "rich>=13.0.0" "click>=8.1.0" "typer>=0.9.0" -q
        # Then install Kosmos without chromadb constraint
        pip install -e vendor/kosmos --no-deps || {
            echo "Error: Failed to install Kosmos. This may be due to dependency conflicts."
            echo "You may need to install Kosmos manually or resolve dependency issues."
            exit 1
        }
    }
    echo "✓ Kosmos installed"
else
    echo "Error: vendor/kosmos directory not found"
    echo "Please ensure Kosmos is vendored in vendor/kosmos"
    exit 1
fi

# Install Int Crucible backend
echo "Installing Int Crucible backend..."
pip install -e .
echo "✓ Int Crucible backend installed"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "✓ .env file created (please edit with your configuration)"
else
    echo "✓ .env file already exists"
fi

# Initialize Kosmos database
echo "Initializing Kosmos database..."
if [ -f ".env" ]; then
    # Source .env to get DATABASE_URL
    export $(grep -v '^#' .env | xargs)
    
    # Run Kosmos database initialization
    python -c "from kosmos.db import init_from_config; init_from_config()" || echo "⚠ Database initialization skipped (may need manual setup)"
    echo "✓ Database initialization attempted"
else
    echo "⚠ Skipping database initialization (no .env file)"
fi

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration (API keys, database URL, etc.)"
echo "2. Activate the virtual environment: source venv/bin/activate"
echo "3. Test the integration: crucible kosmos-test"
echo "4. Start the API server: crucible api (or python -m crucible.api.main)"
echo ""

