"""Imports for customer filters"""

from datetime import timedelta
from django.utils import timezone
from django.db.models import Q
import django_filters
from .models import Customer, Product, Order


# pylint: disable=unused-argument
class CustomerFilter(django_filters.FilterSet):
    """
    Filter customers by name, email, creation date, and phone pattern.
    Supports case-insensitive partial matching and date ranges.
    """

    # Case-insensitive partial match for name
    name = django_filters.CharFilter(
        field_name="name", lookup_expr="icontains", label="Name (partial match)"
    )

    # Case-insensitive partial match for email
    email = django_filters.CharFilter(
        field_name="email", lookup_expr="icontains", label="Email (partial match)"
    )

    # Date range filters for created_at
    created_at_gte = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gte", label="Created after"
    )

    created_at_lte = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte", label="Created before"
    )

    # Custom filter: Phone number pattern matching
    phone_pattern = django_filters.CharFilter(
        method="filter_phone_pattern", label="Phone pattern (e.g., +1 for US numbers)"
    )

    def filter_phone_pattern(self, queryset, name, value):
        """
        Custom filter to match phone numbers starting with a specific pattern.
        Example: phone_pattern="+1" matches all US phone numbers.
        """
        if value:
            return queryset.filter(phone__istartswith=value)
        return queryset

    class Meta:
        model = Customer
        fields = {
            "name": ["exact", "icontains"],
            "email": ["exact", "icontains"],
            "created_at": ["gte", "lte", "exact"],
        }


class ProductFilter(django_filters.FilterSet):
    """
    Filter products by name, price range, and stock levels.
    Includes custom low stock filter.
    """

    # Case-insensitive partial match for name
    name = django_filters.CharFilter(
        field_name="name", lookup_expr="icontains", label="Product name (partial match)"
    )

    # Price range filters
    price_gte = django_filters.NumberFilter(
        field_name="price", lookup_expr="gte", label="Minimum price"
    )

    price_lte = django_filters.NumberFilter(
        field_name="price", lookup_expr="lte", label="Maximum price"
    )

    # Stock range filters
    stock_gte = django_filters.NumberFilter(
        field_name="stock", lookup_expr="gte", label="Minimum stock"
    )

    stock_lte = django_filters.NumberFilter(
        field_name="stock", lookup_expr="lte", label="Maximum stock"
    )

    # Exact stock match
    stock = django_filters.NumberFilter(
        field_name="stock", lookup_expr="exact", label="Exact stock"
    )

    # Custom filter: Low stock (stock < 10)
    low_stock = django_filters.BooleanFilter(
        method="filter_low_stock", label="Low stock (< 10 units)"
    )

    def filter_low_stock(self, queryset, name, value):
        """
        Filter products with low stock (less than 10 units).
        Usage: lowStock: true
        """
        if value:
            return queryset.filter(stock__lt=10)
        return queryset

    class Meta:
        model = Product
        fields = {
            "name": ["exact", "icontains"],
            "price": ["exact", "gte", "lte"],
            "stock": ["exact", "gte", "lte"],
        }


class OrderFilter(django_filters.FilterSet):
    """
    Filter orders by total amount, order date, customer, and products.
    Supports related field lookups and custom product ID filtering.
    """

    # Total amount range filters
    totalAmountGte = django_filters.NumberFilter(
        field_name="total_amount", lookup_expr="gte", label="Minimum total amount"
    )

    totalAmountLte= django_filters.NumberFilter(
        field_name="total_amount", lookup_expr="lte", label="Maximum total amount"
    )

    # Order date range filters
    orderDateGte = django_filters.DateTimeFilter(
        field_name="order_date", lookup_expr="gte", label="Order date from"
    )

    orderDateLte = django_filters.DateTimeFilter(
        field_name="order_date", lookup_expr="lte", label="Order date to"
    )

    # Filter by customer name (related field lookup)
    customer_name = django_filters.CharFilter(
        field_name="customer__name",
        lookup_expr="icontains",
        label="Customer name (partial match)",
    )

    # Filter by customer email (related field lookup)
    customer_email = django_filters.CharFilter(
        field_name="customer__email",
        lookup_expr="icontains",
        label="Customer email (partial match)",
    )

    # Filter by product name (related field lookup through many-to-many)
    product_name = django_filters.CharFilter(
        field_name="products__name",
        lookup_expr="icontains",
        label="Product name (partial match)",
        distinct=True,
    )

    # Custom filter: Filter by specific product ID
    product_id = django_filters.NumberFilter(
        method="filter_product_id", label="Specific product ID"
    )

    # Custom filter: Filter orders containing multiple products
    product_ids = django_filters.CharFilter(
        method="filter_product_ids", label="Multiple product IDs (comma-separated)"
    )

    def filter_product_id(self, queryset, name, value):
        """
        Filter orders that include a specific product ID.
        Usage: productId: "1"
        """
        if value:
            return queryset.filter(products__id=value).distinct()
        return queryset

    def filter_product_ids(self, queryset, name, value):
        """
        Filter orders that include any of the specified product IDs.
        Usage: productIds: "1,2,3"
        """
        if value:
            try:
                ids = [int(id.strip()) for id in value.split(",")]
                return queryset.filter(products__id__in=ids).distinct()
            except ValueError:
                return queryset
        return queryset

    class Meta:
        model = Order
        fields = {
            "total_amount": ["exact", "gte", "lte"],
            "order_date": ["exact", "gte", "lte"],
        }


class AdvancedCustomerFilter(django_filters.FilterSet):
    """
    Advanced customer filtering with additional search capabilities.
    """

    # Search across multiple fields
    search = django_filters.CharFilter(
        method="filter_search", label="Search (name or email)"
    )

    # Filter by has orders
    has_orders = django_filters.BooleanFilter(
        method="filter_has_orders", label="Has placed orders"
    )

    def filter_search(self, queryset, name, value):
        """
        Search customers by name or email.
        Usage: search: "alice"
        """
        if value:
            return queryset.filter(Q(name__icontains=value) | Q(email__icontains=value))
        return queryset

    def filter_has_orders(self, queryset, name, value):
        """
        Filter customers who have placed orders.
        Usage: hasOrders: true
        """
        if value:
            return queryset.filter(orders__isnull=False).distinct()
        else:
            return queryset.filter(orders__isnull=True)
        return queryset

    class Meta:
        model = Customer
        fields = []


class AdvancedProductFilter(django_filters.FilterSet):
    """
    Advanced product filtering with additional search capabilities.
    """

    # Search product name
    search = django_filters.CharFilter(
        field_name="name", lookup_expr="icontains", label="Search product name"
    )

    # Filter by in stock
    in_stock = django_filters.BooleanFilter(method="filter_in_stock", label="In stock")

    # Filter by price category
    price_category = django_filters.ChoiceFilter(
        method="filter_price_category",
        choices=[
            ("budget", "Budget (< $100)"),
            ("mid", "Mid-range ($100-$500)"),
            ("premium", "Premium ($500-$1000)"),
            ("luxury", "Luxury (> $1000)"),
        ],
        label="Price category",
    )

    def filter_in_stock(self, queryset, name, value):
        """
        Filter products that are in stock (stock > 0).
        Usage: inStock: true
        """
        if value:
            return queryset.filter(stock__gt=0)
        else:
            return queryset.filter(stock=0)
        return queryset

    def filter_price_category(self, queryset, name, value):
        """
        Filter products by price category.
        Usage: priceCategory: "premium"
        """
        if value == "budget":
            return queryset.filter(price__lt=100)
        elif value == "mid":
            return queryset.filter(price__gte=100, price__lt=500)
        elif value == "premium":
            return queryset.filter(price__gte=500, price__lte=1000)
        elif value == "luxury":
            return queryset.filter(price__gt=1000)
        return queryset

    class Meta:
        model = Product
        fields = []


class AdvancedOrderFilter(django_filters.FilterSet):
    """
    Advanced order filtering with additional search capabilities.
    """

    # Filter by date range presets
    date_range = django_filters.ChoiceFilter(
        method="filter_date_range",
        choices=[
            ("today", "Today"),
            ("week", "This week"),
            ("month", "This month"),
            ("year", "This year"),
        ],
        label="Date range preset",
    )

    # Filter by order value category
    value_category = django_filters.ChoiceFilter(
        method="filter_value_category",
        choices=[
            ("small", "Small (< $100)"),
            ("medium", "Medium ($100-$500)"),
            ("large", "Large ($500-$1000)"),
            ("xlarge", "Extra Large (> $1000)"),
        ],
        label="Order value category",
    )

    def filter_date_range(self, queryset, name, value):
        """
        Filter orders by date range presets.
        Usage: dateRange: "week"
        """

        now = timezone.now()

        if value == "today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            return queryset.filter(order_date__gte=start)
        elif value == "week":
            start = now - timedelta(days=7)
            return queryset.filter(order_date__gte=start)
        elif value == "month":
            start = now - timedelta(days=30)
            return queryset.filter(order_date__gte=start)
        elif value == "year":
            start = now - timedelta(days=365)
            return queryset.filter(order_date__gte=start)

        return queryset

    def filter_value_category(self, queryset, name, value):
        """
        Filter orders by total amount category.
        Usage: valueCategory: "large"
        """
        if value == "small":
            return queryset.filter(total_amount__lt=100)
        elif value == "medium":
            return queryset.filter(total_amount__gte=100, total_amount__lt=500)
        elif value == "large":
            return queryset.filter(total_amount__gte=500, total_amount__lte=1000)
        elif value == "xlarge":
            return queryset.filter(total_amount__gt=1000)

        return queryset

    class Meta:
        model = Order
        fields = []
