from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, UserViewSet, BusinessViewSet,PublicProductViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='products')
router.register(r'users', UserViewSet, basename='users')
router.register(r'business', BusinessViewSet, basename='business')
router.register(r'public-products', PublicProductViewSet, basename='public-product')

urlpatterns = [
    
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', include(router.urls)),
]
