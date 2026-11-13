"""
Load generator for ecom-sre-pulse.
Run: locust -f locustfile.py --host http://localhost --headless -u 20 -r 2 --run-time 5m
"""
import random
from locust import HttpUser, task, between

PRODUCT_IDS = ["p001", "p002", "p003", "p004", "p005"]

class PaymentUser(HttpUser):
    host = "http://payment:8001"
    wait_time = between(0.5, 2)

    @task(3)
    def process_payment(self):
        self.client.post("/payments", json={
            "amount": round(random.uniform(10, 1000), 2)
        })

    @task(1)
    def get_payment(self):
        self.client.get(f"/payments/pay_{random.randint(10000,99999)}")

    @task(1)
    def health_check(self):
        self.client.get("/health")


class CatalogUser(HttpUser):
    host = "http://product-catalog:8002"
    wait_time = between(0.2, 1)

    @task(4)
    def list_products(self):
        self.client.get("/products")

    @task(3)
    def get_product(self):
        self.client.get(f"/products/{random.choice(PRODUCT_IDS)}")

    @task(2)
    def search(self):
        self.client.get("/products/search?q=laptop")

    @task(1)
    def health_check(self):
        self.client.get("/health")


class OrderUser(HttpUser):
    host = "http://order-service:8003"
    wait_time = between(1, 3)

    @task(3)
    def create_order(self):
        self.client.post("/orders", json={
            "product_id": random.choice(PRODUCT_IDS),
            "amount": round(random.uniform(20, 500), 2)
        })

    @task(1)
    def get_order(self):
        self.client.get(f"/orders/ord_{random.randint(10000,99999)}")

    @task(1)
    def health_check(self):
        self.client.get("/health")
