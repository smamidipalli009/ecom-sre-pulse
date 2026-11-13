# ecom-sre-pulse

A simulated e-commerce platform built to practice real-world SRE work.

The project mimics a production microservices environment with three independent services: Payment, Product Catalog, and Order, each running in Docker. The goal is to observe, monitor, and respond to failures the way an SRE would on a real team.

## Services

| Service         | Port | Responsibility                         |
|-----------------|------|----------------------------------------|
| Payment         | 8001 | Process and track payments             |
| Product Catalog | 8002 | Manage and serve product listings      |
| Order Service   | 8003 | Create orders, calls Payment + Catalog |

Each service is an independent Python/Flask app running in its own Docker container.

## Run the project

```bash
docker compose up -d
```

## Services Running

All 8 containers start with a single command. 3 microservices + full observability stack.

```bash
docker ps --filter name=ecom --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

![Services Running](docs/screenshots/services-up.png)

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

## Prometheus — All Targets UP

Prometheus scrapes metrics from all 3 services every 15 seconds.

```bash
# View targets at http://localhost:9090/targets
```

![Prometheus Targets](docs/screenshots/prometheus-targets.png)

## Grafana Dashboards

Dashboards available at `http://localhost:4000`.

One dashboard per service, each covering the 4 Golden Signals: Traffic, Latency, Errors, and Saturation.

![Grafana Dashboards](docs/screenshots/grafana-dashboards.png)

## Load Testing

Load generator runs inside Docker using [Locust](https://locust.io). Three user classes simulate realistic traffic across all 3 services simultaneously.

```bash
docker compose --profile load up -d load-generator
```

Then open `http://localhost:8089`, set **Users** to 20, **Ramp up** to 5 per second, and click **Start**.

Watch RPS, latency, and error rate update live in Grafana.

![Locust](docs/screenshots/locust.png)

## Chaos Engineering

Each service has `/chaos/enable` and `/chaos/disable` endpoints. When enabled, 60% of requests return 500 errors, simulating a degraded service.

```bash
curl -X POST http://localhost:8001/chaos/enable

curl -X POST http://localhost:8001/chaos/disable
```


## Tech Stack

| Layer        | Tool                           |
|--------------|--------------------------------|
| Services     | Python 3.12 / Flask            |
| Metrics      | Prometheus + prometheus-client |
| Dashboards   | Grafana                        |
| Logs         | Loki + Promtail                |
| Alerting     | Alertmanager                   |
| Container    | Docker Compose                 |
