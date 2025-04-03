import re
from typing import List, Dict, Tuple
from ..models import Doctor, PreDiagnosisReport

class DoctorRecommendationService:
    """医生推荐服务"""
    
    def __init__(self):
        # 权重配置
        self.weights = {
            'pattern': 0.5,    # 证型匹配权重
            'title': 0.3,     # 职称权重
            'rating': 0.2     # 评分权重
        }

    def extract_patterns(self, report_content: str) -> List[str]:
        """从报告中提取证型
        
        Args:
            report_content: 报告内容
            
        Returns:
            提取到的证型列表
        """
        # 简单的证型提取逻辑，可以根据需要优化
        common_patterns = [
            '气虚证', '阳虚证', '阴虚证', '痰湿证', '血瘀证', '肝郁证',
            '脾胃气虚', '肝郁气滞', '肾阳虚', '肾阴虚'
        ]
        found_patterns = []
        for pattern in common_patterns:
            if pattern in report_content:
                found_patterns.append(pattern)
        return found_patterns

    def calculate_pattern_score(self, report_patterns: List[str], doctor: Doctor) -> float:
        """计算证型匹配分数
        
        Args:
            report_patterns: 报告中的证型列表
            doctor: 医生对象
            
        Returns:
            匹配分数 (0-1)
        """
        if not report_patterns:
            return 0.5  # 如果没有提取到证型，返回中等分数
            
        doctor_patterns = doctor.pattern_list
        if not doctor_patterns:
            return 0.3  # 如果医生没有设置擅长证型，返回较低分数
            
        # 计算匹配的证型数量
        matched = sum(1 for p in report_patterns if p in doctor_patterns)
        max_possible = max(len(report_patterns), len(doctor_patterns))
        return matched / max_possible if max_possible > 0 else 0.5

    def calculate_rating_score(self, doctor: Doctor) -> float:
        """计算评分权重
        
        Args:
            doctor: 医生对象
            
        Returns:
            评分分数 (0-1)
        """
        # 评分占 70%，接诊量占 30%
        rating_weight = 0.7
        patients_weight = 0.3
        
        # 评分转换为 0-1 分数
        rating_score = doctor.rating / 5.0
        
        # 接诊量分数（假设 5000 是一个较好的接诊量基准）
        patients_score = min(doctor.patients_count / 5000, 1.0)
        
        return (rating_score * rating_weight) + (patients_score * patients_weight)

    def get_recommendations(self, report: PreDiagnosisReport) -> List[Dict]:
        """获取医生推荐列表
        
        Args:
            report: 预诊报告对象
            
        Returns:
            推荐列表，包含医生信息和匹配分数
        """
        if not report.report_content:
            return []
            
        # 提取报告中的证型
        report_patterns = self.extract_patterns(report.report_content)
        
        # 获取所有医生
        doctors = Doctor.objects.all()
        
        recommendations = []
        for doctor in doctors:
            # 计算各项分数
            pattern_score = self.calculate_pattern_score(report_patterns, doctor)
            title_score = doctor.title_weight
            rating_score = self.calculate_rating_score(doctor)
            
            # 计算总分
            total_score = (
                pattern_score * self.weights['pattern'] +
                title_score * self.weights['title'] +
                rating_score * self.weights['rating']
            )
            
            # 生成匹配原因
            matching_reasons = []
            if pattern_score > 0.7:
                matching_reasons.append("对您的证型有丰富治疗经验")
            if title_score > 0.8:
                matching_reasons.append("具有丰富的临床经验")
            if rating_score > 0.8:
                matching_reasons.append("患者评价较高")
            
            recommendations.append({
                'doctor': {
                    'id': doctor.id,
                    'name': doctor.name,
                    'title': doctor.get_title_display(),
                    'hospital': doctor.hospital,
                    'department': doctor.department,
                    'specialty': doctor.specialty,
                    'tcm_patterns': doctor.tcm_patterns,
                    'years_of_experience': doctor.years_of_experience,
                    'rating': doctor.rating,
                    'patients_count': doctor.patients_count
                },
                'matching_score': round(total_score, 3),
                'matching_reasons': matching_reasons
            })
        
        # 按匹配分数排序
        recommendations.sort(key=lambda x: x['matching_score'], reverse=True)
        
        return recommendations
