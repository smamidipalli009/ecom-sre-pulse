import time, random, os
from flask import Flask, jsonify, request
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import logging
from pythonjsonlogger import jsonlogger

app = Flask(__name__)

logger = logging.getLogger()
handler = logging.StreamHandler()
handler.setFormatter(jsonlogger.JsonFormatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

SERVICE = "payment"
chaos_enabled = False

REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests",
    ["service", "method", "endpoint", "status"])
REQUEST_LATENCY = Histogram("http_request_duration_seconds", "Request latency",
    ["service", "method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0])
IN_PROGRESS = Gauge("http_requests_in_progress", "In-progress requests", ["service"])
PAYMENTS_TOTAL = Counter("payments_processed_total", "Payments processed", ["status"])
PAYMENT_AMOUNT = Histogram("payment_amount_dollars", "Payment amount",
    buckets=[10, 50, 100, 250, 500, 1000, 5000])

@app.before_request
def before():
    request.start_time = time.time()
    IN_PROGRESS.labels(service=SERVICE).inc()

@app.after_request
def after(response):
    dur = time.time() - request.start_time
    REQUEST_LATENCY.labels(service=SERVICE, method=request.method, endpoint=request.path).observe(dur)
    REQUEST_COUNT.labels(service=SERVICE, method=request.method,
        endpoint=request.path, status=response.status_code).inc()
    IN_PROGRESS.labels(service=SERVICE).dec()
    logger.info("request", extra={"service": SERVICE, "method": request.method,
        "path": request.path, "status": response.status_code, "duration_ms": round(dur * 1000, 2)})
    return response

@app.route("/")
def index():
    return jsonify({
        "service": SERVICE, "port": 8001,
        "endpoints": [
            "GET  /health", "GET  /metrics",
            "POST /payments", "GET  /payments/<id>",
            "POST /chaos/enable", "POST /chaos/disable"
        ]
    })

@app.route("/health")
def health():
    return jsonify({"status": "healthy", "service": SERVICE})

@app.route("/payments", methods=["POST"])
def process_payment():
    global chaos_enabled
    if chaos_enabled and random.random() < 0.6:
        PAYMENTS_TOTAL.labels(status="failed").inc()
        return jsonify({"error": "Payment gateway timeout"}), 500

    time.sleep(random.expovariate(1 / 0.25))  # mean ~250ms

    data = request.get_json(silent=True) or {}
    amount = float(data.get("amount", random.uniform(10, 1000)))
    PAYMENT_AMOUNT.observe(amount)

    if random.random() < 0.015:  # ~1.5% natural error rate
        PAYMENTS_TOTAL.labels(status="declined").inc()
        return jsonify({"error": "Card declined"}), 402

    PAYMENTS_TOTAL.labels(status="success").inc()
    return jsonify({"payment_id": f"pay_{random.randint(10000,99999)}",
        "amount": amount, "status": "processed"}), 201

@app.route("/payments/<payment_id>")
def get_payment(payment_id):
    time.sleep(random.uniform(0.01, 0.05))
    return jsonify({"payment_id": payment_id, "status": "completed"})

@app.route("/chaos/enable", methods=["POST"])
def enable_chaos():
    global chaos_enabled; chaos_enabled = True
    logger.warning("CHAOS MODE ENABLED", extra={"service": SERVICE})
    return jsonify({"chaos": "enabled"})

@app.route("/chaos/disable", methods=["POST"])
def disable_chaos():
    global chaos_enabled; chaos_enabled = False
    logger.info("chaos disabled", extra={"service": SERVICE})
    return jsonify({"chaos": "disabled"})

@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8001)))
