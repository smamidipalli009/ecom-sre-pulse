import time, random, os
import requests
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

SERVICE = "order-service"
chaos_enabled = False

PAYMENT_URL = os.environ.get("PAYMENT_URL", "http://payment:8001")
CATALOG_URL = os.environ.get("CATALOG_URL", "http://product-catalog:8002")

REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests",
    ["service", "method", "endpoint", "status"])
REQUEST_LATENCY = Histogram("http_request_duration_seconds", "Request latency",
    ["service", "method", "endpoint"],
    buckets=[0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0])
IN_PROGRESS = Gauge("http_requests_in_progress", "In-progress requests", ["service"])
ORDERS_TOTAL = Counter("orders_created_total", "Orders created", ["status"])
ORDER_VALUE = Histogram("order_value_dollars", "Order value",
    buckets=[10, 50, 100, 250, 500, 1000, 2000])

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
        "service": SERVICE, "port": 8003,
        "endpoints": [
            "GET  /health", "GET  /metrics",
            "POST /orders", "GET  /orders/<id>",
            "POST /chaos/enable", "POST /chaos/disable"
        ]
    })

@app.route("/health")
def health():
    return jsonify({"status": "healthy", "service": SERVICE})

@app.route("/orders", methods=["POST"])
def create_order():
    global chaos_enabled
    if chaos_enabled and random.random() < 0.4:
        ORDERS_TOTAL.labels(status="failed").inc()
        return jsonify({"error": "Order service overloaded"}), 500

    data = request.get_json(silent=True) or {}
    product_id = data.get("product_id", "p001")
    amount = float(data.get("amount", random.uniform(20, 500)))

    # Call product catalog
    try:
        catalog_resp = requests.get(f"{CATALOG_URL}/products/{product_id}", timeout=2)
        if catalog_resp.status_code != 200:
            ORDERS_TOTAL.labels(status="failed").inc()
            return jsonify({"error": "Product not available"}), 503
    except requests.RequestException:
        ORDERS_TOTAL.labels(status="failed").inc()
        return jsonify({"error": "Catalog service unavailable"}), 503

    # Call payment service
    try:
        pay_resp = requests.post(f"{PAYMENT_URL}/payments",
            json={"amount": amount}, timeout=3)
        if pay_resp.status_code not in (200, 201):
            ORDERS_TOTAL.labels(status="payment_failed").inc()
            return jsonify({"error": "Payment failed"}), 402
    except requests.RequestException:
        ORDERS_TOTAL.labels(status="failed").inc()
        return jsonify({"error": "Payment service unavailable"}), 503

    ORDER_VALUE.observe(amount)
    ORDERS_TOTAL.labels(status="success").inc()
    return jsonify({
        "order_id": f"ord_{random.randint(10000,99999)}",
        "product_id": product_id,
        "amount": amount,
        "status": "confirmed"
    }), 201

@app.route("/orders/<order_id>")
def get_order(order_id):
    time.sleep(random.uniform(0.01, 0.05))
    return jsonify({"order_id": order_id, "status": "shipped"})

@app.route("/chaos/enable", methods=["POST"])
def enable_chaos():
    global chaos_enabled; chaos_enabled = True
    logger.warning("CHAOS MODE ENABLED", extra={"service": SERVICE})
    return jsonify({"chaos": "enabled"})

@app.route("/chaos/disable", methods=["POST"])
def disable_chaos():
    global chaos_enabled; chaos_enabled = False
    return jsonify({"chaos": "disabled"})

@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8003)))
