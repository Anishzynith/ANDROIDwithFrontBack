from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

from .routers import router


urlpatterns = [
    path("auth/", include("api.v1.routes.auth_urls")),
    path("", include(router.urls)),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
