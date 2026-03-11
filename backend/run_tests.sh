#!/bin/bash

# Run tests in the backend container
echo "Running backend tests..."
python -m pytest tests/ -v --tb=short

# Run with coverage
echo ""
echo "Running tests with coverage..."
python -m pytest tests/ --cov=. --cov-report=html --cov-report=term
