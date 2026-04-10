.PHONY: install install-dev run test coverage lint clean

# Install runtime dependencies
install:
	pip install -r requirements.txt

# Install development dependencies
install-dev:
	pip install -r requirements-dev.txt

# Run the Telegram bot
run:
	PYTHONPATH=src python -m yoga_chatbot.bot.bot

# Run all tests
test:
	PYTHONPATH=src pytest tests/ -v

# Run tests with coverage report
coverage:
	PYTHONPATH=src pytest tests/ -v --cov=src/yoga_chatbot --cov-report=term-missing --cov-report=html

# Augment training data
augment:
	PYTHONPATH=src python scripts/augment_data.py \
		--input data/raw/intents_diy_full.json \
		--output data/processed/intents_augmented.json \
		--target 60

# Remove Python cache files
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage
