# Root URL registry - equivalent of Flask's register_blueprint calls

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Versioned API routes
    path('api/v1/', include('api.v1.urls')),

]
