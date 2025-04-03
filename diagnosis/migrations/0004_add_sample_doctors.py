from django.db import migrations

def add_sample_doctors(apps, schema_editor):
    Doctor = apps.get_model('diagnosis', 'Doctor')
    
    doctors_data = [
        {
            'name': '张医生',
            'title': '主任医师',
            'years_of_experience': 40,
            'hospital': '上海中医药大学附属龙华医院',
            'department': '呼吸科',
            'specialty': '擅长治疗呼吸系统疾病，尤其是急性传染性疾病',
            'tcm_patterns': '肺胃气虚,痰湿阻肺,肺阴亏虚',
            'rating': 4.9,
            'patients_count': 10000
        },
        {
            'name': '仝医生',
            'title': '主任医师',
            'years_of_experience': 35,
            'hospital': '上海市中医医院',
            'department': '肾病科',
            'specialty': '擅长治疗各类肾病及免疫系统疾病',
            'tcm_patterns': '肾阳虚,肾阴虚,脾肾气虚',
            'rating': 4.8,
            'patients_count': 8000
        },
        {
            'name': '李医生',
            'title': '副主任医师',
            'years_of_experience': 25,
            'hospital': '上海同济医院中医科',
            'department': '脾胃病科',
            'specialty': '擅长治疗消化系统疾病，尤其是功能性胃肠病',
            'tcm_patterns': '脾胃气虚,肝胃不和,胃阴不足',
            'rating': 4.7,
            'patients_count': 6000
        },
        {
            'name': '王医生',
            'title': '主任医师',
            'years_of_experience': 30,
            'hospital': '上海市第一人民医院中医科',
            'department': '心血管科',
            'specialty': '擅长治疗各类心血管疾病，尤其是冠心病、高血压',
            'tcm_patterns': '气虚血瘀,阳虚血瘀,肝阳上亢',
            'rating': 4.8,
            'patients_count': 7500
        },
        {
            'name': '刘医生',
            'title': '主治医师',
            'years_of_experience': 15,
            'hospital': '上海德济医院',
            'department': '妇科',
            'specialty': '擅长治疗妇科疾病，尤其是月经病、不孕症',
            'tcm_patterns': '肾阴虚,肝郁气滞,血瘀气滞',
            'rating': 4.6,
            'patients_count': 4500
        },
        {
            'name': '陈医生',
            'title': '主任医师',
            'years_of_experience': 28,
            'hospital': '上海中医药大学附属岳阳医院',
            'department': '肿瘤科',
            'specialty': '擅长中医药防治肿瘤及其并发症',
            'tcm_patterns': '气阴两虚,脾胃虚弱,痰瘀互结',
            'rating': 4.8,
            'patients_count': 7000
        },
        {
            'name': '赵医生',
            'title': '副主任医师',
            'years_of_experience': 22,
            'hospital': '上海市普陀区中医医院',
            'department': '皮肤科',
            'specialty': '擅长各类皮肤病、过敏性疾病的诊治',
            'tcm_patterns': '血热风燥,湿热蕴肤,血虚风燥',
            'rating': 4.7,
            'patients_count': 5500
        },
        {
            'name': '杨医生',
            'title': '主治医师',
            'years_of_experience': 12,
            'hospital': '杨医生中药堂',
            'department': '内分泌科',
            'specialty': '擅长治疗糖尿病、甲状腺疾病等内分泌疾病',
            'tcm_patterns': '阴虚燥热,气阴两虚,脾肾阳虚',
            'rating': 4.5,
            'patients_count': 3800
        },
        {
            'name': '孙医生',
            'title': '主任医师',
            'years_of_experience': 32,
            'hospital': '孙氏国医馆',
            'department': '针灸科',
            'specialty': '擅长针灸治疗神经系统疾病、疼痛性疾病',
            'tcm_patterns': '肝肾阴虚,气滞血瘀,肝阳上亢',
            'rating': 4.9,
            'patients_count': 8500
        },
        {
            'name': '周医生',
            'title': '副主任医师',
            'years_of_experience': 20,
            'hospital': '周氏中医诊所',
            'department': '骨伤科',
            'specialty': '擅长各类骨伤疾病、颈肩腰腿痛等',
            'tcm_patterns': '肝肾亏虚,气血瘀滞,寒湿阻络',
            'rating': 4.7,
            'patients_count': 6000
        }
    ]
    
    for data in doctors_data:
        Doctor.objects.create(**data)

def remove_sample_doctors(apps, schema_editor):
    Doctor = apps.get_model('diagnosis', 'Doctor')
    Doctor.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('diagnosis', '0003_doctor'),
    ]

    operations = [
        migrations.RunPython(add_sample_doctors, remove_sample_doctors),
    ]
