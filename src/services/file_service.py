"""
文件服务
提供文件操作和下载管理
"""
import os
import zipfile
from pathlib import Path
from typing import Optional, List
from fastapi import HTTPException, status
from fastapi.responses import FileResponse
from loguru import logger


class FileService:
    """
    文件服务

    提供文件下载、验证、压缩等功能。
    注重安全性，防止目录遍历攻击。
    """

    def __init__(self, base_storage_dir: str = "storage"):
        """
        初始化文件服务

        Args:
            base_storage_dir: 基础存储目录
        """
        self.base_storage_dir = Path(base_storage_dir).resolve()
        logger.info(f"文件服务初始化，基础目录: {self.base_storage_dir}")

    def validate_project_id(self, project_id: str) -> Path:
        """
        验证项目ID并返回项目目录

        Args:
            project_id: 项目ID

        Returns:
            项目目录路径

        Raises:
            HTTPException: 如果项目ID无效或项目不存在
        """
        # 防止目录遍历攻击
        if ".." in project_id or "/" in project_id or "\\" in project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的项目ID"
            )

        # 构建项目目录路径
        project_dir = self.base_storage_dir / project_id

        # 验证路径在基础目录内
        try:
            project_dir = project_dir.resolve()
            if not str(project_dir).startswith(str(self.base_storage_dir)):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="非法的项目路径"
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"路径解析失败: {str(e)}"
            )

        # 检查项目是否存在
        if not project_dir.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"项目不存在: {project_id}"
            )

        return project_dir

    def get_pptx_path(self, project_id: str) -> Path:
        """
        获取PPTX文件路径

        Args:
            project_id: 项目ID

        Returns:
            PPTX文件路径

        Raises:
            HTTPException: 如果文件不存在
        """
        project_dir = self.validate_project_id(project_id)
        pptx_file = project_dir / "reports" / "ppt" / "output.pptx"

        if not pptx_file.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PPTX文件不存在，请先生成PPT"
            )

        return pptx_file

    def get_html_path(self, project_id: str) -> Path:
        """
        获取HTML导航页路径

        Args:
            project_id: 项目ID

        Returns:
            HTML文件路径

        Raises:
            HTTPException: 如果文件不存在
        """
        project_dir = self.validate_project_id(project_id)
        index_html = project_dir / "reports" / "ppt" / "index.html"

        if not index_html.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="HTML文件不存在，请先生成PPT"
            )

        return index_html

    def create_pptx_response(self, project_id: str) -> FileResponse:
        """
        创建PPTX文件下载响应

        Args:
            project_id: 项目ID

        Returns:
            FileResponse对象
        """
        pptx_path = self.get_pptx_path(project_id)

        logger.info(f"提供PPTX下载: {project_id} -> {pptx_path.name}")

        return FileResponse(
            path=str(pptx_path),
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            filename=pptx_path.name,
            background=None
        )

    def create_html_response(self, project_id: str) -> FileResponse:
        """
        创建HTML文件下载响应

        Args:
            project_id: 项目ID

        Returns:
            FileResponse对象
        """
        html_path = self.get_html_path(project_id)

        logger.info(f"提供HTML下载: {project_id} -> {html_path.name}")

        return FileResponse(
            path=str(html_path),
            media_type="text/html",
            filename=html_path.name,
            background=None
        )

    def create_zip_response(
        self,
        project_id: str,
        include_pptx: bool = True,
        include_html: bool = True
    ) -> FileResponse:
        """
        创建ZIP压缩包下载响应

        Args:
            project_id: 项目ID
            include_pptx: 是否包含PPTX文件
            include_html: 是否包含HTML文件

        Returns:
            FileResponse对象
        """
        project_dir = self.validate_project_id(project_id)

        # 创建临时ZIP文件
        zip_filename = f"{project_id}.zip"
        zip_path = self.base_storage_dir / zip_filename

        try:
            logger.info(f"创建ZIP压缩包: {project_id}")

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 添加PPTX文件
                if include_pptx:
                    pptx_file = project_dir / "reports" / "ppt" / "output.pptx"
                    if pptx_file.exists():
                        zipf.write(pptx_file, pptx_file.name)
                        logger.debug(f"  添加: {pptx_file.name}")

                # 添加HTML文件
                if include_html:
                    ppt_dir = project_dir / "reports" / "ppt"
                    if ppt_dir.exists():
                        for html_file in ppt_dir.glob("*.html"):
                            arcname = f"slides/{html_file.name}"
                            zipf.write(html_file, arcname)
                            logger.debug(f"  添加: {arcname}")

            logger.info(f"ZIP压缩包创建成功: {zip_path.name}")

            return FileResponse(
                path=str(zip_path),
                media_type="application/zip",
                filename=zip_filename,
                background=None
            )

        except Exception as e:
            # 清理临时文件
            if zip_path.exists():
                zip_path.unlink()

            logger.error(f"创建ZIP失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"创建压缩包失败: {str(e)}"
            )

    def list_project_files(self, project_id: str) -> List[Dict[str, Any]]:
        """
        列出项目的所有文件

        Args:
            project_id: 项目ID

        Returns:
            文件列表
        """
        project_dir = self.validate_project_id(project_id)

        files = []

        # 递归查找所有文件
        for file_path in project_dir.rglob("*"):
            if file_path.is_file():
                # 相对路径
                rel_path = file_path.relative_to(project_dir)
                files.append({
                    "name": file_path.name,
                    "path": str(rel_path),
                    "size": file_path.stat().st_size,
                    "type": file_path.suffix
                })

        return files

    def delete_project(self, project_id: str) -> bool:
        """
        删除项目及其所有文件

        Args:
            project_id: 项目ID

        Returns:
            是否删除成功

        Raises:
            HTTPException: 如果删除失败
        """
        project_dir = self.validate_project_id(project_id)

        try:
            logger.warning(f"删除项目: {project_id} -> {project_dir}")

            # 递归删除目录
            import shutil
            shutil.rmtree(project_dir)

            logger.info(f"项目已删除: {project_id}")
            return True

        except Exception as e:
            logger.error(f"删除项目失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"删除项目失败: {str(e)}"
            )

    def list_all_projects(self) -> List[Dict[str, Any]]:
        """
        列出所有项目

        Returns:
            项目列表
        """
        projects = []

        for project_dir in self.base_storage_dir.iterdir():
            if project_dir.is_dir():
                # 读取元数据
                metadata_file = project_dir / "metadata.json"
                metadata = {}
                if metadata_file.exists():
                    try:
                        import json
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                    except Exception as e:
                        logger.warning(f"读取元数据失败: {e}")

                projects.append({
                    "project_id": project_dir.name,
                    "path": str(project_dir),
                    "created_at": metadata.get("created_at", ""),
                    "status": metadata.get("status", "unknown"),
                    "topic": metadata.get("topic", "")
                })

        # 按创建时间排序
        projects.sort(key=lambda x: x["created_at"], reverse=True)

        return projects
