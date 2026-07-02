# Central registry - Django equivalent of Flask's __init__.py
# Add one line per new domain as project grows

from django.urls import path, include

urlpatterns = [
    # Legacy auth routes maintained for compatibility.
    # New clients should use api.v1.urls, which exposes the same auth endpoints via a router.
    path('auth/', include('users.routes.auth_urls')),

    # Future blueprints:
    # path('employees/', include('employees.routes.employee_urls')),
    # path('leaves/',    include('leaves.routes.leave_urls')),
]
