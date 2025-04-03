# 中医智能诊断系统 API 文档

## API 概述

- 基础URL: `http://101.34.240.140:9004/api`
- API版本: v1
- 数据格式: JSON
- 认证方式: Bearer Token
- 时间格式: ISO 8601 (YYYY-MM-DDTHH:mm:ss.sssZ)

## 通用响应格式

### 成功响应
```json
{
    "code": 200,
    "message": "操作成功",
    "data": {
        // 具体数据
    }
}
```

### 错误响应
```json
{
    "code": 400,
    "message": "错误描述",
    "errors": {
        "field": ["具体错误信息"]
    }
}
```

## API 端点

### 1. 诊断流程

#### 1.1 上传诊断图片

**POST** `/diagnosis/images/upload/`

上传3-5张诊断相关图片。

**请求头**
```
Content-Type: multipart/form-data
Authorization: Bearer <token>
```

**请求参数**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| images | File[] | 是 | 3-5张诊断图片 |

**响应示例**
```json
{
    "code": 200,
    "message": "图片上传成功",
    "data": {
        "report_id": "12345",
        "images": [
            {
                "id": 1,
                "url": "/media/diagnosis/2025/04/image1.jpg",
                "uploaded_at": "2025-04-03T10:15:30Z"
            }
        ]
    }
}
```

#### 1.2 上传语音描述

**POST** `/diagnosis/description/audio/`

上传患者症状语音描述（支持MP3格式）。

**请求头**
```
Content-Type: multipart/form-data
Authorization: Bearer <token>
```

**请求参数**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| audio | File | 是 | MP3格式音频文件 |
| report_id | String | 是 | 诊断报告ID |

**响应示例**
```json
{
    "code": 200,
    "message": "语音上传成功",
    "data": {
        "description_id": "67890",
        "text_content": "患者描述的症状文本",
        "duration": 45.6,
        "created_at": "2025-04-03T10:20:30Z"
    }
}
```

#### 1.3 获取诊断问题

**GET** `/diagnosis/questions/{report_id}/`

获取系统生成的诊断问题列表。

**请求参数**
| 参数 | 类型 | 位置 | 说明 |
|------|------|------|------|
| report_id | String | Path | 诊断报告ID |

**响应示例**
```json
{
    "code": 200,
    "message": "获取成功",
    "data": {
        "questions": [
            {
                "id": 1,
                "content": "请问患者是否有头痛症状？",
                "type": "boolean",
                "created_at": "2025-04-03T10:25:30Z"
            }
        ]
    }
}
```

#### 1.4 提交问题答案

**POST** `/diagnosis/questions/{question_id}/answer/`

提交诊断问题的答案。

**请求体**
```json
{
    "content": "是",
    "additional_info": "经常在早上醒来时发生"
}
```

**响应示例**
```json
{
    "code": 200,
    "message": "回答已记录",
    "data": {
        "answer_id": "13579",
        "created_at": "2025-04-03T10:30:30Z"
    }
}
```

### 2. 医生推荐

#### 2.1 获取推荐医生列表

**GET** `/doctors/recommend/{report_id}/`

基于诊断结果获取推荐医生列表。

**查询参数**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | Integer | 否 | 页码，默认1 |
| size | Integer | 否 | 每页数量，默认10 |

**响应示例**
```json
{
    "code": 200,
    "message": "获取成功",
    "data": {
        "total": 50,
        "page": 1,
        "size": 10,
        "doctors": [
            {
                "id": "24680",
                "name": "张医生",
                "title": "主任医师",
                "hospital": "协和医院",
                "department": "中医科",
                "specialty": "擅长治疗内科疾病",
                "rating": 4.8,
                "patients_count": 1200,
                "match_score": 0.95
            }
        ]
    }
}
```

### 3. 诊断报告

#### 3.1 获取诊断报告

**GET** `/diagnosis/report/{report_id}/`

获取完整的诊断报告内容。

**响应示例**
```json
{
    "code": 200,
    "message": "获取成功",
    "data": {
        "report_id": "12345",
        "status": "completed",
        "diagnosis": {
            "symptoms": ["症状1", "症状2"],
            "possible_diseases": ["疾病1", "疾病2"],
            "tcm_patterns": ["证型1", "证型2"]
        },
        "treatment_plan": "详细的治疗建议",
        "created_at": "2025-04-03T11:00:30Z",
        "updated_at": "2025-04-03T11:30:30Z"
    }
}
```

## 错误代码

| 错误码 | 说明 |
|--------|------|
| 400 | 请求参数错误 |
| 401 | 未授权访问 |
| 403 | 访问被拒绝 |
| 404 | 资源不存在 |
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |
