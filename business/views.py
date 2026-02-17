from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from .models import Product, User, Business, ActivityLog,ChatMessage
from .serializers import ProductSerializer, UserSerializer, BusinessSerializer
from .permissions import IsAdminUserRole, IsApproverRole
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny
import re
import google.generativeai as genai
import os
from dotenv import load_dotenv
from pathlib import Path
from django.conf import settings

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(os.path.join(BASE_DIR, '.env'))

genai.configure(api_key=settings.GEMINI_API_KEY)


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser] 

    def get_queryset(self):
        return Product.objects.filter(business=self.request.user.business)

    def perform_create(self, serializer):
        product = serializer.save(created_by=self.request.user, business=self.request.user.business)
        ActivityLog.objects.create(user=self.request.user, action=f"Created product '{product.name}'")

    def perform_update(self, serializer):
        product = self.get_object()
        if product.created_by != self.request.user and self.request.user.role != "Admin":
            raise PermissionDenied("You cannot edit this product")
        updated = serializer.save()
        ActivityLog.objects.create(user=self.request.user, action=f"Updated product '{updated.name}'")

    def perform_destroy(self, instance):
        if instance.created_by != self.request.user and self.request.user.role != "Admin":
            raise PermissionDenied("You cannot delete this product")
        ActivityLog.objects.create(user=self.request.user, action=f"Deleted product '{instance.name}'")
        instance.delete()

    @action(detail=True, methods=["POST"], permission_classes=[IsApproverRole])
    def approve(self, request, pk=None):
        product = self.get_object()
        product.status = "approved"
        product.save()
        ActivityLog.objects.create(user=request.user, action=f"Approved product '{product.name}'")
        return Response({"message": f"Product '{product.name}' approved."}, status=status.HTTP_200_OK)
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Product.objects.none()
        user = self.request.user
        return Product.objects.filter(business=user.business)
        



class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUserRole]

   
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return User.objects.none()
        return User.objects.filter(business=self.request.user.business)

   
    def perform_create(self, serializer):
       
        password = serializer.validated_data.pop("password", None)
       
        user = serializer.save(business=self.request.user.business)
       
        if password:
            user.set_password(password)
            user.save()
       
        ActivityLog.objects.create(
            user=self.request.user,
            action=f"Created user '{user.username}'"
        )



class BusinessViewSet(viewsets.ModelViewSet):
    serializer_class = BusinessSerializer
    permission_classes = [IsAuthenticated, IsAdminUserRole]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Business.objects.none()
        user = self.request.user
        return Business.objects.filter(id=user.business.id)
    

class PublicProductViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Product.objects.filter(status="approved")

    @action(detail=False, methods=["POST"], url_path="chat", permission_classes=[AllowAny])
    def chat(self, request):
      
        user_message = request.data.get("message", "")

        if not user_message:
            return Response(
                {"response": "Please enter a message."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

      
        products = Product.objects.filter(status="approved")
        if not products.exists():
            return Response({"response": "No approved products available."})

        product_context = "\n".join([
            f"Name: {p.name}\nPrice: ${p.price}\nDescription: {p.description}\n"
            for p in products
        ])

       
        prompt = f"""
            You are a helpful product assistant.

            ONLY answer using the product data below.
            If a product is not found, say it is not available.

            Available Products:
            {product_context}

            User Question:
            {user_message}
        """

        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=300,
                    temperature=0.7,
                )
            )
            
         
            ai_response = response.text

        except Exception as e:
            
            print(f"Gemini API error: {str(e)}")
            return Response(
                {"response": "AI service temporarily unavailable."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

      
        ChatMessage.objects.create(
            user=request.user if request.user.is_authenticated else None,
            user_message=user_message,
            ai_response=ai_response
        )

        return Response({"response": ai_response}, status=status.HTTP_200_OK)