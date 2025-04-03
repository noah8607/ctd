from django.contrib import admin
from .models import (
    PreDiagnosisReport, DiagnosisImage, UserDescription,
    DiagnosisQuestion, DiagnosisAnswer, Doctor
)

# Register your models here.

@admin.register(PreDiagnosisReport)
class PreDiagnosisReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    search_fields = ('id', 'report_content')

@admin.register(DiagnosisImage)
class DiagnosisImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'report', 'uploaded_at')
    list_filter = ('uploaded_at', 'report')
    search_fields = ('report__id',)
    date_hierarchy = 'uploaded_at'

@admin.register(UserDescription)
class UserDescriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'report', 'processed', 'uploaded_at', 'text_content')
    list_filter = ('processed', 'uploaded_at')
    readonly_fields = ('text_content', 'uploaded_at', 'processed')
    search_fields = ('report__id', 'text_content')
    date_hierarchy = 'uploaded_at'

@admin.register(DiagnosisQuestion)
class DiagnosisQuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'report', 'question_number', 'content', 'created_at')
    list_filter = ('question_number', 'created_at')
    search_fields = ('report__id', 'content')
    date_hierarchy = 'created_at'

@admin.register(DiagnosisAnswer)
class DiagnosisAnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'content', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('question__id', 'content')
    date_hierarchy = 'created_at'

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('name', 'title', 'hospital', 'department', 'rating', 'patients_count')
    list_filter = ('title', 'hospital', 'department')
    search_fields = ('name', 'hospital', 'specialty', 'tcm_patterns')
    ordering = ('-rating', '-patients_count')
