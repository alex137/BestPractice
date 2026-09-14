# Fixture stub -- part of the demo-consumer-repo phase-3 simulation fixture.
# Not a real application; exists so this fixture has its own plausible file
# tree for scenario generation, distinct from BestPractice's own.

class Order:
    def __init__(self, order_id, customer_id, total_cents):
        self.order_id = order_id
        self.customer_id = customer_id
        self.total_cents = total_cents
