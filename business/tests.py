from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Business, Product

User = get_user_model()

class ProductAPITestCase(APITestCase):
    def setUp(self):
        self.business = Business.objects.create(
            name="Test Business",
            about="Test About",
            email="test@business.com"
        )

        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="password123",
            role="Admin",
            business=self.business,
            is_staff=True 
        )

        self.approver_user = User.objects.create_user(
            username="approver",
            email="approver@test.com",
            password="password123",
            role="Approver",
            business=self.business
        )

        self.client.login(username="admin", password="password123")


    def test_create_product(self):
        url = reverse("products-list")

        data = {
            "name": "Laptop",
            "description": "Gaming laptop",
            "price": "1500.00"
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(Product.objects.first().created_by, self.admin_user)

 
    def test_product_belongs_to_business(self):
        product = Product.objects.create(
            name="Phone",
            description="Smartphone",
            price="800.00",
            created_by=self.admin_user,
            business=self.business
        )

        self.assertEqual(product.business, self.business)

 
    def test_only_approver_can_approve(self):
        product = Product.objects.create(
            name="Tablet",
            description="Android tablet",
            price="600.00",
            created_by=self.admin_user,
            business=self.business
        )

        # login as approver
        self.client.login(username="approver", password="password123")

        url = reverse("products-detail", args=[product.id])
        response = self.client.patch(url, {"status": "approved"}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        product.refresh_from_db()
        self.assertEqual(product.status, "approved")

    def test_only_approved_products_visible(self):

        Product.objects.create(
            name="Draft Product",
            description="Not approved",
            price="100.00",
            status="draft",
            created_by=self.admin_user,
            business=self.business
        )

        Product.objects.create(
            name="Approved Product",
            description="Approved",
            price="200.00",
            status="approved",
            created_by=self.admin_user,
            business=self.business
        )

        url = reverse("products-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)