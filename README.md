# ecom-sre-pulse

A simulated e-commerce platform built to practice real-world SRE work.

The project mimics a production microservices environment with three independent services — Payment, Product Catalog, and Order — each running in Docker. The goal is to observe, monitor, and respond to failures the way an SRE would on a real team.

---

## Services

| Service         | Port | Responsibility                        |
|-----------------|------|---------------------------------------|
| Payment         | 8001 | Process and track payments            |
| Product Catalog | 8002 | Manage and serve product listings     |
| Order Service   | 8003 | Create orders, calls Payment + Catalog|

Each service is an independent Python/Flask app running in its own Docker container.

---

## Run the project

```bash
docker compose up -d
```

---

## Tech Stack

- **Python / Flask** — microservices
- **Docker Compose** — container orchestration
- **Prometheus** — metrics collection
- **Grafana** — dashboards
- **Loki** — log aggregation
- **Alertmanager** — alerting
