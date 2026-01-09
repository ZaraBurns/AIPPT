"""
PPT相关API数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class PPTStyle(str, Enum):
    """PPT风格枚举"""
    BUSINESS = "business"
    ACADEMIC = "academic"
    CREATIVE = "creative"
    SIMPLE = "simple"
    EDUCATIONAL = "educational"
    TECH = "tech"
    NATURE = "nature"
    MAGAZINE = "magazine"
    TED = "ted"


# ==================== 请求模型 ====================

class PPTOutlineRequest(BaseModel):
    """PPT大纲生成请求"""
    topic: str = Field(..., min_length=1, max_length=200, description="PPT主题")
    style: PPTStyle = Field(default=PPTStyle.BUSINESS, description="PPT风格")
    slides: int = Field(default=10, ge=1, le=50, description="幻灯片数量")
    custom_materials: Optional[str] = Field(
        default=None,
        max_length=10000,
        description="自定义参考资料，支持文档解析、用户整理的资料、联网搜索结果等，最大10000字符"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "topic": "量子计算的技术突破",
                "style": "tech",
                "slides": 8,
                "custom_materials": "最新研究表明，量子计算机在2024年实现了重要突破：1. IBM推出了1000+量子比特处理器；2. Google实现了量子纠错新方法；3. 中国在量子通信领域取得领先优势。"
            }
        }


class PPTGenerateRequest(PPTOutlineRequest):
    """PPT生成请求"""
    include_speech_notes: bool = Field(default=False, description="是否包含演讲稿")
    convert_to_pptx: bool = Field(default=True, description="是否转换为PPTX")

    class Config:
        json_schema_extra = {
            "example": {
                "topic": "2024年新能源汽车市场分析",
                "style": "business",
                "slides": 12,
                "include_speech_notes": False,
                "custom_materials": "根据中国汽车工业协会数据：1. 2024年新能源汽车销量达到950万辆，同比增长40%；2. 比亚迪、特斯拉、蔚来占据市场份额前三；3. 动力电池成本下降至100元/kWh以下；4. 充电桩数量突破300万台；5. 出口量突破500万辆。",
                "convert_to_pptx": True
            }
        }


class ConversionRequest(BaseModel):
    """转换为PPTX请求"""
    enable_llm_fix: bool = Field(default=True, description="是否启用LLM修复")
    skip_failed_files: bool = Field(default=True, description="是否跳过失败的文件")

    class Config:
        json_schema_extra = {
            "example": {
                "enable_llm_fix": True,
                "skip_failed_files": True
            }
        }


class GenerateFromOutlineRequest(BaseModel):
    """从大纲生成PPT请求"""
    outline: Dict[str, Any] = Field(..., description="PPT大纲数据（JSON格式）")
    style: PPTStyle = Field(default=PPTStyle.BUSINESS, description="PPT风格")
    include_speech_notes: bool = Field(default=False, description="是否包含演讲稿")
    convert_to_pptx: bool = Field(default=True, description="是否转换为PPTX")
    custom_materials: Optional[str] = Field(
        default=None,
        max_length=10000,
        description="自定义参考资料，支持文档解析、用户整理的资料、联网搜索结果等，最大10000字符"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "outline": {
                    "title": "2024年全球气候变化报告",
                    "subtitle": "数据分析与趋势预测",
                    "colors": {
                        "primary": "#2d6a4f",
                        "accent": "#52b788",
                        "background": "#ffffff",
                        "text": "#1b4332",
                        "secondary": "#74c69d"
                    },
                    "pages": [
                        {
                            "slide_number": 1,
                            "page_type": "title",
                            "title": "2024年全球气候变化报告",
                            "key_points": [],
                            "has_chart": False,
                            "has_image": True,
                            "description": "封面页",
                            "chart_config": None,
                            "image_config": [{"type": "photo", "query": "climate change earth"}]
                        },
                        {
                            "slide_number": 2,
                            "page_type": "content",
                            "title": "全球气温上升趋势",
                            "key_points": ["2024年平均气温", "温室气体排放", "极端天气事件"],
                            "has_chart": True,
                            "has_image": False,
                            "description": "展示气温数据和趋势"
                        }
                    ]
                },
                "style": "academic",
                "include_speech_notes": False,
                "convert_to_pptx": True,
                "custom_materials": "根据NASA和NOAA数据：2024年全球平均气温比工业化前水平上升1.3°C，接近《巴黎协定》1.5°C警戒线。极端天气事件增加20%，包括热浪、干旱和洪水。温室气体浓度达历史新高，CO2浓度突破420ppm。"
            }
        }


# ==================== 响应模型 ====================

class PPTOutlineResponse(BaseModel):
    """PPT大纲生成响应"""
    outline: Dict[str, Any] = Field(description="PPT大纲数据")
    estimated_slides: int = Field(description="预估幻灯片数量")
    estimated_time: str = Field(description="预估生成时间")

    class Config:
        json_schema_extra = {
            "example": {
                "outline": {
                    "title": "人工智能的发展趋势",
                    "pages": [...]
                },
                "estimated_slides": 10,
                "estimated_time": "3-5分钟"
            }
        }


class PPTGenerateResponse(BaseModel):
    """PPT生成响应"""
    project_id: str = Field(description="项目ID")
    ppt_dir: str = Field(description="PPT目录路径")
    total_slides: int = Field(description="总幻灯片数")
    index_page: str = Field(description="导航页路径")
    presenter_page: str = Field(description="演示页路径")
    pptx_file: Optional[str] = Field(default=None, description="PPTX文件路径")
    status: str = Field(description="状态 (completed/failed)")

    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "20250107_143052_人工智能的发展趋势",
                "ppt_dir": "storage/20250107_143052_人工智能的发展趋势/reports/ppt/slides",
                "total_slides": 10,
                "index_page": "storage/.../index.html",
                "presenter_page": "storage/.../presenter.html",
                "pptx_file": "storage/.../output.pptx",
                "status": "completed"
            }
        }


class ConversionResponse(BaseModel):
    """PPTX转换响应"""
    task_id: str = Field(description="任务ID")
    status: str = Field(description="转换状态")
    pptx_path: str = Field(description="PPTX文件路径")
    conversion_stats: Dict[str, Any] = Field(description="转换统计信息")

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "uuid",
                "status": "completed",
                "pptx_path": "storage/.../output.pptx",
                "conversion_stats": {
                    "total": 10,
                    "success": 10,
                    "failed": 0,
                    "elapsed_time": 45.2
                }
            }
        }


class ProjectStatusResponse(BaseModel):
    """项目状态响应"""
    project_id: str = Field(description="项目ID")
    status: str = Field(description="项目状态")
    created_at: str = Field(description="创建时间")
    files: List[str] = Field(description="文件列表")

    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "20250107_143052_人工智能的发展趋势",
                "status": "completed",
                "created_at": "2025-01-07T14:30:00",
                "files": ["index.html", "presenter.html", "output.pptx"]
            }
        }


class DownloadRequest(BaseModel):
    """文件下载请求参数（用于路径参数）"""
    file_type: str = Field(description="文件类型 (html/pptx/all)")
