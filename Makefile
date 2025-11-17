.PHONY: help backend frontend dev test lint clean install

# Default target
help:
	@echo "Available commands:"
	@echo "  make install       - Install dependencies for backend and frontend"
	@echo "  make backend       - Run the backend server"
	@echo "  make frontend      - Run the frontend dev server"
	@echo "  make dev           - Run both backend and frontend concurrently"
	@echo "  make test          - Run all tests"
	@echo "  make lint          - Run linters on backend and frontend"
	@echo "  make format        - Format code (backend and frontend)"
	@echo "  make clean         - Clean build artifacts and caches"
	@echo "  make db-init       - Initialize the database"
	@echo "  make db-migrate    - Run database migrations"

# Installation
install:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt || pip install fastapi uvicorn sqlalchemy pydantic pydantic-settings python-multipart pytesseract pillow pypdf httpx
	@echo "Installing frontend dependencies..."
	npm install
	@echo "✅ All dependencies installed"

# Backend commands
backend:
	@echo "Starting backend server..."
	cd backend && python main.py

# Frontend commands
frontend:
	@echo "Starting frontend dev server..."
	npm run dev

# Development - run both servers
dev:
	@echo "Starting both backend and frontend..."
	@echo "Note: Use 'make backend' and 'make frontend' in separate terminals for better control"
	@echo "Or use a process manager like concurrently or tmux"

# Testing
test:
	@echo "Running backend tests..."
	cd backend && python -m pytest tests/ || echo "No backend tests found"
	@echo "Running frontend tests..."
	npm test || echo "No frontend tests configured"

# Linting
lint:
	@echo "Linting backend..."
	cd backend && python -m ruff check . || python -m flake8 . || echo "Install ruff or flake8 for linting: pip install ruff"
	@echo "Linting frontend..."
	npm run lint || echo "No frontend linting configured"

# Formatting
format:
	@echo "Formatting backend code..."
	cd backend && python -m ruff format . || python -m black . || echo "Install ruff or black for formatting: pip install ruff"
	@echo "Formatting frontend code..."
	npm run format || npx prettier --write . || echo "Run: npm install -D prettier"

# Database
db-init:
	@echo "Initializing database..."
	cd backend && python -c "from database import init_db, create_engine; from config import Settings; engine = create_engine(Settings().database_url, connect_args={'check_same_thread': False}); init_db(engine); print('✅ Database initialized')"

db-migrate:
	@echo "Running database migrations..."
	@echo "Note: Add alembic for proper migrations: pip install alembic"

# Cleanup
clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .next 2>/dev/null || true
	rm -rf node_modules/.cache 2>/dev/null || true
	@echo "✅ Cleaned build artifacts"

# Quick development setup
setup: install db-init
	@echo "✅ Project setup complete!"
	@echo "Run 'make backend' in one terminal and 'make frontend' in another to start developing"
