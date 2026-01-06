"""
图片处理器 - 负责在Markdown内容中智能插入图片

主要功能:
1. 支持多种图片插入模式（智能、顶部、底部、分布）
2. 基于alt文本的智能匹配
3. 生成图片画廊和元数据
4. 增强搜索结果的视觉效果
"""

from typing import List, Dict, Any, Optional
from loguru import logger
import re


class ImageProcessor:
    """
    图片处理器 - 提供多种策略将图片智能插入到Markdown内容中

    支持根据内容语义、图片描述等信息进行智能匹配和布局
    """

    @staticmethod
    def insert_images_to_content(
        content: str,
        images: List[Dict[str, Any]],
        mode: str = "smart"
    ) -> str:
        """
        将图片列表按指定模式插入到Markdown内容中

        Args:
            content: 原始Markdown内容
            images: 图片信息列表 [{"url": "", "alt": "", "width": 0, "height": 0}, ...]
            mode: 插入模式
                - "smart": 基于alt文本智能匹配段落
                - "top": 所有图片插入到内容顶部
                - "bottom": 所有图片插入到内容底部
                - "distribute": 均匀分布到各段落之间
                - "none": 不插入图片

        Returns:
            插入图片后的Markdown内容
        """
        # 如果没有图片或模式为none，直接返回原内容
        if not images or mode == "none":
            logger.debug(f"[图片处理器] 跳过图片插入 - 图片数量: {len(images) if images else 0}, 模式: {mode}")
            return content

        logger.info(f"[图片处理器] 开始图片插入 - 模式: {mode}, 图片数量: {len(images)}")

        # 根据模式选择相应的插入策略
        if mode == "top":
            result = ImageProcessor._insert_images_at_top(content, images)
        elif mode == "bottom":
            result = ImageProcessor._insert_images_at_bottom(content, images)
        elif mode == "distribute":
            result = ImageProcessor._distribute_images(content, images)
        elif mode == "smart":
            result = ImageProcessor._smart_insert_images(content, images)
        else:
            logger.warning(f"[图片处理器] 未识别的插入模式: {mode}，使用默认模式(bottom)")
            result = ImageProcessor._insert_images_at_bottom(content, images)

        logger.debug(f"[图片处理器] 图片插入完成 - 内容长度: {len(content)} -> {len(result)}")
        return result

    @staticmethod
    def _insert_images_at_top(content: str, images: List[Dict[str, Any]]) -> str:
        """
        将所有图片作为画廊插入到内容顶部

        适用于希望优先展示图片的场景
        """
        logger.debug(f"[图片处理器] 顶部插入模式 - 生成 {len(images)} 张图片的画廊")
        image_markdown = ImageProcessor._generate_image_gallery(images, title="相关图片")
        return f"{image_markdown}\n\n{content}"

    @staticmethod
    def _insert_images_at_bottom(content: str, images: List[Dict[str, Any]]) -> str:
        """
        将所有图片作为画廊插入到内容底部

        适用于补充说明或参考资料的场景
        """
        logger.debug(f"[图片处理器] 底部插入模式 - 生成 {len(images)} 张图片的画廊")
        image_markdown = ImageProcessor._generate_image_gallery(images, title="相关图片")
        return f"{content}\n\n{image_markdown}"

    @staticmethod
    def _distribute_images(content: str, images: List[Dict[str, Any]]) -> str:
        """
        将图片均匀分布到内容的各个段落之间

        根据段落数量和图片数量计算合理的插入间隔
        """
        if not images:
            return content

        # 按双换行符分割内容为段落
        paragraphs = content.split('\n\n')
        logger.debug(f"[图片处理器] 分布插入模式 - 段落数: {len(paragraphs)}, 图片数: {len(images)}")

        if len(paragraphs) <= 1:
            # 内容太短，无法分布，改用底部插入
            logger.debug(f"[图片处理器] 段落数过少，改用底部插入模式")
            return ImageProcessor._insert_images_at_bottom(content, images)

        # 计算图片插入间隔，确保均匀分布
        interval = max(1, len(paragraphs) // (len(images) + 1))
        logger.debug(f"[图片处理器] 计算插入间隔: 每 {interval} 个段落插入一张图片")

        result_parts = []
        image_index = 0

        for i, para in enumerate(paragraphs):
            result_parts.append(para)

            # 按间隔插入图片
            if image_index < len(images) and (i + 1) % interval == 0:
                img = images[image_index]
                img_md = ImageProcessor._format_single_image(img)
                result_parts.append(img_md)
                logger.debug(f"[图片处理器] 在第 {i+1} 个段落后插入图片: {img.get('alt', '无描述')[:30]}...")
                image_index += 1

        # 将剩余图片追加到末尾
        while image_index < len(images):
            img_md = ImageProcessor._format_single_image(images[image_index])
            result_parts.append(img_md)
            logger.debug(f"[图片处理器] 追加剩余图片: {images[image_index].get('alt', '无描述')[:30]}...")
            image_index += 1

        return '\n\n'.join(result_parts)

    @staticmethod
    def _smart_insert_images(content: str, images: List[Dict[str, Any]]) -> str:
        """
        基于内容语义智能插入图片

        算法逻辑：
        1. 分析图片的alt描述文本，提取关键词
        2. 将关键词与段落内容进行匹配
        3. 在最相关的段落后插入对应图片
        4. 未匹配的图片统一放在文末画廊中
        """
        if not images:
            return content

        # 按段落分割内容
        paragraphs = content.split('\n\n')
        logger.debug(f"[图片处理器] 智能插入模式 - 段落数: {len(paragraphs)}, 图片数: {len(images)}")

        if len(paragraphs) <= 1:
            logger.debug(f"[图片处理器] 段落数过少，改用底部插入模式")
            return ImageProcessor._insert_images_at_bottom(content, images)

        inserted_images = set()  # 记录已插入的图片索引
        result_parts = []
        match_count = 0

        for para_idx, para in enumerate(paragraphs):
            result_parts.append(para)

            # 为每个段落尝试匹配图片
            for img_idx, img in enumerate(images):
                if img_idx in inserted_images:
                    continue

                # 提取并分析图片的alt描述
                alt = img.get('alt', '').lower()
                para_lower = para.lower()

                if alt and len(alt) > 3:
                    # 从alt中提取有意义的关键词（长度>2的单词）
                    keywords = [w for w in re.findall(r'\w+', alt) if len(w) > 2]

                    # 检查关键词是否在段落中出现
                    if keywords and any(kw.lower() in para_lower for kw in keywords):
                        # 找到匹配，插入图片
                        img_md = ImageProcessor._format_single_image(img)
                        result_parts.append(img_md)
                        inserted_images.add(img_idx)
                        match_count += 1

                        matched_keywords = [kw for kw in keywords if kw.lower() in para_lower]
                        logger.debug(
                            f"[图片处理器] 智能匹配成功 - 段落 {para_idx+1}, "
                            f"图片: {alt[:30]}..., 匹配关键词: {matched_keywords}"
                        )
                        break  # 每个段落最多插入一张图片

        logger.info(f"[图片处理器] 智能匹配完成 - 成功匹配: {match_count}/{len(images)} 张图片")

        # 将未匹配的图片生成画廊追加到文末
        remaining_images = [img for i, img in enumerate(images) if i not in inserted_images]
        if remaining_images:
            logger.debug(f"[图片处理器] 生成未匹配图片画廊 - {len(remaining_images)} 张图片")
            gallery = ImageProcessor._generate_image_gallery(
                remaining_images,
                title="其他相关图片"
            )
            result_parts.append(gallery)

        return '\n\n'.join(result_parts)

    @staticmethod
    def _format_single_image(img: Dict[str, Any]) -> str:
        """
        将单张图片格式化为Markdown语法

        包含图片URL、alt描述和元数据信息
        """
        # 优先使用本地路径，其次使用网络URL
        local_path = img.get('local_path', '')
        url = img.get('url', '')
        image_url = local_path if local_path else url

        alt = img.get('alt', '图片')
        width = img.get('width', 0)
        height = img.get('height', 0)

        # 获取图片来源信息
        source = img.get('source', '')
        photographer = img.get('photographer', '')

        # 生成基础Markdown图片语法
        img_md = f"![{alt}]({image_url})"

        # 添加图片元数据信息
        metadata_parts = []
        if width and height:
            metadata_parts.append(f"尺寸: {width}x{height}")
        if photographer:
            metadata_parts.append(f"作者: {photographer}")
        if source:
            metadata_parts.append(f"来源: {source}")

        if metadata_parts:
            img_md += f"\n*{' | '.join(metadata_parts)}*"

        return img_md

    @staticmethod
    def _generate_image_gallery(
        images: List[Dict[str, Any]],
        title: str = "图片画廊"
    ) -> str:
        """
        生成图片画廊的Markdown格式

        为图片列表创建有序的展示画廊，包含编号、描述和元数据
        """
        if not images:
            logger.debug(f"[图片处理器] 图片列表为空，跳过画廊生成")
            return ""

        logger.debug(f"[图片处理器] 生成图片画廊 - 标题: {title}, 图片数量: {len(images)}")

        parts = [f"## {title}\n"]

        for i, img in enumerate(images, 1):
            # 获取图片URL，优先本地路径
            local_path = img.get('local_path', '')
            url = img.get('url', '')
            image_url = local_path if local_path else url

            alt = img.get('alt', f'图片 {i}')
            width = img.get('width', 0)
            height = img.get('height', 0)
            photographer = img.get('photographer', '')
            photographer_url = img.get('photographer_url', '')

            # 添加图片标题和编号
            parts.append(f"### {i}. {alt if alt else f'图片 {i}'}")
            parts.append(f"![{alt}]({image_url})")

            # 添加图片元数据
            metadata_parts = []
            if width and height:
                metadata_parts.append(f"尺寸: {width}x{height}")
            if photographer:
                if photographer_url:
                    metadata_parts.append(f"摄影师: [{photographer}]({photographer_url})")
                else:
                    metadata_parts.append(f"摄影师: {photographer}")

            if metadata_parts:
                parts.append(f"*{' | '.join(metadata_parts)}*")

            parts.append("")  # 添加空行分隔

        return '\n'.join(parts)

    @staticmethod
    def enhance_search_results_with_images(
        results: List[Dict[str, Any]],
        mode: str = "smart"
    ) -> List[Dict[str, Any]]:
        """
        为搜索结果批量插入图片，增强内容的视觉效果

        Args:
            results: 搜索结果列表
            mode: 图片插入模式

        Returns:
            增强后的搜索结果列表
        """
        if not results:
            logger.debug(f"[图片处理器] 搜索结果为空，跳过图片增强")
            return []

        logger.info(f"[图片处理器] 开始增强搜索结果 - 结果数量: {len(results)}, 插入模式: {mode}")

        enhanced_results = []
        processed_count = 0
        images_inserted_count = 0

        for result_idx, result in enumerate(results):
            enhanced_result = result.copy()

            # 获取内容和图片信息
            full_content = result.get('full_content', '')
            images = result.get('images', [])

            if full_content and images:
                logger.debug(
                    f"[图片处理器] 处理第 {result_idx + 1} 个结果 - "
                    f"内容长度: {len(full_content)}, 图片数: {len(images)}"
                )

                # 执行图片插入处理
                enhanced_content = ImageProcessor.insert_images_to_content(
                    full_content,
                    images,
                    mode=mode
                )
                enhanced_result['full_content'] = enhanced_content
                enhanced_result['images_inserted'] = True
                enhanced_result['image_insert_mode'] = mode

                processed_count += 1
                images_inserted_count += len(images)

                logger.debug(
                    f"[图片处理器] 成功插入 {len(images)} 张图片到结果: "
                    f"'{result.get('title', '无标题')[:40]}...'"
                )
            else:
                enhanced_result['images_inserted'] = False
                if not full_content:
                    logger.debug(f"[图片处理器] 跳过第 {result_idx + 1} 个结果 - 无内容")
                elif not images:
                    logger.debug(f"[图片处理器] 跳过第 {result_idx + 1} 个结果 - 无图片")

            enhanced_results.append(enhanced_result)

        logger.info(
            f"[图片处理器] 搜索结果增强完成 - "
            f"处理结果: {processed_count}/{len(results)}, "
            f"插入图片总数: {images_inserted_count}"
        )

        return enhanced_results
