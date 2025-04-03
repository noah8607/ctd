from django.db import models
from django.utils import timezone
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.core.exceptions import ValidationError

class PreDiagnosisReport(models.Model):
    """预诊报告 - 作为整个诊断流程的主表"""
    # 状态信息
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('error', '错误')
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # 报告内容
    report_content = models.TextField(blank=True)
    treatment_plan = models.TextField(blank=True)
    error_message = models.TextField(blank=True)

    # 时间戳
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def has_images(self):
        """检查是否有上传的图片"""
        return self.images.exists()
           
    @property
    def has_description(self):
        """检查是否有症状描述"""
        return hasattr(self, 'description') and bool(self.description.text_content)
           
    @property
    def has_questions(self):
        """检查是否已生成问题"""
        return self.questions.exists()
           
    @property
    def all_questions_answered(self):
        """检查是否所有问题都已回答"""
        return not self.questions.filter(answer__isnull=True).exists() if self.has_questions else False
           
    @property
    def progress_status(self):
        """获取当前进度状态"""
        if not self.has_images:
            return 'waiting_for_images'
        if not self.has_description:
            return 'waiting_for_description'
        if not self.has_questions:
            return 'waiting_for_questions'
        if not self.all_questions_answered:
            return 'waiting_for_answers'
        if not self.report_content:
            return 'waiting_for_report'
        return 'completed'

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"诊断报告 {self.id} - {self.get_status_display()}"

    def clean(self):
        """验证图片数量在3-5张之间"""
        super().clean()
        if self.pk and self.has_images:  # 只在图片上传完成时验证
            image_count = self.images.count()
            if not (3 <= image_count <= 5):
                raise ValidationError({
                    'images': f'必须上传3-5张图片，当前有{image_count}张'
                })

class DiagnosisImage(models.Model):
    """诊断图片"""
    report = models.ForeignKey(
        PreDiagnosisReport,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='diagnosis_images/%Y/%m/%d/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['uploaded_at']

    def __str__(self):
        return f"诊断图片 {self.id} - 报告 {self.report_id}"

class UserDescription(models.Model):
    """用户自述"""
    report = models.OneToOneField(
        PreDiagnosisReport,
        on_delete=models.CASCADE,
        related_name='description'
    )
    audio = models.FileField(upload_to='user_descriptions/%Y/%m/%d/', blank=True)
    text_content = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)

    class Meta:
        ordering = ['uploaded_at']

    def __str__(self):
        return f"用户自述 {self.id} - 报告 {self.report_id}"

class DiagnosisQuestion(models.Model):
    """诊断问题"""
    report = models.ForeignKey(
        PreDiagnosisReport,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    question_number = models.PositiveSmallIntegerField()  # Q1, Q2, Q3 对应 1, 2, 3
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['question_number']
        unique_together = ['report', 'question_number']  # 每个报告的问题编号不能重复

    def __str__(self):
        return f"问题 {self.question_number} - 报告 {self.report_id}"

class DiagnosisAnswer(models.Model):
    """诊断问题回答"""
    question = models.OneToOneField(
        DiagnosisQuestion,
        on_delete=models.CASCADE,
        related_name='answer'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['question__question_number']

    def __str__(self):
        return f"问题 {self.question.question_number} 的回答 - 报告 {self.question.report_id}"

class Doctor(models.Model):
    """医生信息"""
    TITLE_CHOICES = [
        ('主任医师', '主任医师'),
        ('副主任医师', '副主任医师'),
        ('主治医师', '主治医师')
    ]

    name = models.CharField('姓名', max_length=50)
    title = models.CharField('职称', max_length=20, choices=TITLE_CHOICES)
    years_of_experience = models.IntegerField('执业年限')
    hospital = models.CharField('主要执业医院', max_length=100)
    department = models.CharField('科室', max_length=50)
    specialty = models.TextField('专长领域')
    tcm_patterns = models.CharField('擅长证型', max_length=200, help_text='用逗号分隔的证型列表')
    rating = models.FloatField('评分', default=5.0)
    patients_count = models.IntegerField('接诊量', default=0)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        ordering = ['-rating', '-patients_count']
        verbose_name = '医生'
        verbose_name_plural = '医生'

    def __str__(self):
        return f"{self.name} - {self.get_title_display()} ({self.hospital})"

    @property
    def title_weight(self):
        """获取职称权重"""
        weights = {
            '主任医师': 1.0,
            '副主任医师': 0.8,
            '主治医师': 0.6
        }
        return weights.get(self.title, 0.5)

    @property
    def pattern_list(self):
        """获取证型列表"""
        return [p.strip() for p in self.tcm_patterns.split(',') if p.strip()]
