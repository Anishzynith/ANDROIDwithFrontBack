from rest_framework.routers import DefaultRouter

from users.views import UserViewSet


router = DefaultRouter()
router.register("auth", UserViewSet, basename="auth")

# Future app routers:
# router.register("onboarding", OnboardingViewSet, basename="onboarding")
# router.register("training", TrainingViewSet, basename="training")
# router.register("health", HealthViewSet, basename="health")
# router.register("races", RaceViewSet, basename="races")
