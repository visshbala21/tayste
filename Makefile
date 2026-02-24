.PHONY: dev stop jobs-ingest jobs-score jobs-discover jobs-llm demo seed clean

# Start all services
dev:
	docker compose up --build -d db backend frontend
	@echo "Tayste is running:"
	@echo "  Frontend: http://localhost:3000"
	@echo "  Backend:  http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"

# Stop all services
stop:
	docker compose down

# Run ingestion job (roster → snapshots)
jobs-ingest:
	docker compose run --rm jobs app.jobs.ingest

# Run discovery job (find new candidates)
jobs-discover:
	docker compose run --rm jobs app.jobs.discover

# Run scoring job (features → ranking)
jobs-score:
	docker compose run --rm jobs app.jobs.score

# Run LLM enrichment job
jobs-llm:
	docker compose run --rm jobs app.jobs.llm_enrich

# Full demo pipeline
demo:
	@echo "=== Tayste Demo Pipeline ==="
	@echo "Step 1: Starting services..."
	docker compose up --build -d db backend frontend
	@echo "Waiting for services to be ready..."
	@sleep 10
	@echo "Step 2: Seeding demo data..."
	docker compose run --rm jobs app.jobs.seed_demo
	@echo "Step 3: Running ingestion..."
	docker compose run --rm jobs app.jobs.ingest
	@echo "Step 4: Running discovery..."
	docker compose run --rm jobs app.jobs.discover
	@echo "Step 5: Running scoring..."
	docker compose run --rm jobs app.jobs.score
	@echo "Step 6: Running LLM enrichment..."
	docker compose run --rm jobs app.jobs.llm_enrich
	@echo "=== Demo Ready ==="
	@echo "  Frontend: http://localhost:3000"
	@echo "  API Docs: http://localhost:8000/docs"

# Seed demo data without full pipeline
seed:
	docker compose run --rm jobs app.jobs.seed_demo

# Clean everything
clean:
	docker compose down -v
	docker compose rm -f
