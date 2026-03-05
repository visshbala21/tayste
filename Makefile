.PHONY: dev stop jobs-ingest jobs-score jobs-discover jobs-llm jobs-sc-discover jobs-sc-enrich jobs-spotify-graph jobs-cultural-collect jobs-cultural-interpret demo seed clean

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

# Run legacy discovery job (find new candidates via YouTube/Spotify search)
jobs-discover:
	docker compose run --rm jobs app.jobs.discover

# Run scoring job (features → ranking)
jobs-score:
	docker compose run --rm jobs app.jobs.score

# Run LLM enrichment job
jobs-llm:
	docker compose run --rm jobs app.jobs.llm_enrich

# Run Spotify related-artists graph expansion (primary discovery)
jobs-spotify-graph:
	docker compose run --rm jobs app.jobs.pull_spotify_graph

# Run Soundcharts candidate discovery + cross-referencing
jobs-sc-discover:
	docker compose run --rm jobs app.jobs.pull_soundcharts_candidates

# Run Soundcharts enrichment (time-series stats)
jobs-sc-enrich:
	docker compose run --rm jobs app.jobs.enrich_soundcharts_artists

# Collect cultural signals (YouTube comments + Reddit mentions)
jobs-cultural-collect:
	docker compose run --rm jobs app.jobs.collect_cultural_signals

# Run LLM cultural interpretation (post-scoring, for UI)
jobs-cultural-interpret:
	docker compose run --rm jobs app.jobs.interpret_cultural_signals

# Full demo pipeline
demo:
	@echo "=== Tayste Demo Pipeline ==="
	@echo "Step 1: Starting services..."
	docker compose up --build -d db backend frontend
	@echo "Waiting for services to be ready..."
	@sleep 10
	@echo "Step 2: Seeding demo data..."
	docker compose run --rm jobs app.jobs.seed_demo
	@echo "Step 3: Soundcharts cross-referencing..."
	docker compose run --rm jobs app.jobs.pull_soundcharts_candidates
	@echo "Step 4: Related-artist graph discovery..."
	docker compose run --rm jobs app.jobs.pull_spotify_graph
	@echo "Step 5: Soundcharts enrichment..."
	docker compose run --rm jobs app.jobs.enrich_soundcharts_artists
	@echo "Step 6: Collecting cultural signals..."
	docker compose run --rm jobs app.jobs.collect_cultural_signals
	@echo "Step 7: Running supplemental ingestion..."
	docker compose run --rm jobs app.jobs.ingest
	@echo "Step 8: Running scoring..."
	docker compose run --rm jobs app.jobs.score
	@echo "Step 9: Running cultural interpretation..."
	docker compose run --rm jobs app.jobs.interpret_cultural_signals
	@echo "Step 10: Running LLM enrichment..."
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
