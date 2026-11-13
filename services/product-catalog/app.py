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

SERVICE = "product-catalog"
chaos_enabled = False

REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests",
    ["service", "method", "endpoint", "status"])
REQUEST_LATENCY = Histogram("http_request_duration_seconds", "Request latency",
    ["service", "method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5])
IN_PROGRESS = Gauge("http_requests_in_progress", "In-progress requests", ["service"])
PRODUCTS_VIEWED = Counter("products_viewed_total", "Products viewed", ["category"])
SEARCH_QUERIES = Counter("catalog_searches_total", "Catalog searches")

SAMPLE_PRODUCTS = [
    {"id": "p001", "name": "Laptop Pro", "category": "electronics", "price": 1299.99},
    {"id": "p002", "name": "Running Shoes", "category": "sports", "price": 89.99},
    {"id": "p003", "name": "Coffee Maker", "category": "kitchen", "price": 49.99},
    {"id": "p004", "name": "Wireless Mouse", "category": "electronics", "price": 29.99},
    {"id": "p005", "name": "Yoga Mat", "category": "sports", "price": 24.99},
]

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
        "service": SERVICE, "port": 8002,
        "endpoints": [
            "GET  /health", "GET  /metrics",
            "GET  /products", "GET  /products/<id>",
            "GET  /products/search?q=<query>",
            "POST /chaos/enable", "POST /chaos/disable"
        ]
    })

@app.route("/health")
def health():
    return jsonify({"status": "healthy", "service": SERVICE})

@app.route("/products")
def list_products():
    global chaos_enabled
    if chaos_enabled and random.random() < 0.4:
        return jsonify({"error": "Database connection timeout"}), 503

    time.sleep(random.uniform(0.05, 0.15))
    category = request.args.get("category")
    products = [p for p in SAMPLE_PRODUCTS if not category or p["category"] == category]
    return jsonify({"products": products, "total": len(products)})

@app.route("/products/<product_id>")
def get_product(product_id):
    global chaos_enabled
    if chaos_enabled and random.random() < 0.3:
        return jsonify({"error": "Service unavailable"}), 503

    time.sleep(random.uniform(0.02, 0.08))
    product = next((p for p in SAMPLE_PRODUCTS if p["id"] == product_id), None)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    PRODUCTS_VIEWED.labels(category=product["category"]).inc()
    return jsonify(product)

@app.route("/products/search")
def search_products():
    time.sleep(random.uniform(0.1, 0.3))
    SEARCH_QUERIES.inc()
    q = request.args.get("q", "").lower()
    results = [p for p in SAMPLE_PRODUCTS if q in p["name"].lower()] if q else SAMPLE_PRODUCTS
    return jsonify({"results": results})

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
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8002)))
