"""
 - 
"""
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from loguru import logger


class SearchStorage:
    """TODO: Add docstring."""

    def __init__(self, base_dir: str = "storage"):
        """
        Args:
            base_dir: 
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        self.current_project_dir: Optional[Path] = None
        self.project_id: Optional[str] = None

    def create_project(self, query: str) -> str:
        """创建新的搜索项目目录结构

        为每个搜索任务创建独立的项目目录，包含所有必要的子目录和元数据文件，
        用于存储整个搜索流程中产生的各种数据文件。

        Args:
            query: 用户输入的搜索查询语句

        Returns:
            str: 生成的唯一项目ID，格式为"时间戳_查询关键词"
        """
        # 1. 生成唯一的项目ID - 时间戳 + 查询关键词摘要
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # 格式：20241209_143052
        query_slug = self._slugify(query)[:30]  # 将查询转换为URL友好格式，限制长度
        self.project_id = f"{timestamp}_{query_slug}"

        # 2. 创建项目根目录
        self.current_project_dir = self.base_dir / self.project_id
        self.current_project_dir.mkdir(exist_ok=True)

        # 3. 创建项目子目录结构
        (self.current_project_dir / "intermediate").mkdir(exist_ok=True)  # 中间处理结果目录
        (self.current_project_dir / "reports").mkdir(exist_ok=True)       # 最终报告目录
        (self.current_project_dir / "search_results").mkdir(exist_ok=True) # 搜索结果目录

        # 4. 创建并保存项目元数据文件
        metadata = {
            "project_id": self.project_id,
            "query": query,
            "created_at": datetime.now().isoformat(),
            "status": "running"
        }
        self.save_metadata(metadata)

        logger.info(f"[SearchStorage] : {self.project_id}")
        return self.project_id

    def save_metadata(self, metadata: Dict[str, Any]):
        """TODO: Add docstring."""
        if not self.current_project_dir:
            return

        metadata_file = self.current_project_dir / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

    def save_task_decomposition(self, decomposition: Dict[str, Any]):
        """TODO: Add docstring."""
        if not self.current_project_dir:
            return

        file_path = self.current_project_dir / "intermediate" / "01_task_decomposition.json"
        self._save_json(file_path, decomposition)
        logger.info(f"[SearchStorage] : {file_path}")

    def save_search_results(self, search_results: Dict[str, Any]):
        """TODO: Add docstring."""
        if not self.current_project_dir:
            return

        file_path = self.current_project_dir / "intermediate" / "02_search_results.json"
        self._save_json(file_path, search_results)

        # 
        text_path = self.current_project_dir / "search_results" / "search_results.txt"
        self._save_search_results_text(text_path, search_results)

        logger.info(f"[SearchStorage] : {file_path}")

    def save_content_evaluation(self, evaluation: Dict[str, Any]):
        """TODO: Add docstring."""
        if not self.current_project_dir:
            return

        file_path = self.current_project_dir / "intermediate" / "03_content_evaluation.json"
        self._save_json(file_path, evaluation)
        logger.info(f"[SearchStorage] : {file_path}")

    def save_refined_subtasks(self, refined_subtasks: list):
        """
        NEW METHOD: Save refined subtask content.
        This stores the analyzed and synthesized content for each subtask.
        """
        if not self.current_project_dir:
            return

        file_path = self.current_project_dir / "intermediate" / "02b_refined_subtasks.json"
        self._save_json(file_path, {"refined_subtasks": refined_subtasks})

        # Also save a human-readable version
        text_path = self.current_project_dir / "search_results" / "refined_subtasks.md"
        self._save_refined_subtasks_markdown(text_path, refined_subtasks)

        logger.info(f"[SearchStorage] : {file_path}")

    def save_search_analysis(self, analysis: Dict[str, Any]):
        """TODO: Add docstring."""
        if not self.current_project_dir:
            return

        file_path = self.current_project_dir / "intermediate" / "04_search_analysis.json"
        self._save_json(file_path, analysis)
        logger.info(f"[SearchStorage] : {file_path}")

    def save_content_synthesis(self, synthesis: Dict[str, Any]):
        """TODO: Add docstring."""
        if not self.current_project_dir:
            return

        file_path = self.current_project_dir / "intermediate" / "05_content_synthesis.json"
        self._save_json(file_path, synthesis)

        # Markdown
        if synthesis.get("report_content"):
            md_path = self.current_project_dir / "reports" / "synthesis_report.md"
            self._save_text(md_path, synthesis["report_content"])

        logger.info(f"[SearchStorage] : {file_path}")

    def save_final_report(self, report: Dict[str, Any], query: str):
        """保存最终报告到文件系统

        根据报告类型（PPT或普通报告）将生成的内容保存为不同格式的文件，
        包括JSON数据、HTML页面、Markdown文档等，并更新项目元数据。

        Args:
            report: 包含报告内容和格式信息的字典
            query: 用户原始查询语句
        """
        if not self.current_project_dir:
            return

        # 1. 保存报告的完整JSON数据到中间文件
        json_path = self.current_project_dir / "intermediate" / "06_final_report.json"
        self._save_json(json_path, report)

        html_path = None

        # 2. 处理PPT类型报告
        if report.get("ppt"):
            ppt_data = report["ppt"]

            # 保存PPT的HTML展示页面
            html_path = self.current_project_dir / "reports" / "FINAL_REPORT.html"
            if report.get("html_content"):
                self._save_text(html_path, report["html_content"])
                logger.info(f"[SearchStorage] 保存PPT HTML文件: {html_path}")

            # 保存PPT的结构化数据
            ppt_json_path = self.current_project_dir / "reports" / "PPT_DATA.json"
            self._save_json(ppt_json_path, ppt_data)
            logger.info(f"[SearchStorage] 保存PPT数据文件: {ppt_json_path}")

            # 保存演讲稿注释文件
            if report.get("speech_notes"):
                # 可读性强的文本格式演讲稿
                speech_notes_path = self.current_project_dir / "reports" / "SPEECH_NOTES.txt"
                speech_content = self._format_speech_notes(report["speech_notes"], ppt_data)
                self._save_text(speech_notes_path, speech_content)
                logger.info(f"[SearchStorage] 保存演讲稿文本: {speech_notes_path}")

                # 结构化的JSON格式演讲稿
                speech_json_path = self.current_project_dir / "reports" / "SPEECH_NOTES.json"
                self._save_json(speech_json_path, {"speech_notes": report["speech_notes"]})
                logger.info(f"[SearchStorage] 保存演讲稿JSON: {speech_json_path}")

        # 3. 处理普通报告类型（研究报告/小说等）
        elif report.get("report"):
            report_data = report["report"]

            # 保存完整的Markdown格式报告
            md_path = self.current_project_dir / "reports" / "FINAL_REPORT.md"
            report_content = self._format_final_report(report_data, query)
            self._save_text(md_path, report_content)

            # 保存报告摘要版本
            summary_path = self.current_project_dir / "reports" / "SUMMARY.md"
            summary_content = self._format_summary_report(report_data, query)
            self._save_text(summary_path, summary_content)

            # 如果有HTML版本，同时保存HTML格式
            if report.get("html_content"):
                html_path = self.current_project_dir / "reports" / "FINAL_REPORT.html"
                self._save_text(html_path, report["html_content"])
                logger.info(f"[SearchStorage] 保存HTML报告: {html_path}")

        # 4. 更新项目元数据，标记为完成状态
        metadata = self.load_metadata()
        if metadata:
            metadata["status"] = "completed"
            metadata["completed_at"] = datetime.now().isoformat()
            metadata["report_path"] = str(self.current_project_dir / "reports" / "FINAL_REPORT.md")
            metadata["output_format"] = report.get("output_format", "md")
            if html_path:
                metadata["html_report_path"] = str(html_path)
            self.save_metadata(metadata)

        logger.info(f"[SearchStorage] 最终报告保存完成: {self.current_project_dir / 'reports' / 'FINAL_REPORT.md'}")

        # 5. 在控制台打印保存结果摘要
        print(f"\n{'='*60}")
        print(f"报告保存完成: {self.current_project_dir}")

        # 根据报告类型显示不同的文件信息
        if report.get("ppt"):
            if html_path:
                print(f"PPT HTML页面: {html_path}")
            ppt_json = self.current_project_dir / "reports" / "PPT_DATA.json"
            if ppt_json.exists():
                print(f"PPT数据文件: {ppt_json}")
            speech_notes_txt = self.current_project_dir / "reports" / "SPEECH_NOTES.txt"
            if speech_notes_txt.exists():
                print(f"演讲稿文本: {speech_notes_txt}")
                print(f"   演讲稿JSON: {self.current_project_dir / 'reports' / 'SPEECH_NOTES.json'}")
        else:
            # 普通报告/小说文件信息
            print(f"完整报告: {self.current_project_dir / 'reports' / 'FINAL_REPORT.md'}")
            if html_path:
                print(f"HTML版本: {html_path}")
            print(f"报告摘要: {self.current_project_dir / 'reports' / 'SUMMARY.md'}")

        print(f"搜索结果: {self.current_project_dir / 'search_results' / 'search_results.txt'}")
        print(f"{'='*60}\n")

    def save_execution_log(self, messages: list):
        """TODO: Add docstring."""
        if not self.current_project_dir:
            return

        log_path = self.current_project_dir / "execution_log.json"
        self._save_json(log_path, {"messages": messages})

        # 
        text_path = self.current_project_dir / "execution_log.txt"
        log_content = self._format_execution_log(messages)
        self._save_text(text_path, log_content)

        logger.info(f"[SearchStorage] : {log_path}")

    def load_metadata(self) -> Optional[Dict[str, Any]]:
        """TODO: Add docstring."""
        if not self.current_project_dir:
            return None

        metadata_file = self.current_project_dir / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def _save_json(self, file_path: Path, data: Dict[str, Any]):
        """JSON"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _save_text(self, file_path: Path, content: str):
        """TODO: Add docstring."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def _save_search_results_text(self, file_path: Path, search_results: Dict[str, Any]):
        """TODO: Add docstring."""
        content = "# \n\n"

        all_content = search_results.get("all_content", [])
        content += f": {len(all_content)} \n\n"
        content += "=" * 80 + "\n\n"

        for i, item in enumerate(all_content, 1):
            content += f"## {i}. {item.get('title', '')}\n\n"
            content += f"**URL**: {item.get('url', 'N/A')}\n\n"
            content += f"****: {item.get('search_query', 'N/A')}\n\n"
            content += f"****: {item.get('subtask_title', 'N/A')}\n\n"
            content += f"****:\n{item.get('content', '')[:500]}...\n\n"
            content += "-" * 80 + "\n\n"

        self._save_text(file_path, content)

    def _save_refined_subtasks_markdown(self, file_path: Path, refined_subtasks: list):
        """
        NEW METHOD: Save refined subtasks in Markdown format for human readability.
        """
        content = f"#  - \n\n"
        content += f": {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        content += f": {len(refined_subtasks)} \n\n"
        content += "=" * 80 + "\n\n"

        for i, subtask in enumerate(refined_subtasks, 1):
            content += f"## {i}. {subtask.get('subtask_title', 'Untitled')}\n\n"
            content += f"**ID**: {subtask.get('subtask_id', 'N/A')}\n\n"

            # Analysis info
            analysis = subtask.get("analysis", {})
            quality_score = analysis.get("quality_score", 0.0)
            content += f"**: {quality_score:.2f}\n\n"

            # Key points
            key_points = subtask.get("key_points", [])
            if key_points:
                content += f"**:**\n"
                for point in key_points:
                    content += f"- {point}\n"
                content += "\n"

            # Refined content
            refined_content = subtask.get("refined_content", "")
            content += f"**:**\n\n{refined_content}\n\n"

            # Metadata
            metadata = subtask.get("metadata", {})
            content += f"**: {metadata.get('results_count', 0)}\n"
            content += f"**: {metadata.get('analysis_quality', 'N/A')}\n\n"

            content += "-" * 80 + "\n\n"

        self._save_text(file_path, content)

    def _format_final_report(self, report_data: Dict[str, Any], query: str) -> str:
        """TODO: Add docstring."""
        content = f"# \n\n"
        content += f"****: {query}\n\n"
        content += f"****: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        content += f"**ID**: {self.project_id}\n\n"
        content += "=" * 80 + "\n\n"

        # 
        report_content = report_data.get("content", "")
        content += report_content

        # 
        content += "\n\n" + "=" * 80 + "\n\n"
        content += "##  \n\n"

        metadata = report_data.get("metadata", {})
        content += f"- ****: {metadata.get('report_type', 'N/A')}\n"
        content += f"- ****: {metadata.get('content_sources', 'N/A')}\n"
        content += f"- ****: {metadata.get('word_count', 'N/A')}\n"
        content += f"- ****: {metadata.get('generation_time', 'N/A')}\n"

        return content

    def _format_summary_report(self, report_data: Dict[str, Any], query: str) -> str:
        """TODO: Add docstring."""
        content = f"# \n\n"
        content += f"****: {query}\n\n"
        content += f"****: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        # 
        report_content = report_data.get("content", "")
        sections = report_data.get("sections", [])

        if sections:
            # 
            for section in sections[:2]:
                content += f"## {section.get('title', '')}\n\n"
                content += f"{section.get('content', '')[:500]}...\n\n"
        else:
            # 1000
            content += report_content[:1000] + "...\n\n"

        content += f"\n\n: `FINAL_REPORT.md`\n"

        return content


    def _format_execution_log(self, messages: list) -> str:
        """TODO: Add docstring."""
        content = "# \n\n"
        content += f"****: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        content += "=" * 80 + "\n\n"

        for i, msg in enumerate(messages, 1):
            agent = msg.get("agent", "Unknown")
            msg_content = msg.get("content", "")

            content += f"## {i}. {agent}\n\n"
            content += f"{msg_content}\n\n"
            content += "-" * 80 + "\n\n"

        return content

    def _format_speech_notes(self, speech_notes: list, ppt_data: Dict[str, Any]) -> str:
        """TODO: Add docstring."""
        content = f"# PPT\n\n"
        content += f"**PPT**: {ppt_data.get('title', '')}\n"
        content += f"****: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += f"****: {ppt_data.get('metadata', {}).get('slide_count', 0)}\n\n"
        content += "=" * 80 + "\n\n"

        for note in speech_notes:
            slide_number = note.get("slide_number", 0)
            speech_text = note.get("speech_notes", "")

            content += f"##  {slide_number} \n\n"
            content += f"{speech_text}\n\n"
            content += "-" * 80 + "\n\n"

        return content

    def _slugify(self, text: str) -> str:
        """URLslug"""
        # 
        import re
        text = re.sub(r'[^\w\s-]', '', text)
        # 
        text = re.sub(r'[\s]+', '_', text)
        return text.lower()

    def get_project_dir(self) -> Optional[Path]:
        """TODO: Add docstring."""
        return self.current_project_dir

    def list_projects(self) -> list:
        """TODO: Add docstring."""
        projects = []

        for project_dir in self.base_dir.iterdir():
            if project_dir.is_dir():
                metadata_file = project_dir / "metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        projects.append({
                            "project_id": metadata.get("project_id"),
                            "query": metadata.get("query"),
                            "created_at": metadata.get("created_at"),
                            "status": metadata.get("status"),
                            "path": str(project_dir)
                        })

        # 
        projects.sort(key=lambda x: x["created_at"], reverse=True)
        return projects
