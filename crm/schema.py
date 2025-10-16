"""Imports for GraphQL schema"""

import re
from datetime import datetime
import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.validators import validate_email


from .models import Customer, Product, Order
from .filters import CustomerFilter, ProductFilter, OrderFilter


# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=unused-argument
# ============================================
# OBJECT TYPES WITH RELAY CONNECTION SUPPORT
# ============================================
class CustomerType(DjangoObjectType):
    """CustomerType definition"""

    class Meta:
        model = Customer
        fields = (
            "id",
            "name",
            "email",
            "phone",
            "created_at",
        )
        filterset_class = CustomerFilter
        interfaces = (graphene.relay.Node,)


class ProductType(DjangoObjectType):
    """ProductType definition"""

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "price",
            "stock",
            "created_at",
        )
        filterset_class = ProductFilter
        interfaces = (graphene.relay.Node,)


class OrderType(DjangoObjectType):
    """OrderType definition"""

    total_amount = graphene.Decimal()

    class Meta:
        model = Order
        fields = (
            "id",
            "customer",
            "products",
            "order_date",
            "total_amount",
            "created_at",
        )
        filterset_class = OrderFilter
        interfaces = (graphene.relay.Node,)

    totalAmount = graphene.Float(source="total_amount")
    orderDate = graphene.DateTime(source="order_date")


# ============================================
# STANDARD TYPES (NON-RELAY)
# ============================================
class CustomerTypeStandard(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone", "created_at")


class ProductTypeStandard(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock", "created_at")


class OrderTypeStandard(DjangoObjectType):
    total_amount = graphene.Decimal()

    class Meta:
        model = Order
        fields = (
            "id",
            "customer",
            "products",
            "order_date",
            "total_amount",
            "created_at",
        )


# ============================================
# INPUT TYPES
# ============================================
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()


class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Decimal(required=True)
    stock = graphene.Int(default_value=0)


class OrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.ID, required=True)
    order_date = graphene.DateTime()


# Filter Input Types for Standard Queries
class CustomerFilterInput(graphene.InputObjectType):
    name = graphene.String()
    name_icontains = graphene.String()
    email = graphene.String()
    email_icontains = graphene.String()
    created_at_gte = graphene.DateTime()
    created_at_lte = graphene.DateTime()
    phone_pattern = graphene.String()


class ProductFilterInput(graphene.InputObjectType):
    name = graphene.String()
    name_icontains = graphene.String()
    price_gte = graphene.Decimal()
    price_lte = graphene.Decimal()
    stock = graphene.Int()
    stock_gte = graphene.Int()
    stock_lte = graphene.Int()
    low_stock = graphene.Boolean()


class OrderFilterInput(graphene.InputObjectType):
    totalAmountGte = graphene.Decimal()
    totalAmountLte = graphene.Decimal()
    orderDateGte = graphene.DateTime()
    orderDateLte = graphene.DateTime()
    customer_name = graphene.String()
    customer_email = graphene.String()
    product_name = graphene.String()
    product_id = graphene.Int()
    product_ids = graphene.String()


# Validation Helpers
# Accepts +1234567890, 123-456-7890, (123) 456-7890, or 1234567890
PHONE_REGEX = re.compile(r"^(?:\+?\d{10,15}|\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4})$")


def validate_phone_format(phone):
    """Validate phone number format"""
    if not phone:
        return True

    # Accept formats: +1234567890, 123-456-7890, (123) 456-7890, 1234567890
    phone = phone.strip()
    return bool(PHONE_REGEX.match(phone))


def validate_customer_data(name, email, phone=None):
    """Validate customer data and return error message if invalid"""
    errors = []

    if not name or len(name.strip()) == 0:
        errors.append("Name is required and cannot be empty")

    if not email:
        errors.append("Email is required")
    else:
        try:
            validate_email(email)
        except ValidationError:
            errors.append(f"Invalid email format: {email}")

    if phone and not validate_phone_format(phone):
        errors.append(
            f"Invalid phone format: {phone}."
            "Use formats like +1234567890, 123-456-7890, (123) 456-7890, or 1234567890"
        )

    return errors


def apply_filters(queryset, filter_dict):
    """Apply filters from input dict to queryset"""
    if not filter_dict:
        return queryset

    # Remove None values
    filters = {k: v for k, v in filter_dict.items() if v is not None}

    # Handle special filter keys
    for key, value in filters.items():
        if "__" in key:
            # Django lookup expression
            queryset = queryset.filter(**{key: value})
        elif key == "name" or key == "email":
            queryset = queryset.filter(**{f"{key}__exact": value})

    return queryset


# pylint: disable=no-member
# pylint: disable=redefined-builtin
# pylint: disable=broad-exception-caught
# Mutations
class CreateCustomer(graphene.Mutation):
    """Create a single customer with validation"""

    class Arguments:
        input = CustomerInput(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()
    errors = graphene.List(graphene.String)

    def mutate(self, _info, input):
        # Validate input data
        validation_errors = validate_customer_data(
            input.name,
            input.email,
            input.get("phone"),
        )
        if validation_errors:
            return CreateCustomer(
                customer=None,
                message="Validation failed",
                errors=validation_errors,
            )

        # Check for duplicate email
        if Customer.objects.filter(email=input.email).exists():
            return CreateCustomer(
                customer=None,
                message="Creation failed",
                errors=[f"Email already exists: {input.email}"],
            )

        try:
            customer = Customer(
                name=input.name.strip(),
                email=input.email.lower().strip(),
                phone=input.get("phone", "").strip() if input.get("phone") else None,
            )
            customer.full_clean()
            customer.save()

            return CreateCustomer(
                customer=customer,
                message="Customer created successfully",
                errors=[],
            )
        except ValidationError as e:
            return CreateCustomer(
                customer=None,
                message="Validation error",
                errors=[str(e)],
            )
        except Exception as e:
            return CreateCustomer(
                customer=None,
                message="Failed to create customer",
                errors=[str(e)],
            )


class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(CustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)
    success_count = graphene.Int()
    failure_count = graphene.Int()

    def mutate(self, _info, input):
        created_customers = []
        errors = []

        # Use transaction to ensure data consistency
        try:
            with transaction.atomic():
                for idx, customer_data in enumerate(input):
                    try:
                        # Validate data
                        validation_errors = validate_customer_data(
                            customer_data.name,
                            customer_data.email,
                            customer_data.get("phone"),
                        )

                        if validation_errors:
                            errors.append(
                                f"Record {idx + 1}: {', '.join(validation_errors)}"
                            )
                            continue

                        # Check for duplicate email
                        email = customer_data.email.lower().strip()
                        if Customer.objects.filter(email=email).exists():
                            errors.append(
                                f"Record {idx + 1}: Email already exists: {email}"
                            )
                            continue

                        # Check for duplicates within the batch
                        if any(c.email == email for c in created_customers):
                            errors.append(
                                f"Record {idx + 1}: Duplicate email in batch: {email}"
                            )
                            continue

                        # Create customer
                        customer = Customer(
                            name=customer_data.name.strip(),
                            email=email,
                            phone=(
                                customer_data.get("phone", "").strip()
                                if customer_data.get("phone")
                                else None
                            ),
                        )
                        customer.full_clean()
                        customer.save()
                        created_customers.append(customer)

                    except ValidationError as e:
                        errors.append(f"Record {idx + 1}: Validation error - {str(e)}")
                    except ValueError as e:
                        errors.append(f"Record {idx + 1}: Invalid data - {str(e)}")
                    except Exception as e:
                        errors.append(f"Record {idx + 1}: Error - {str(e)}")

        except Exception as e:
            errors.append(f"Transaction error: {str(e)}")

        return BulkCreateCustomers(
            customers=created_customers,
            errors=errors,
            success_count=len(created_customers),
            failure_count=len(input) - len(created_customers),
        )


class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)

    product = graphene.Field(ProductType)
    message = graphene.String()
    errors = graphene.List(graphene.String)

    def mutate(self, _info, input):
        errors = []

        # Validate product name
        if not input.name or len(input.name.strip()) == 0:
            errors.append("Product name is required and cannot be empty")

        # Validate price
        if input.price is None:
            errors.append("Price is required")
        elif input.price <= 0:
            errors.append(f"Price must be positive, got: {input.price}")

        # Validate stock
        if input.stock < 0:
            errors.append(f"Stock cannot be negative, got: {input.stock}")

        if errors:
            return CreateProduct(
                product=None,
                message="Validation failed",
                errors=errors,
            )

        try:
            product = Product(
                name=input.name.strip(),
                price=input.price,
                stock=input.stock,
            )
            product.full_clean()
            product.save()

            return CreateProduct(
                product=product,
                message="Product created successfully",
                errors=[],
            )
        except ValidationError as e:
            return CreateProduct(
                product=None,
                message="Validation error",
                errors=[str(e)],
            )
        except Exception as e:
            return CreateProduct(
                product=None,
                message="Failed to create product",
                errors=[str(e)],
            )


class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)

    order = graphene.Field(OrderType)
    message = graphene.String()
    errors = graphene.List(graphene.String)

    def mutate(self, _info, input):
        errors = []

        # Validate customer ID
        try:
            customer = Customer.objects.get(pk=input.customer_id)
        except Customer.DoesNotExist:
            return CreateOrder(
                order=None,
                message="Order creation failed",
                errors=[f"Invalid customer ID: {input.customer_id}"],
            )

        # Validate product IDs
        if not input.product_ids or len(input.product_ids) == 0:
            return CreateOrder(
                order=None,
                message="Order creation failed",
                errors=["At least one product must be selected"],
            )

        # Fetch products and validate
        products = []
        invalid_product_ids = []

        for product_id in input.product_ids:
            try:
                product = Product.objects.get(pk=product_id)
                products.append(product)
            except Product.DoesNotExist:
                errors.append(f"Invalid product ID: {product_id}")

        if invalid_product_ids:
            return CreateOrder(
                order=None,
                message="Order creation failed",
                errors=[f"Invalid product ID(s): {', '.join(invalid_product_ids)}"],
            )

        try:
            with transaction.atomic():
                # Create order
                order = Order(
                    customer=customer,
                    order_date=(
                        input.order_date if input.get("order_date") else datetime.now()
                    ),
                )
                order.save()

                # Associate products
                order.products.set(products)

                # Calculate total amount
                total_amount = sum(product.price for product in products)
                order.total_amount = total_amount
                order.save()

                return CreateOrder(
                    order=order,
                    message="Order created successfully",
                    errors=[],
                )
        except Exception as e:
            return CreateOrder(
                order=None,
                message="Failed to create order",
                errors=[str(e)],
            )


# ============================================
# QUERY CLASS WITH FILTERING
# ============================================
class Query(graphene.ObjectType):
    # Relay-style connection queries with filtering
    all_customers_connection = DjangoFilterConnectionField(CustomerType)
    all_products_connection = DjangoFilterConnectionField(ProductType)
    all_orders_connection = DjangoFilterConnectionField(OrderType)

    # Standard list queries with custom filtering
    all_customers = graphene.List(
        CustomerTypeStandard,
        filter=CustomerFilterInput(),
        order_by=graphene.String(),
    )
    all_products = graphene.List(
        ProductTypeStandard,
        filter=ProductFilterInput(),
        order_by=graphene.String(),
    )
    all_orders = graphene.List(
        OrderTypeStandard,
        filter=OrderFilterInput(),
        order_by=graphene.String(),
    )

    # Single object queries
    customer = graphene.Field(CustomerTypeStandard, id=graphene.ID(required=True))
    product = graphene.Field(ProductTypeStandard, id=graphene.ID(required=True))
    order = graphene.Field(OrderTypeStandard, id=graphene.ID(required=True))

    def resolve_all_customers(self, info, filter=None, order_by=None):
        """
        Resolve all customers with optional filtering and sorting.
        Supports filters: name, email, created_at range, phone_pattern
        """
        queryset = Customer.objects.all()

        # Apply filters
        if filter:
            filter_obj = CustomerFilter(data=filter, queryset=queryset)
            queryset = filter_obj.qs

        # Apply ordering
        if order_by:
            queryset = queryset.order_by(order_by)
        return queryset

    def resolve_all_products(self, info, filter=None, order_by=None):
        """
        Resolve all products with optional filtering and sorting.
        Supports filters: name, price range, stock range, low_stock
        """
        queryset = Product.objects.all()

        # Apply filters
        if filter:
            filter_obj = ProductFilter(data=filter, queryset=queryset)
            queryset = filter_obj.qs

        # Apply ordering
        if order_by:
            queryset = queryset.order_by(order_by)

        return queryset

    def resolve_all_orders(self, info, filter=None, order_by=None):
        """
        Resolve all orders with optional filtering and sorting.
        Supports filters: total_amount range, order_date range,
                         customer_name, product_name, product_id
        """
        queryset = (
            Order.objects.select_related("customer").prefetch_related("products").all()
        )

        # Apply filters
        if filter:
            filter_obj = OrderFilter(data=filter, queryset=queryset)
            queryset = filter_obj.qs

        # Apply ordering
        if order_by:
            order_by = order_by.replace("totalAmount", "total_amount").replace(
                "orderDate", "order_date"
            )
            queryset = queryset.order_by(order_by)

        return queryset

    def resolve_customer(self, info, id):
        try:
            return Customer.objects.get(pk=id)
        except Customer.DoesNotExist:
            return None

    def resolve_product(self, info, id):
        try:
            return Product.objects.get(pk=id)
        except Product.DoesNotExist:
            return None

    def resolve_order(self, info, id):
        try:
            return (
                Order.objects.select_related("customer")
                .prefetch_related("products")
                .get(pk=id)
            )
        except Order.DoesNotExist:
            return None


# ========================
# MUTATION CLASS
# ========================
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()


# Schema
schema = graphene.Schema(query=Query, mutation=Mutation)
