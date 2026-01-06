"""
图片下载器 - 提供高效的图片下载和优化功能

主要功能:
1. 并发下载网络图片
2. 自动图片格式优化和压缩
3. 本地缓存避免重复下载
4. 支持按项目分类存储
"""

import os
import hashlib
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
from loguru import logger
import httpx
import aiofiles
from PIL import Image
import io


class ImageDownloader:
    """
    图片下载器 - 负责网络图片的下载、优化和本地存储管理

    支持并发下载、自动优化、缓存管理等功能
    """

    def __init__(
        self,
        storage_dir: Optional[Path] = None,
        max_image_size: int = 2048,  # 最大图片尺寸
        quality: int = 85,  # JPEG质量
        max_concurrent_downloads: int = 5
    ):
        """
        初始化图片下载器

        Args:
            storage_dir: 图片存储目录
            max_image_size: 图片压缩后的最大尺寸（像素）
            quality: JPEG压缩质量 (1-100)
            max_concurrent_downloads: 最大并发下载数
        """
        self.storage_dir = storage_dir or Path("storage/images")
        self.max_image_size = max_image_size
        self.quality = quality
        self.max_concurrent_downloads = max_concurrent_downloads
        self.name = "图片下载器"

        # 确保存储目录存在
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # 创建并发控制信号量
        self.semaphore = asyncio.Semaphore(max_concurrent_downloads)

        logger.info(
            f"[{self.name}] 初始化完成 "
            f"(存储目录: {self.storage_dir}, 并发数: {max_concurrent_downloads})"
        )

    async def download_image(
        self,
        url: str,
        filename: Optional[str] = None,
        optimize: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        下载单张图片并保存到本地

        Args:
            url: 图片URL地址
            filename: 保存的文件名（可选）
            optimize: 是否进行图片优化

        Returns:
            下载结果信息字典，失败时返回None
        """
        async with self.semaphore:
            try:
                logger.debug(f"[{self.name}] 开始下载图片: {url[:100]}...")

                # 生成文件名，使用URL哈希值避免重名
                if not filename:
                    url_hash = hashlib.md5(url.encode()).hexdigest()
                    filename = f"{url_hash}.jpg"

                local_path = self.storage_dir / filename

                # 检查本地缓存，避免重复下载
                if local_path.exists():
                    logger.debug(f"[{self.name}] 使用本地缓存: {filename}")
                    return {
                        "url": url,
                        "local_path": str(local_path),
                        "filename": filename,
                        "cached": True
                    }

                # 发起HTTP请求下载图片
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, timeout=30.0, follow_redirects=True)

                    if response.status_code != 200:
                        logger.warning(f"[{self.name}] 下载失败 (状态码{response.status_code}): {url[:50]}...")
                        return None

                    image_data = response.content

                # 如果启用优化，对图片进行压缩处理
                if optimize:
                    image_data = await self._optimize_image(image_data)

                # 保存图片到本地文件
                async with aiofiles.open(local_path, "wb") as f:
                    await f.write(image_data)

                logger.debug(f"[{self.name}] 下载完成: {filename} ({len(image_data)} 字节)")

                return {
                    "url": url,
                    "local_path": str(local_path),
                    "filename": filename,
                    "size": len(image_data),
                    "cached": False
                }

            except Exception as e:
                logger.error(f"[{self.name}] 图片下载失败 {url[:100]}...: {e}")
                return None

    async def download_images(
        self,
        images: List[Dict[str, Any]],
        optimize: bool = True
    ) -> List[Dict[str, Any]]:
        """
        批量下载图片列表

        Args:
            images: 图片信息列表 [{"url": "", "alt": "", ...}, ...]
            optimize: 是否进行图片优化

        Returns:
            包含本地路径信息的增强图片列表
        """
        try:
            logger.info(f"[{self.name}] 开始批量下载 {len(images)} 张图片")

            # 创建并发下载任务
            tasks = []
            for img in images:
                url = img.get("download_url") or img.get("url")
                if url:
                    tasks.append(self.download_image(url, optimize=optimize))

            # 并发执行所有下载任务
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 合并原始图片信息和下载结果
            downloaded_images = []
            for i, img in enumerate(images):
                if i < len(results) and results[i] and not isinstance(results[i], Exception):
                    # 下载成功，合并信息
                    enhanced_img = {
                        **img,
                        **results[i]
                    }
                    downloaded_images.append(enhanced_img)
                else:
                    # 下载失败，保留原始信息
                    downloaded_images.append(img)

            success_count = sum(1 for r in results if r and not isinstance(r, Exception))
            logger.info(f"[{self.name}] 批量下载完成: {success_count}/{len(images)} 张成功")

            return downloaded_images

        except Exception as e:
            logger.error(f"[{self.name}] 批量下载失败: {e}")
            return images

    async def _optimize_image(self, image_data: bytes) -> bytes:
        """
        优化图片：压缩尺寸、转换格式、降低质量

        Args:
            image_data: 原始图片字节数据

        Returns:
            优化后的图片字节数据
        """
        try:
            # 使用PIL打开图片
            img = Image.open(io.BytesIO(image_data))

            # 处理透明通道，将RGBA转换为RGB格式
            if img.mode in ('RGBA', 'LA', 'P'):
                # 创建白色背景合成透明图片
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # 按比例缩放图片，限制最大尺寸
            if max(img.width, img.height) > self.max_image_size:
                if img.width > img.height:
                    new_width = self.max_image_size
                    new_height = int(img.height * (self.max_image_size / img.width))
                else:
                    new_height = self.max_image_size
                    new_width = int(img.width * (self.max_image_size / img.height))

                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # 保存为JPEG格式，应用质量压缩
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=self.quality, optimize=True)
            optimized_data = output.getvalue()

            logger.debug(
                f"[{self.name}] 图片优化完成: "
                f"{len(image_data)} -> {len(optimized_data)} 字节 "
                f"({img.width}x{img.height})"
            )

            return optimized_data

        except Exception as e:
            logger.warning(f"[{self.name}] 图片优化失败，使用原图: {e}")
            return image_data

    async def download_for_project(
        self,
        project_id: str,
        images: List[Dict[str, Any]],
        optimize: bool = True
    ) -> List[Dict[str, Any]]:
        """
        为特定项目下载图片，存储在项目专用目录

        Args:
            project_id: 项目ID
            images: 图片列表
            optimize: 是否优化图片

        Returns:
            下载结果列表
        """
        # 创建项目专用图片目录
        project_image_dir = self.storage_dir / project_id
        project_image_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"[{self.name}] 为项目 {project_id} 下载图片到: {project_image_dir}")

        # 临时切换存储目录
        original_dir = self.storage_dir
        self.storage_dir = project_image_dir

        try:
            result = await self.download_images(images, optimize)
            logger.info(f"[{self.name}] 项目 {project_id} 图片下载完成")
            return result
        finally:
            # 恢复原始存储目录
            self.storage_dir = original_dir

    def clean_old_images(self, days: int = 30):
        """
        清理过期的缓存图片文件

        Args:
            days: 保留天数，超过此天数的图片将被删除
        """
        try:
            import time
            current_time = time.time()
            max_age = days * 86400  # 转换为秒

            logger.info(f"[{self.name}] 开始清理 {days} 天前的缓存图片...")

            cleaned_count = 0
            for file_path in self.storage_dir.glob("**/*.jpg"):
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age:
                    file_path.unlink()
                    cleaned_count += 1

            logger.info(f"[{self.name}] 缓存清理完成，删除了 {cleaned_count} 个过期文件")

        except Exception as e:
            logger.error(f"[{self.name}] 缓存清理失败: {e}")

    def get_storage_size(self) -> int:
        """
        计算存储目录的总大小

        Returns:
            存储目录大小（字节）
        """
        total_size = 0
        try:
            for file_path in self.storage_dir.glob("**/*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size

            # 转换为可读格式进行日志记录
            size_mb = total_size / 1024 / 1024
            logger.debug(f"[{self.name}] 当前存储大小: {size_mb:.2f} MB")

        except Exception as e:
            logger.error(f"[{self.name}] 计算存储大小失败: {e}")

        return total_size
