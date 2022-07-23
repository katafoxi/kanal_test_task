from contracts.views import *
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="Contracts API",
      default_version='v1',
      description="Kanalservis contracts"
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)

router = DefaultRouter()

router.register('contracts', ContractsViewset)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/orderslist', ContractAPIView.as_view()),
    path('', include(router.urls)),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
