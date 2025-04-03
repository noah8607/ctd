from rest_framework import serializers
from .models import (
    DiagnosisImage, UserDescription, DiagnosisQuestion,
    DiagnosisAnswer, PreDiagnosisReport, Doctor
)

class DiagnosisImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiagnosisImage
        fields = ['id', 'report', 'image', 'uploaded_at']
        read_only_fields = ['uploaded_at']

class UserDescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDescription
        fields = ['id', 'report', 'audio', 'text_content', 'uploaded_at', 'processed']
        read_only_fields = ['text_content', 'uploaded_at', 'processed']

class DiagnosisAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiagnosisAnswer
        fields = ['id', 'question', 'content', 'created_at']
        read_only_fields = ['created_at']

class DiagnosisQuestionSerializer(serializers.ModelSerializer):
    answer = DiagnosisAnswerSerializer(read_only=True)
    
    class Meta:
        model = DiagnosisQuestion
        fields = ['id', 'report', 'question_number', 'content', 'answer', 'created_at']
        read_only_fields = ['created_at']

class DiagnosisQuestionWithAnswerSerializer(serializers.ModelSerializer):
    answer = DiagnosisAnswerSerializer(read_only=True)
    
    class Meta:
        model = DiagnosisQuestion
        fields = ['id', 'report', 'question_number', 'content', 'answer', 'created_at']
        read_only_fields = ['created_at']

class DoctorSerializer(serializers.ModelSerializer):
    """医生序列化器"""
    title_display = serializers.CharField(source='get_title_display', read_only=True)
    
    class Meta:
        model = Doctor
        fields = [
            'id', 'name', 'title', 'title_display', 'years_of_experience',
            'hospital', 'department', 'specialty', 'tcm_patterns',
            'rating', 'patients_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class DoctorRecommendationSerializer(serializers.Serializer):
    """医生推荐序列化器"""
    report_id = serializers.IntegerField(required=True)

class PreDiagnosisReportSerializer(serializers.ModelSerializer):
    images = DiagnosisImageSerializer(many=True, read_only=True)
    description = UserDescriptionSerializer(read_only=True)
    questions = serializers.SerializerMethodField()
    progress_status = serializers.CharField(read_only=True)
    has_images = serializers.BooleanField(read_only=True)
    has_description = serializers.BooleanField(read_only=True)
    has_questions = serializers.BooleanField(read_only=True)
    all_questions_answered = serializers.BooleanField(read_only=True)

    class Meta:
        model = PreDiagnosisReport
        fields = [
            'id', 'images', 'description', 'questions',
            'progress_status', 'has_images', 'has_description',
            'has_questions', 'all_questions_answered',
            'report_content', 'treatment_plan', 'error_message', 'status',
            'created_at', 'updated_at'
        ]

    def get_questions(self, obj):
        """获取问题列表，包括每个问题的回答"""
        questions = obj.questions.all().order_by('question_number')
        detailed = self.context.get('detailed', False)
        
        # 如果是详细模式，包含问题的回答
        if detailed:
            return DiagnosisQuestionWithAnswerSerializer(questions, many=True).data
        
        # 否则使用基本的问题序列化器
        return DiagnosisQuestionSerializer(questions, many=True).data
