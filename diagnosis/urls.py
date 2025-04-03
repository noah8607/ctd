from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DiagnosisImageViewSet, UserDescriptionViewSet,
    DiagnosisQuestionViewSet, DiagnosisAnswerViewSet,
    PreDiagnosisReportViewSet, DoctorViewSet
)

router = DefaultRouter()
router.register(r'images', DiagnosisImageViewSet)
router.register(r'descriptions', UserDescriptionViewSet)
router.register(r'questions', DiagnosisQuestionViewSet)
router.register(r'answers', DiagnosisAnswerViewSet)
router.register(r'reports', PreDiagnosisReportViewSet)
router.register(r'doctors', DoctorViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
