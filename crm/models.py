"""Imports for models"""

from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator


class Customer(models.Model):
    """Customer model definition"""

    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["email"]),
        ]

    def __str__(self):
        return f"{self.name} {self.email}"


class Product(models.Model):
    """Product model definition"""

    name = models.CharField(max_length=100)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=Decimal("0.00"),
    )
    stock = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ${self.price}"


# pylint: disable=no-member
class Order(models.Model):
    """Order model definition"""

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="orders",
    )
    products = models.ManyToManyField(
        Product,
        related_name="orders",
    )
    order_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    class Meta:
        ordering = ["-order_date"]
        indexes = [
            models.Index(fields=["order_date"]),
            models.Index(fields=["customer", "order_date"]),
        ]

    def __str__(self):
        return f"Order {self.id} - {self.customer.name} - {self.total_amount}"

    def calculate_total(self):
        """Calculate and update the total amount based on associated products"""
        total = sum(product.price for product in self.products.all())
        self.total_amount = total
        return total
