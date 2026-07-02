# Auth blueprint - equivalent of Flask's auth_routes.py
# Each path maps directly to a UserViewSet action

from django.urls import path
from users.views import UserViewSet

urlpatterns = [
    path('signup/',                 UserViewSet.as_view({'post': 'signup'})),
    path('login/',                  UserViewSet.as_view({'post': 'login'})),
    path('verify-otp/',             UserViewSet.as_view({'post': 'verify_otp'})),
    path('resend-otp/',             UserViewSet.as_view({'post': 'resend_otp'})),
    path('google-login/',           UserViewSet.as_view({'post': 'google_login'})),
    path('password-reset/',         UserViewSet.as_view({'post': 'password_reset_request'})),
    path('password-reset/confirm/', UserViewSet.as_view({'post': 'password_reset_confirm'})),
    path('profile/',                UserViewSet.as_view({'get':  'profile', 'patch': 'profile'})),
    path('logout/',                 UserViewSet.as_view({'post': 'logout'})),
    path('admin-login/',            UserViewSet.as_view({'post': 'admin_login'})),
]
