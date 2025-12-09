#!/bin/bash
# Static analysis script to detect logging violations in core Host and Enclave components.
# This script uses ripgrep to enforce rules regarding sensitive data logging and direct logging module usage.

set -euo pipefail

HOST_DIR="src/signal_assistant/host"
ENCLAVE_DIR="src/signal_assistant/enclave"
TEST_DIR="tests" # Directory containing test files
APP_ROOT="src/signal_assistant" # Root of the application source

VIOLATIONS_FOUND=0

echo "Running static analysis for logging violations..."

# Rule: Block direct usage of the standard 'logging' module functions
# This enforces the use of secure_logging and logging_client interfaces.
# It looks for 'import logging' or 'logging.' but excludes the interface files themselves AND test files.
# It also excludes main.py, simulate.py, and mocks.py as they are entrypoints or utility scripts that might legitimately
# configure basic logging for the application startup or mock scenarios.
echo "Checking for direct 'logging' module usage in core modules..."
if rg -q "\bimport logging\b|\blogging\." "${APP_ROOT}" -t py \
    --glob "!${ENCLAVE_DIR}/secure_logging.py" \
    --glob "!${HOST_DIR}/logging_client.py" \
    --glob "!${TEST_DIR}/**" \
    --glob "!${APP_ROOT}/main.py" \
    --glob "!${APP_ROOT}/simulate.py" \
    --glob "!${APP_ROOT}/mocks.py"; then
    echo "ERROR: Direct 'logging' module usage found. Please use secure_logging/logging_client interfaces."
    rg "\bimport logging\b|\blogging\." "${APP_ROOT}" -t py \
       --glob "!${ENCLAVE_DIR}/secure_logging.py" \
       --glob "!${HOST_DIR}/logging_client.py" \
       --glob "!${TEST_DIR}/**" \
       --glob "!${APP_ROOT}/main.py" \
       --glob "!${APP_ROOT}/simulate.py" \
       --glob "!${APP_ROOT}/mocks.py" || true
    VIOLATIONS_FOUND=1
fi

if [ "$VIOLATIONS_FOUND" -eq 0 ]; then
    echo "Static analysis passed. No logging violations found."
else
    echo "Static analysis FAILED: Logging violations detected!"
    exit 1
fi
