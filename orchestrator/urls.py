from django.contrib import admin
from django.urls import include, path
from rest_framework import routers

from workflows import views as workflow_views

router = routers.DefaultRouter()
router.register(r"workflows", workflow_views.WorkflowViewSet, basename="workflow")
router.register(r"runs", workflow_views.WorkflowRunViewSet, basename="run")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
]
