# Root URL registry - equivalent of Flask's register_blueprint calls
 
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve
 
urlpatterns = [
    path('admin/', admin.site.urls),
 
    # Versioned API routes
    path('api/v1/', include('api.v1.urls')),
]
 
if settings.DEBUG or getattr(settings, "SERVE_MEDIA_FILES", False):
    urlpatterns += [
        re_path(
            r"^media/(?P<path>.*)$",
            serve,
            {"document_root": settings.MEDIA_ROOT},
        )
    ]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
  
 
