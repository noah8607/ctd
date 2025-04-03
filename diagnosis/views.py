import logging
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils.crypto import get_random_string
from django.core.files.base import ContentFile
import base64
from .models import (
    DiagnosisImage, UserDescription, DiagnosisQuestion,
    DiagnosisAnswer, PreDiagnosisReport, Doctor
)
from .serializers import (
    DiagnosisImageSerializer, UserDescriptionSerializer,
    DiagnosisQuestionSerializer, DiagnosisAnswerSerializer,
    PreDiagnosisReportSerializer, DoctorSerializer, DoctorRecommendationSerializer
)
from .services.stt import transcribe_audio
from .services.ai_service import AIService
from .services.report_service import ReportGenerationService
from .services.doctor_recommendation import DoctorRecommendationService

# 获取logger实例
logger = logging.getLogger('diagnosis')

class DiagnosisImageViewSet(viewsets.ModelViewSet):
    """诊断图片视图集"""
    queryset = DiagnosisImage.objects.all()
    serializer_class = DiagnosisImageSerializer

    @action(detail=False, methods=['POST'], url_path='upload-batch')
    def upload_batch(self, request):
        """
        批量上传图片接口
        
        请求体格式：
        {
            "report": 1,
            "images": [
                {
                    "filename": "image1.jpg",
                    "content": "base64_encoded_content..."
                },
                ...
            ]
        }
        """
        report_id = request.data.get('report')
        images_data = request.data.get('images', [])
        
        if not report_id:
            logger.warning('No report ID provided')
            return Response({'error': '请提供报告ID'}, status=status.HTTP_400_BAD_REQUEST)
            
        if not images_data:
            logger.warning('No images provided in request')
            return Response({'error': '没有提供图片文件'}, status=status.HTTP_400_BAD_REQUEST)
            
        if not (3 <= len(images_data) <= 5):
            logger.warning(f'Invalid number of images: {len(images_data)}')
            return Response({'error': '必须上传3-5张图片'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            report = PreDiagnosisReport.objects.get(id=report_id)
        except PreDiagnosisReport.DoesNotExist:
            logger.error(f'Report not found: {report_id}')
            return Response({'error': '报告不存在'}, status=status.HTTP_404_NOT_FOUND)
        
        # 保存所有图片
        uploaded_images = []
        for idx, image_data in enumerate(images_data):
            try:
                if not isinstance(image_data, dict):
                    logger.error(f'Invalid image data format for image {idx}')
                    return Response(
                        {'error': f'图片 {idx + 1} 数据格式无效'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                filename = image_data.get('filename', f'image_{idx + 1}.jpg')
                content = image_data.get('content', '')
                
                if not content:
                    logger.error(f'No content provided for image {filename}')
                    return Response(
                        {'error': f'图片 {filename} 没有提供内容'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # 解码base64内容
                try:
                    # 移除可能的base64前缀（如 "data:image/jpeg;base64,"）
                    if ';base64,' in content:
                        content = content.split(';base64,')[1]
                    image_content = base64.b64decode(content)
                except Exception as e:
                    logger.error(f'Failed to decode base64 content for image {filename}: {str(e)}')
                    return Response(
                        {'error': f'图片 {filename} 的base64编码无效'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # 创建文件对象并保存
                image_file = ContentFile(image_content, name=filename)
                diagnosis_image = DiagnosisImage.objects.create(
                    report=report,
                    image=image_file
                )
                uploaded_images.append(diagnosis_image)
                
            except Exception as e:
                logger.error(f'Error processing image {idx + 1}: {str(e)}')
                # 如果出错，删除已上传的图片
                for image in uploaded_images:
                    image.delete()
                return Response(
                    {'error': f'处理图片 {idx + 1} 时出错: {str(e)}'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        # 更新报告状态
        report.status = 'processing'
        report.save()
        
        logger.info(f'Successfully uploaded {len(uploaded_images)} images for report {report_id}')
        serializer = self.get_serializer(uploaded_images, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class UserDescriptionViewSet(viewsets.ModelViewSet):
    queryset = UserDescription.objects.all()
    serializer_class = UserDescriptionSerializer

    def perform_create(self, serializer):
        """创建用户描述"""
        instance = serializer.save()
        logger.info(f'Created new user description with ID: {instance.id}')
        
        # 如果上传了音频文件，直接进行语音转文字
        if instance.audio:
            logger.info(f'Processing audio file for description ID: {instance.id}')
            try:
                result = transcribe_audio(instance.audio.path)
                if result.get('error'):
                    instance.status = 'error'
                    instance.error_message = result['error']
                    logger.error(f'Failed to transcribe audio for description ID {instance.id}: {result["error"]}')
                else:
                    instance.text_content = result['text']
                    instance.processed = True
                    logger.info(f'Successfully transcribed audio for description ID {instance.id}')
                instance.save()
            except Exception as e:
                logger.error(f'Exception during audio transcription for description ID {instance.id}: {str(e)}')
                instance.status = 'error'
                instance.error_message = str(e)
                instance.save()

    @action(detail=False, methods=['POST'], url_path='upload')
    def upload_description(self, request):
        """
        上传用户自述音频
        """
        if 'audio' not in request.FILES:
            logger.warning('No audio provided in request')
            return Response({'error': '请提供音频文件'}, status=status.HTTP_400_BAD_REQUEST)

        # 生成上传会话ID
        upload_session = get_random_string(32)
        logger.info(f'Created new upload session for audio: {upload_session}')

        try:
            # 创建用户描述记录
            serializer = self.get_serializer(data={
                'audio': request.FILES['audio'],
                'upload_session': upload_session
            })
            serializer.is_valid(raise_exception=True)
            instance = serializer.save()

            # 等待语音转文字处理完成
            if instance.audio:
                logger.info(f'Processing audio file for description ID: {instance.id}')
                try:
                    result = transcribe_audio(instance.audio.path)
                    if result.get('error'):
                        instance.status = 'error'
                        instance.error_message = result['error']
                        logger.error(f'Failed to transcribe audio for description ID {instance.id}: {result["error"]}')
                    else:
                        instance.text_content = result['text']
                        instance.processed = True
                        logger.info(f'Successfully transcribed audio for description ID {instance.id}')
                    instance.save()
                except Exception as e:
                    logger.error(f'Exception during audio transcription for description ID {instance.id}: {str(e)}')
                    instance.status = 'error'
                    instance.error_message = str(e)
                    instance.save()
                    return Response(
                        {'error': f'音频处理失败: {str(e)}'}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

            # 返回更新后的数据
            serializer = self.get_serializer(instance)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f'Failed to process audio upload: {str(e)}')
            return Response(
                {'error': f'音频上传失败: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class DiagnosisQuestionViewSet(viewsets.ModelViewSet):
    queryset = DiagnosisQuestion.objects.all()
    serializer_class = DiagnosisQuestionSerializer
    ai_service = AIService()

    @action(detail=False, methods=['POST'], url_path='generate-questions')
    def generate_questions(self, request):
        """根据用户描述生成问题"""
        report_id = request.data.get('report_id')
        if not report_id:
            logger.warning('No report ID provided')
            return Response({'error': '请提供报告ID'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            report = PreDiagnosisReport.objects.get(id=report_id)
            
            # 检查是否有用户描述
            if not report.has_description:
                logger.warning(f'Report {report_id} has no description or text content')
                return Response({'error': '报告尚未添加症状描述或症状描述未处理完成'}, status=status.HTTP_400_BAD_REQUEST)

            # 生成问题
            questions = self.ai_service.generate_questions(report.description.text_content)
            
            # 创建问题记录
            created_questions = []
            for i, question_content in enumerate(questions, 1):
                question = DiagnosisQuestion.objects.create(
                    report=report,
                    question_number=i,
                    content=question_content
                )
                created_questions.append(question)
            
            # 更新报告状态
            report.status = 'processing'
            report.save()
            
            logger.info(f'Successfully generated {len(questions)} questions for report {report.id}')
            serializer = self.get_serializer(created_questions, many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except PreDiagnosisReport.DoesNotExist:
            logger.error(f'Report not found: {report_id}')
            return Response(
                {'error': '报告不存在'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f'Error generating questions: {str(e)}')
            return Response(
                {'error': f'生成问题失败: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['POST'], url_path='batch-answer')
    def batch_answer(self, request):
        """批量创建问题回答"""
        report_id = request.data.get('report_id')
        answers = request.data.get('answers', [])
        
        if not report_id:
            logger.warning('No report ID provided')
            return Response({'error': '请提供报告ID'}, status=status.HTTP_400_BAD_REQUEST)
            
        if not answers:
            logger.warning('No answers provided')
            return Response({'error': '请提供答案'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            report = PreDiagnosisReport.objects.get(id=report_id)
            
            # 检查是否已生成问题
            if not report.has_questions:
                logger.warning(f'Report {report_id} has no questions')
                return Response({'error': '报告尚未生成问题'}, status=status.HTTP_400_BAD_REQUEST)

            # 创建回答
            for answer_data in answers:
                question_number = answer_data.get('question_number')
                content = answer_data.get('content')
                
                try:
                    question = report.questions.get(question_number=question_number)
                    DiagnosisAnswer.objects.create(
                        question=question,
                        content=content
                    )
                except DiagnosisQuestion.DoesNotExist:
                    logger.warning(f'Question {question_number} not found for report {report_id}')
                    return Response(
                        {'error': f'问题编号 {question_number} 不存在'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # 更新报告状态
            report.status = 'processing'
            report.save()
            
            return Response({
                'message': '回答已保存',
                'report_id': report_id
            })

        except PreDiagnosisReport.DoesNotExist:
            logger.error(f'Report not found: {report_id}')
            return Response(
                {'error': '报告不存在'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f'Error saving answers: {str(e)}')
            return Response(
                {'error': f'保存回答失败: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class DiagnosisAnswerViewSet(viewsets.ModelViewSet):
    queryset = DiagnosisAnswer.objects.all()
    serializer_class = DiagnosisAnswerSerializer

class DoctorViewSet(viewsets.ModelViewSet):
    """医生视图集"""
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer

    def get_serializer_class(self):
        if self.action == 'recommend':
            return DoctorRecommendationSerializer
        return self.serializer_class

    @action(detail=False, methods=['POST'])
    def recommend(self, request):
        """根据诊断报告推荐医生
        
        请求体格式：
        {
            "report_id": 123
        }
        """
        try:
            report_id = request.data.get('report_id')
            if not report_id:
                return Response(
                    {'error': '请提供报告ID'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                report = PreDiagnosisReport.objects.get(id=report_id)
            except PreDiagnosisReport.DoesNotExist:
                return Response(
                    {'error': '报告不存在'}, 
                    status=status.HTTP_404_NOT_FOUND
                )

            if not report.report_content:
                return Response(
                    {'error': '报告尚未生成，无法推荐医生'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 获取推荐
            recommendation_service = DoctorRecommendationService()
            recommendations = recommendation_service.get_recommendations(report)

            return Response({
                'report_id': report_id,
                'recommendations': recommendations
            })

        except Exception as e:
            logger.error(f'Error recommending doctors: {str(e)}')
            return Response(
                {'error': '推荐医生时发生错误'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PreDiagnosisReportViewSet(viewsets.ModelViewSet):
    queryset = PreDiagnosisReport.objects.all()
    serializer_class = PreDiagnosisReportSerializer
    report_service = ReportGenerationService()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.action == 'retrieve':
            context['detailed'] = True
        return context

    def retrieve(self, request, *args, **kwargs):
        """
        获取报告详细信息，包括：
        - 报告基本信息
        - 所有上传的图片
        - 用户描述（音频和转换后的文字）
        - 所有问题和回答
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def perform_create(self, serializer):
        """创建报告时的额外处理"""
        report = serializer.save()
        logger.info(f'Created new pre-diagnosis report with ID: {report.id}')
        
        # 基于图片、用户自述文字和问答来生成报告
        report.status = 'processing'
        report.save()
        
        try:
            # 获取用户自述
            description = report.description
            if not description or not description.text_content:
                raise ValueError("用户自述内容不能为空")

            # 获取问答对
            qa_pairs = []
            for qa in report.diagnosis_answers.all():
                qa_pairs.append({
                    'question': qa.get_question_display(),
                    'answer': qa.answer
                })

            if not qa_pairs:
                raise ValueError("问诊记录不能为空")

            # 生成报告
            report_content = self.report_service.generate_report(
                description.text_content,
                qa_pairs
            )

            if report_content:
                report.report_content = report_content
                report.status = 'completed'
                logger.info(f'Successfully generated report for ID: {report.id}')
            else:
                report.status = 'error'
                report.error_message = "报告生成失败"
                logger.error(f'Failed to generate report content for ID: {report.id}')

        except Exception as e:
            report.status = 'error'
            report.error_message = str(e)
            logger.error(f'Error processing report ID {report.id}: {str(e)}')

        report.save()

    @action(detail=True, methods=['POST'], url_path='generate_report')
    def generate_report(self, request, pk=None):
        """生成预诊报告"""
        report = self.get_object()
        
        # 检查是否满足生成报告的条件
        if not report.has_description:
            return Response(
                {'error': 'PreDiagnosisReport has no description.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if not report.has_questions or not report.all_questions_answered:
            return Response(
                {'error': '尚未完成问题问答环节'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 检查报告是否已经生成
            if report.report_content and report.status == 'completed':
                logger.info(f'Report {report.id} already has content, skipping generation')
                return Response({
                    'message': '报告已生成',
                    'report_content': report.report_content,
                    'treatment_plan': report.treatment_plan,
                })

            # 获取问答对
            qa_pairs = []
            for question in report.questions.all():
                if question.answer:
                    qa_pairs.append({
                        'question': question.content,
                        'answer': question.answer.content
                    })

            # 生成报告内容
            report_content = self.report_service.generate_report(
                report.description.text_content, 
                qa_pairs,
                treatment=False
            )

            # 生成治疗方案
            treatment_report_content = self.report_service.generate_report(
                report.description.text_content, 
                qa_pairs,
                treatment=True
            )
            
            # 更新报告
            report.report_content = report_content
            report.treatment_plan = treatment_report_content
            report.status = 'completed'
            report.save()
            
            return Response({
                'message': '报告生成成功',
                'report_content': report.report_content,
                'treatment_plan': report.treatment_plan,
            })

        except Exception as e:
            logger.error(f'Failed to generate report: {str(e)}')
            report.error_message = str(e)
            report.status = 'error'
            report.save()
            return Response(
                {'error': f'生成报告失败: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def create_from_components(self, request):
        """从组件创建预诊断报告"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # 创建报告
            report = serializer.save()
            logger.info(f'Created pre-diagnosis report from components with ID: {report.id}')
            return Response(
                self.get_serializer(report).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f'Failed to create pre-diagnosis report: {str(e)}')
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
