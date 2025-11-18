#!/bin/bash
# Simple verification script for Int Crucible backend setup
# This script tests that everything is working correctly

set -e

echo "=========================================="
echo "Int Crucible Setup Verification"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0

check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} $1"
        ((FAILED++))
        return 1
    fi
}

echo "Step 1: Checking Python environment..."
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠ Virtual environment not found. Running setup...${NC}"
    ./setup_backend.sh
    source venv/bin/activate
else
    source venv/bin/activate
    check "Virtual environment exists"
fi

echo ""
echo "Step 2: Testing Python and packages..."
python --version > /dev/null 2>&1
check "Python is available"

python -c "import fastapi" > /dev/null 2>&1
check "FastAPI is installed"

python -c "import kosmos" > /dev/null 2>&1
check "Kosmos can be imported"

python -c "import crucible" > /dev/null 2>&1
check "Int Crucible backend can be imported"

echo ""
echo "Step 3: Testing CLI commands..."
crucible version > /dev/null 2>&1
check "CLI command 'crucible version' works"

crucible config > /dev/null 2>&1
check "CLI command 'crucible config' works"

echo ""
echo "Step 4: Testing Kosmos integration..."
# Create minimal .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "DATABASE_URL=sqlite:///crucible.db" > .env
    echo "LOG_LEVEL=INFO" >> .env
    echo -e "${YELLOW}⚠ Created minimal .env file${NC}"
fi

crucible kosmos-test > /dev/null 2>&1
check "Kosmos integration test passes"

echo ""
echo "Step 5: Testing FastAPI application..."
python -c "from crucible.api.main import app; print('OK')" > /dev/null 2>&1
check "FastAPI app can be imported"

# Test that the app structure is correct
python -c "
from crucible.api.main import app
assert app.title == 'Int Crucible API'
assert hasattr(app, 'lifespan')
print('OK')
" > /dev/null 2>&1
check "FastAPI app structure is correct"

echo ""
echo "=========================================="
echo "Verification Summary"
echo "=========================================="
echo -e "${GREEN}Passed: ${PASSED}${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Failed: ${FAILED}${NC}"
    echo ""
    echo "If any tests failed, try:"
    echo "  1. Run ./setup_backend.sh again"
    echo "  2. Check that vendor/kosmos exists"
    echo "  3. Check Python version (3.11+ required)"
    exit 1
else
    echo -e "${GREEN}All tests passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Edit .env file with your API keys (if needed)"
    echo "  2. Run: crucible kosmos-test (to see detailed output)"
    echo "  3. Start the API: python -m crucible.api.main"
    echo "  4. Visit http://127.0.0.1:8000/docs for API documentation"
    exit 0
fi

