# ecom-sre-pulse

A simulated e-commerce platform built to practice real-world SRE work.

The project mimics a production microservices environment with three independent services — Payment, Product Catalog, and Order — each running in Docker. The goal is to observe, monitor, and respond to failures the way an SRE would on a real team.

---

## Services

| Service         | Port | Responsibility                         |
|-----------------|------|----------------------------------------|
| Payment         | 8001 | Process and track payments             |
| Product Catalog | 8002 | Manage and serve product listings      |
| Order Service   | 8003 | Create orders, calls Payment + Catalog |

Each service is an independent Python/Flask app running in its own Docker container.

---

## Run the project

```bash
docker compose up -d
```

---

## Services Running

All 8 containers start with a single command — 3 microservices + full observability stack.

```bash
docker ps --filter name=ecom --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

![Services Running](docs/screenshots/services-up.png)

---

### Health checks

Each service exposes a `/health` endpoint to confirm it is up and responding.

```bash
curl http://localhost:8001/health
```
![Payment Health](docs/screenshots/health-checks-payment.png)

```bash
curl http://localhost:8002/health
```
![Product Catalog Health](docs/screenshots/health-checks-product.png)

```bash
curl http://localhost:8003/health
```
![Order Service Health](docs/screenshots/health-checks-order.png)

---

## Prometheus — All Targets UP

Prometheus scrapes metrics from all 3 services every 15 seconds.

```bash
# View targets at http://localhost:9090/targets
```

![Prometheus Targets](docs/screenshots/prometheus-targets.png)

---

## Grafana

Dashboards available at `http://localhost:4000` (login: `admin` / `admin`).

The `ecom-sre-pulse` folder is provisioned and ready for dashboards.

![Grafana](docs/screenshots/grafana-home.png)

---

## Tech Stack

| Layer        | Tool                           |
|--------------|--------------------------------|
| Services     | Python 3.12 / Flask            |
| Metrics      | Prometheus + prometheus-client |
| Dashboards   | Grafana                        |
| Logs         | Loki + Promtail                |
| Alerting     | Alertmanager                   |
| Container    | Docker Compose                 |
