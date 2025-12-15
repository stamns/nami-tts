.PHONY: help install setup dev-backend dev-frontend test smoke-test clean clean-cache clean-venv

# Cross-platform Makefile for nami-tts local development
# 
# Unix/Linux/macOS: Works out of the box with python3
# Windows: Use Git Bash, WSL, or set PYTHON=python (e.g., `make PYTHON=python install`)
#          On Windows, paths use forward slashes which work in most shells.

# Python command (use python3 on Unix, python on Windows)
PYTHON ?= python3

# Configuration
BACKEND_PORT ?= 5001
FRONTEND_PORT ?= 8000

# Load PORT from .env if it exists
-include .env
export

ifdef PORT
	BACKEND_PORT := $(PORT)
endif

# Default target
help:
	@echo "==================================================================="
	@echo "  nami-tts Local Development Makefile"
	@echo "==================================================================="
	@echo ""
	@echo "Available targets:"
	@echo "  make help            - Show this help message"
	@echo "  make install         - Create virtual environment and install dependencies"
	@echo "  make setup           - Alias for install"
	@echo "  make dev-backend     - Run Flask backend server (port: $(BACKEND_PORT))"
	@echo "  make dev-frontend    - Serve static frontend (port: $(FRONTEND_PORT))"
	@echo "  make test            - Run smoke tests (test_diagnosis.py)"
	@echo "  make smoke-test      - Alias for test"
	@echo "  make clean           - Remove all cache and build artifacts"
	@echo "  make clean-cache     - Remove cache directory only"
	@echo "  make clean-venv      - Remove virtual environment"
	@echo ""
	@echo "Environment variables:"
	@echo "  BACKEND_PORT         - Backend server port (default: from .env or 5001)"
	@echo "  FRONTEND_PORT        - Frontend server port (default: 8000)"
	@echo ""
	@echo "Quick start:"
	@echo "  1. Copy .env.example to .env and configure your settings"
	@echo "  2. make install"
	@echo "  3. Open two terminals:"
	@echo "     - Terminal 1: make dev-backend"
	@echo "     - Terminal 2: make dev-frontend"
	@echo "  4. Visit http://localhost:$(FRONTEND_PORT)"
	@echo ""

# Create virtual environment
.venv:
	@echo "Creating virtual environment..."
	@$(PYTHON) -m venv .venv
	@echo "✅ Virtual environment created!"

# Install dependencies
install: .venv
	@echo "Installing Python dependencies..."
	@.venv/bin/pip install --upgrade pip
	@.venv/bin/pip install -r requirements.txt
	@echo ""
	@echo "✅ Dependencies installed successfully!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Copy .env.example to .env: cp .env.example .env"
	@echo "  2. Edit .env and set your configuration"
	@echo "  3. Run backend: make dev-backend"
	@echo "  4. Run frontend: make dev-frontend"

setup: install

# Run Flask backend server
dev-backend: .venv
	@if [ ! -f .env ]; then \
		echo "⚠️  Warning: .env file not found. Creating from .env.example..."; \
		cp .env.example .env; \
		echo "✅ Created .env file. Please review and update your settings."; \
		echo ""; \
	fi
	@echo "Starting Flask backend on port $(BACKEND_PORT)..."
	@echo "Press Ctrl+C to stop"
	@echo ""
	@.venv/bin/python -m flask --app backend.app run --host=0.0.0.0 --port=$(BACKEND_PORT)

# Serve static frontend
dev-frontend: .venv
	@echo "Starting frontend development server on port $(FRONTEND_PORT)..."
	@echo "Visit: http://localhost:$(FRONTEND_PORT)"
	@echo "Press Ctrl+C to stop"
	@echo ""
	@cd frontend && ../.venv/bin/python -m http.server $(FRONTEND_PORT)

# Run smoke tests
test: .venv
	@echo "Running smoke tests..."
	@echo ""
	@if [ ! -f .env ]; then \
		echo "⚠️  Warning: .env file not found. Using .env.example values..."; \
	fi
	@.venv/bin/python test_diagnosis.py

smoke-test: test

# Clean all artifacts
clean: clean-cache
	@echo "Cleaning Python cache files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup complete!"

# Clean cache directory
clean-cache:
	@echo "Cleaning cache directory..."
	@rm -rf cache 2>/dev/null || true
	@rm -rf /tmp/cache 2>/dev/null || true
	@echo "✅ Cache cleaned!"

# Remove virtual environment
clean-venv:
	@echo "Removing virtual environment..."
	@rm -rf .venv 2>/dev/null || true
	@echo "✅ Virtual environment removed!"
	@echo "Run 'make install' to recreate it."
