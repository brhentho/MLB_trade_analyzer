#!/bin/bash

# Baseball Trade AI - Test Runner Script
# Comprehensive test execution script with different test types and environments

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
TEST_TYPE="all"
ENVIRONMENT="development"
COVERAGE=true
PARALLEL=true
VERBOSE=false
QUICK=false
MARKERS=""
OUTPUT_FORMAT="terminal"

# Functions
print_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -t, --test-type TYPE    Test type: all, unit, integration, security, performance, e2e"
    echo "  -e, --env ENV          Environment: development, testing, ci"
    echo "  -m, --markers MARKERS  Pytest markers to run (e.g., 'unit and not slow')"
    echo "  --no-coverage          Disable coverage reporting"
    echo "  --no-parallel          Disable parallel test execution"
    echo "  -v, --verbose          Verbose output"
    echo "  -q, --quick            Quick test run (skip slow tests)"
    echo "  -f, --format FORMAT    Output format: terminal, junit, html, json"
    echo "  -h, --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -t unit -v                    # Run unit tests with verbose output"
    echo "  $0 -t security --no-parallel     # Run security tests sequentially"
    echo "  $0 -m 'not slow' -q              # Quick test run, skip slow tests"
    echo "  $0 -e ci -f junit                # CI environment with JUnit output"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE} Baseball Trade AI - Test Runner${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
}

print_section() {
    echo -e "${GREEN}➤ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--test-type)
            TEST_TYPE="$2"
            shift 2
            ;;
        -e|--env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -m|--markers)
            MARKERS="$2"
            shift 2
            ;;
        --no-coverage)
            COVERAGE=false
            shift
            ;;
        --no-parallel)
            PARALLEL=false
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -q|--quick)
            QUICK=true
            shift
            ;;
        -f|--format)
            OUTPUT_FORMAT="$2"
            shift 2
            ;;
        -h|--help)
            print_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            print_usage
            exit 1
            ;;
    esac
done

print_header

# Validate test type
valid_types=("all" "unit" "integration" "security" "performance" "e2e" "smoke" "regression")
if [[ ! " ${valid_types[@]} " =~ " ${TEST_TYPE} " ]]; then
    print_error "Invalid test type: $TEST_TYPE"
    echo "Valid types: ${valid_types[*]}"
    exit 1
fi

# Set up environment
print_section "Setting up test environment"

# Check if we're in the backend directory
if [[ ! -f "pytest.ini" ]]; then
    if [[ -d "backend" ]]; then
        cd backend
    else
        print_error "Cannot find pytest.ini or backend directory"
        exit 1
    fi
fi

# Load environment variables
if [[ -f ".env.${ENVIRONMENT}" ]]; then
    print_success "Loading environment from .env.${ENVIRONMENT}"
    export $(grep -v '^#' .env.${ENVIRONMENT} | xargs)
elif [[ -f ".env" ]]; then
    print_success "Loading environment from .env"
    export $(grep -v '^#' .env | xargs)
else
    print_warning "No environment file found, using defaults"
fi

# Set test-specific environment variables
export ENVIRONMENT="testing"
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Create directories for test outputs
mkdir -p test-results
mkdir -p htmlcov

# Build pytest command
print_section "Building test command"

PYTEST_ARGS=""

# Add markers based on test type
case $TEST_TYPE in
    "unit")
        PYTEST_ARGS="$PYTEST_ARGS -m 'unit'"
        if [[ $QUICK == true ]]; then
            PYTEST_ARGS="$PYTEST_ARGS and not slow"
        fi
        ;;
    "integration")
        PYTEST_ARGS="$PYTEST_ARGS -m 'integration'"
        ;;
    "security")
        PYTEST_ARGS="$PYTEST_ARGS -m 'security'"
        ;;
    "performance")
        PYTEST_ARGS="$PYTEST_ARGS -m 'performance'"
        ;;
    "e2e")
        PYTEST_ARGS="$PYTEST_ARGS -m 'e2e'"
        ;;
    "smoke")
        PYTEST_ARGS="$PYTEST_ARGS -m 'smoke'"
        ;;
    "regression")
        PYTEST_ARGS="$PYTEST_ARGS -m 'regression'"
        ;;
    "all")
        if [[ $QUICK == true ]]; then
            PYTEST_ARGS="$PYTEST_ARGS -m 'not slow'"
        fi
        ;;
esac

# Add custom markers if specified
if [[ -n "$MARKERS" ]]; then
    if [[ -n "$PYTEST_ARGS" && "$PYTEST_ARGS" == *"-m"* ]]; then
        PYTEST_ARGS="$PYTEST_ARGS and $MARKERS"
    else
        PYTEST_ARGS="$PYTEST_ARGS -m '$MARKERS'"
    fi
fi

# Add coverage options
if [[ $COVERAGE == true ]]; then
    PYTEST_ARGS="$PYTEST_ARGS --cov=."
    
    case $OUTPUT_FORMAT in
        "html")
            PYTEST_ARGS="$PYTEST_ARGS --cov-report=html"
            ;;
        "xml")
            PYTEST_ARGS="$PYTEST_ARGS --cov-report=xml"
            ;;
        "json")
            PYTEST_ARGS="$PYTEST_ARGS --cov-report=json"
            ;;
        "junit")
            PYTEST_ARGS="$PYTEST_ARGS --cov-report=xml --junit-xml=test-results/junit.xml"
            ;;
        *)
            PYTEST_ARGS="$PYTEST_ARGS --cov-report=term-missing --cov-report=html --cov-report=xml"
            ;;
    esac
else
    PYTEST_ARGS="$PYTEST_ARGS --no-cov"
fi

# Add parallel execution
if [[ $PARALLEL == true && $TEST_TYPE != "performance" ]]; then
    PYTEST_ARGS="$PYTEST_ARGS -n auto"
fi

# Add verbosity
if [[ $VERBOSE == true ]]; then
    PYTEST_ARGS="$PYTEST_ARGS -v"
else
    PYTEST_ARGS="$PYTEST_ARGS --tb=short"
fi

# Add output format specific options
case $OUTPUT_FORMAT in
    "junit")
        PYTEST_ARGS="$PYTEST_ARGS --junit-xml=test-results/junit.xml"
        ;;
    "html")
        PYTEST_ARGS="$PYTEST_ARGS --html=test-results/report.html --self-contained-html"
        ;;
    "json")
        PYTEST_ARGS="$PYTEST_ARGS --json-report --json-report-file=test-results/report.json"
        ;;
esac

# Environment-specific configurations
case $ENVIRONMENT in
    "ci")
        PYTEST_ARGS="$PYTEST_ARGS --maxfail=5 --timeout=600"
        ;;
    "development")
        PYTEST_ARGS="$PYTEST_ARGS --maxfail=1"
        ;;
    "testing")
        PYTEST_ARGS="$PYTEST_ARGS --maxfail=10"
        ;;
esac

# Display configuration
print_section "Test Configuration"
echo "Test Type: $TEST_TYPE"
echo "Environment: $ENVIRONMENT"
echo "Coverage: $COVERAGE"
echo "Parallel: $PARALLEL"
echo "Quick Mode: $QUICK"
echo "Output Format: $OUTPUT_FORMAT"
if [[ -n "$MARKERS" ]]; then
    echo "Custom Markers: $MARKERS"
fi
echo ""

# Check dependencies
print_section "Checking dependencies"

if ! command -v python &> /dev/null; then
    print_error "Python not found"
    exit 1
fi

if ! python -m pytest --version &> /dev/null; then
    print_error "pytest not found"
    echo "Install with: pip install pytest"
    exit 1
fi

# Check for required test dependencies based on test type
case $TEST_TYPE in
    "performance")
        if ! python -c "import psutil" &> /dev/null; then
            print_warning "psutil not found, some performance tests may fail"
        fi
        ;;
    "security")
        if ! command -v bandit &> /dev/null; then
            print_warning "bandit not found, install with: pip install bandit"
        fi
        ;;
esac

print_success "Dependencies check completed"

# Pre-test setup
print_section "Pre-test setup"

# Clean previous test artifacts if requested
if [[ $ENVIRONMENT == "ci" ]]; then
    print_success "Cleaning previous test artifacts"
    rm -rf htmlcov/
    rm -rf test-results/
    rm -f .coverage
    rm -f coverage.xml
    mkdir -p test-results
    mkdir -p htmlcov
fi

# Database setup for integration tests
if [[ $TEST_TYPE == "integration" || $TEST_TYPE == "all" ]]; then
    if [[ -n "${DATABASE_URL}" ]]; then
        print_success "Database configured for integration tests"
    else
        print_warning "No DATABASE_URL set, integration tests may fail"
    fi
fi

# Run tests
print_section "Running tests"

echo "Command: pytest $PYTEST_ARGS"
echo ""

# Capture start time
START_TIME=$(date +%s)

# Run pytest with built arguments
if [[ $VERBOSE == true ]]; then
    python -m pytest $PYTEST_ARGS
else
    python -m pytest $PYTEST_ARGS 2>&1 | tee test-results/output.log
fi

TEST_EXIT_CODE=$?
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Post-test reporting
echo ""
print_section "Test Results"

if [[ $TEST_EXIT_CODE -eq 0 ]]; then
    print_success "All tests passed!"
else
    print_error "Some tests failed (exit code: $TEST_EXIT_CODE)"
fi

echo "Duration: ${DURATION}s"

# Coverage reporting
if [[ $COVERAGE == true && -f "coverage.xml" ]]; then
    print_section "Coverage Summary"
    python -m coverage report --show-missing | tail -n 5
    
    if [[ -d "htmlcov" ]]; then
        echo "HTML coverage report available at: htmlcov/index.html"
    fi
fi

# Performance summary for performance tests
if [[ $TEST_TYPE == "performance" && -f "test-results/performance-summary.json" ]]; then
    print_section "Performance Summary"
    python -c "
import json
try:
    with open('test-results/performance-summary.json') as f:
        data = json.load(f)
    print(f'Total tests: {data.get(\"total_tests\", 0)}')
    print(f'Average duration: {data.get(\"avg_duration\", 0):.2f}s')
    print(f'Slowest test: {data.get(\"slowest_test\", \"N/A\")}')
except:
    print('No performance summary available')
"
fi

# Test artifacts summary
print_section "Test Artifacts"
if [[ -d "test-results" ]]; then
    echo "Test results directory:"
    ls -la test-results/
fi

if [[ -d "htmlcov" ]]; then
    echo "Coverage report: htmlcov/index.html"
fi

# Exit with the same code as pytest
exit $TEST_EXIT_CODE