"""
Load generator for ecom-sre-pulse.
Targets all 3 services using internal Docker hostnames.
"""
import random
from locust import HttpUser, task, between

PAYMENT_HOST  = "http://payment:8001"
CATALOG_HOST  = "http://product-catalog:8002"
ORDER_HOST    = "http://order-service:8003"
PRODUCT_IDS   = ["p001", "p002", "p003", "p004", "p005"]


class PaymentUser(HttpUser):
    host = PAYMENT_HOST
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
    host = CATALOG_HOST
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
    host = ORDER_HOST
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
