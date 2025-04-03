# 中医智能诊断推荐系统

基于Django REST framework构建的中医智能诊断及医生推荐系统。系统通过分析患者的图片、语音描述等信息，结合AI进行智能诊断，并基于证型匹配算法推荐最适合的医生。

## 核心功能

- 智能诊断：通过图片分析和语音描述理解患者症状
- 医生推荐：基于证型匹配度、职称权重和综合评价进行智能推荐
- RESTful API：提供完整的API接口支持
- 数据分析：支持医生评分和接诊量统计

## 系统架构

### 数据模型

- **PreDiagnosisReport**: 预诊报告主表
- **DiagnosisImage**: 诊断图片管理
- **UserDescription**: 用户症状描述
- **DiagnosisQuestion/Answer**: 诊断问答管理
- **Doctor**: 医生信息管理

### 推荐算法

医生推荐算法基于以下权重：
- 证型匹配度: 40%
- 职称权重: 30%
- 综合评价: 30%

职称等级权重：
- 主任医师: 1.0
- 副主任医师: 0.8
- 主治医师: 0.6

## API接口

基础URL: `http://101.34.240.140:9004/api`

主要接口：
- 图片上传: `/images/upload-batch/`
- 语音上传: `/description/upload-audio/`
- 诊断报告: `/diagnosis/report/`
- 医生推荐: `/doctors/recommend/`

详细API文档请参考 [API文档](docs/api.md)

## 技术栈

- **后端框架**: Django REST framework
- **数据库**: PostgreSQL
- **文件存储**: Django默认文件系统
- **API文档**: Swagger/OpenAPI

## 部署要求

- Python 3.8+
- Django 4.0+
- PostgreSQL 12+

## 安装部署

1. 克隆仓库
```bash
git clone https://github.com/yourusername/ctd.git
cd ctd
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置数据库
```bash
python manage.py migrate
```

4. 启动服务
```bash
python manage.py runserver
```

## 许可证

MIT License

## 贡献指南

欢迎提交Issue和Pull Request来帮助改进项目。
