
import time
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from openai import OpenAI


class ConversionMode(Enum):
    """转换模式"""
    FILE = 'file'
    FOLDER = 'folder'


class FixMethod(Enum):
    """修复方法"""
    DIRECT = 'direct'  # 直接转换成功
    AUTO_FIX = 'auto_fix'  # convert.js自动修复
    LLM = 'llm'  # LLM智能修复
    SKIPPED = 'skipped'  # 跳过
    FAILED = 'failed'  # 失败


@dataclass
class TokenStats:
    """Token使用统计"""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    def __add__(self, other):
        """支持统计累加"""
        return TokenStats(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            total_tokens=self.total_tokens + other.total_tokens
        )


@dataclass
class ConversionResult:
    """单个文件转换结果"""
    file: str
    success: bool
    method: Optional[FixMethod] = None
    error: Optional[str] = None
    tokens: TokenStats = field(default_factory=TokenStats)


@dataclass
class BatchConversionStats:
    """批量转换统计"""
    total: int = 0
    success: int = 0
    failed: int = 0
    skipped: int = 0
    direct: int = 0
    llm: int = 0
    failed_files: List[Dict] = field(default_factory=list)
    skipped_files: List[Dict] = field(default_factory=list)
    total_tokens: TokenStats = field(default_factory=TokenStats)
    elapsed_time: float = 0.0


@dataclass
class ServiceConfig:
    """服务配置"""
    # API配置
    api_key: str = ''
    api_base_url: str = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
    model_name: str = 'deepseek-v3.2-exp'

    # 转换参数
    backup_html: bool = False
    skip_failed_files: bool = True
    enable_llm_fix: bool = True
    request_interval: float = 1.0
    timeout: int = 120

    # 系统提示词
    system_prompt: str = """你是一个专业的HTML格式规范化助手。你的任务是修复HTML文件使其能成功转换为PPTX，确保：

1. HTML主容器尺寸严格为1600x900px（16:9比例），所有内容需在容器内的安全边距范围内显示，垂直方向和水平方向均不得溢出
2. 所有元素正确定位和显示，不能有任何文字和图表被其他元素遮挡
3. 保持合理的DOM层级结构（最多嵌套5层，遵循语义化标签优先原则，如标题用h1-h3、段落用p、列表用ul/ol等）
4. 保持视觉层次清晰（标题与正文字体大小差异≥4px，重要信息用加粗/更大字号突出，次要信息用常规字号，通过间距区分不同模块）
5. 文本元素不能有边框、背景、阴影（只有DIV可以有）

6. **目录页布局优化**
- 章节数小于等于3，均匀分布在页面中部，避免顶部或底部堆积
- 章节数大于3，分两列排列，左侧列3个，右侧列剩余章节，确保整体平衡美观

7. 标题约束

- **主标题**：最多20个中文字符或40个英文字符
- **副标题**：最多15个中文字符或30个英文字符
- **章节标题**：最多12个中文字符或24个英文字符

8. 图表 (Charts)

**强制要求：**

1. **图表占位符容器**:

    - 必须创建一个 `div` 作为图表的占位符容器。
    - 这个 `div` **必须** 包含 `class="placeholder"`，以便 `html2pptx.js` 脚本能识别其位置。
    - 这个 `div` **必须** 有一个唯一的 `id`，例如 `id="chart-placeholder-1"`，以便截图工具能精确定位到它。

2. **Canvas 元素**:

    - 在图表占位符容器 (`placeholder` div) **内部**，放置一个 `<canvas>` 元素用于绘制图表。
    - `<canvas>` 元素应设置样式以填充其父容器，例如 `style="width: 100%; height: 100%;"`。
    - `<canvas>` 需要一个唯一的 `id`，例如 `id="chart_canvas_1"`。

3. **Chart.js 脚本**:
    - 照常编写 Chart.js 的 `<script>` 块，使用 `<canvas>` 的 `id` 来获取上下文并绘制图表。
    - **重要**: 在 Chart.js 的 `options` 配置中，**必须**设置 `animation: false`，以确保截图时图表是静态的。

4. **图表准确性检查**:
    - 验证使用的图表类型是否为Chart.js支持的类型（如line、bar、pie、doughnut、radar、polarArea、bubble、scatter等），禁止使用Chart.js不支持的图表类型
    - 检查图表配置项是否符合Chart.js语法规范，确保数据结构、标签定义等无语法错误

9. 布局适配检查

- 检查容器高度是否足够容纳所有内容
- 验证文字是否会溢出指定区域
- 确保图片占位符比例正确
- 80px安全边距正确设置，内容不贴边

10. 文字精简

1. **删除冗余词汇**：去掉"的"、"了"、"着"等助词
2. **使用简洁表达**：用词精准，避免重复
3. **数字化表达**：用数据代替形容词
4. **关键词突出**：保留核心概念，删除修饰语

11. 布局优化策略

1. **垂直空间管理**：合理分配标题、内容、留白比例
2. **水平空间利用**：避免单行文字过长导致换行
3. **视觉层次控制**：通过字体大小差异减少文字密度感

## **注意事项**

- 确保元素完全在主容器范围内
- 严格验证内容不溢出主容器边界,预留安全边距：内容需在主容器（1600x900px）内的安全区域显示，具体为左右各80px、顶部80px、底部160px，确保内容不超出安全边距范围
- 文本正确包裹在语义标签中
- 不使用任何禁止的 CSS 特性
- 布局清晰美观，适合转换为 PowerPoint
- **禁止的输出示例（这些都是错误的）：**
  ❌ "# 宠物市场分析..."
  ❌ "基于您提供的内容，我将创建..."
  ❌ "```html"
  ❌ "## 设计说明"
  ❌ "以下是 HTML 代码："

- **正确的输出格式（唯一正确的格式）：**
  ✅ 直接输出：<!DOCTYPE html><html lang="zh-CN"><head>...

请直接返回修复后的完整HTML代码，不要添加任何解释文字或markdown标记。
"""


class HTML2PPTXService:
    """HTML转PPTX转换服务"""

    def __init__(self, config: Optional[ServiceConfig] = None):
        """
        初始化服务

        Args:
            config: 服务配置，如果为None则使用默认配置
        """
        self.config = config or ServiceConfig()
        self.client: Optional[OpenAI] = None
        self._init_llm_client()

        # 回调函数（用于进度通知）
        self.on_progress: Optional[Callable[[str, Dict], None]] = None

    def _init_llm_client(self):
        """初始化LLM客户端"""
        if not self.config.enable_llm_fix:
            return

        if not self.config.api_key:
            print("⚠️  警告: 未配置API_KEY，LLM修复功能已禁用")
            self.config.enable_llm_fix = False
            return

        try:
            self.client = OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.api_base_url,
                timeout=self.config.timeout
            )
        except Exception as e:
            print(f"⚠️  LLM客户端初始化失败: {e}")
            self.config.enable_llm_fix = False

    def _notify_progress(self, event: str, data: Dict):
        """通知进度"""
        if self.on_progress:
            self.on_progress(event, data)

    def test_html_file(self, html_file: Path) -> Dict:
        """
        测试单个HTML文件是否能成功转换

        Args:
            html_file: HTML文件路径

        Returns:
            {'success': bool, 'error': str or None}
        """
        temp_pptx = html_file.parent / f"temp_{html_file.stem}.pptx"

        try:
            temp_pptx.parent.mkdir(parents=True, exist_ok=True)

            # 获取项目根目录（假设脚本在 script/ 目录下）
            script_dir = Path(__file__).parent
            project_root = script_dir.parent if script_dir.name == 'script' else script_dir

            result = subprocess.run(
                ['node', 'script/convert.js', '--file', str(html_file), '--output', str(temp_pptx)],
                capture_output=True,
                text=True,
                timeout=self.config.timeout,
                encoding='utf-8',
                cwd=project_root
            )

            # 删除临时文件
            if temp_pptx.exists():
                temp_pptx.unlink()

            if result.returncode == 0:
                return {'success': True, 'error': None}

            error_msg = result.stderr.strip() or result.stdout.strip()
            return {'success': False, 'error': error_msg}

        except subprocess.TimeoutExpired:
            if temp_pptx.exists():
                temp_pptx.unlink()
            return {'success': False, 'error': '转换超时'}
        except Exception as e:
            if temp_pptx.exists():
                temp_pptx.unlink()
            return {'success': False, 'error': str(e)}

    def fix_with_llm(self, html_file: Path, error_msg: str) -> tuple[bool, TokenStats]:
        """
        使用LLM修复HTML文件

        Args:
            html_file: HTML文件路径
            error_msg: 错误信息

        Returns:
            (修复是否成功, Token统计)
        """
        token_stats = TokenStats()

        if not self.config.enable_llm_fix or self.client is None:
            return False, token_stats

        try:
            html_content = html_file.read_text(encoding='utf-8')

            # 备份
            if self.config.backup_html:
                backup = html_file.with_suffix(html_file.suffix + '.backup')
                if not backup.exists():
                    backup.write_text(html_content, encoding='utf-8')

            self._notify_progress('llm_fix_start', {'file': html_file.name})

            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[
                    {'role': 'system', 'content': self.config.system_prompt},
                    {'role': 'user', 'content': f"修复此HTML（错误：{error_msg}）：\n{html_content}"}
                ]
            )

            # 提取token统计
            if hasattr(response, 'usage') and response.usage:
                token_stats.input_tokens = getattr(response.usage, 'prompt_tokens', 0)
                token_stats.output_tokens = getattr(response.usage, 'completion_tokens', 0)
                token_stats.total_tokens = getattr(response.usage, 'total_tokens', 0)

            fixed_html = response.choices[0].message.content.strip()

            # 清理LLM输出
            fixed_html = re.sub(r'^```html\s*', '', fixed_html)
            fixed_html = re.sub(r'^```\s*', '', fixed_html)
            fixed_html = re.sub(r'\s*```$', '', fixed_html)

            # 找到HTML开始和结束
            if not fixed_html.startswith('<'):
                match = re.search(r'<', fixed_html)
                if match:
                    fixed_html = fixed_html[match.start():]

            if not fixed_html.endswith('>'):
                idx = fixed_html.rfind('>')
                if idx > 0:
                    fixed_html = fixed_html[:idx + 1]

            html_file.write_text(fixed_html, encoding='utf-8')

            self._notify_progress('llm_fix_complete', {
                'file': html_file.name,
                'tokens': token_stats.total_tokens
            })

            return True, token_stats

        except Exception as e:
            self._notify_progress('llm_fix_error', {
                'file': html_file.name,
                'error': str(e)
            })
            return False, token_stats

    def process_single_html(self, html_file: Path) -> ConversionResult:
        """
        处理单个HTML文件

        Args:
            html_file: HTML文件路径

        Returns:
            ConversionResult对象
        """
        filename = html_file.name
        self._notify_progress('file_start', {'file': filename})

        token_stats = TokenStats()

        # 第一次尝试：直接转换
        self._notify_progress('test_conversion', {'file': filename})
        result = self.test_html_file(html_file)

        if result['success']:
            self._notify_progress('file_complete', {
                'file': filename,
                'method': 'direct'
            })
            return ConversionResult(
                file=filename,
                success=True,
                method=FixMethod.DIRECT,
                tokens=token_stats
            )

        error_msg = result['error']
        self._notify_progress('conversion_failed', {
            'file': filename,
            'error': error_msg
        })

        # LLM修复
        if self.config.enable_llm_fix:
            llm_success, llm_tokens = self.fix_with_llm(html_file, error_msg)
            token_stats = llm_tokens

            if llm_success:
                # 修复后重新测试
                result = self.test_html_file(html_file)
                if result['success']:
                    self._notify_progress('file_complete', {
                        'file': filename,
                        'method': 'llm',
                        'tokens': token_stats.total_tokens
                    })
                    return ConversionResult(
                        file=filename,
                        success=True,
                        method=FixMethod.LLM,
                        tokens=token_stats
                    )
                error_msg = result['error']

        # 修复失败
        method = FixMethod.SKIPPED if not self.config.enable_llm_fix else FixMethod.FAILED

        self._notify_progress('file_failed', {
            'file': filename,
            'method': method.value,
            'error': error_msg
        })

        return ConversionResult(
            file=filename,
            success=False,
            method=method,
            error=error_msg,
            tokens=token_stats
        )

    def convert_file(
            self,
            input_file: str | Path,
            output_file: str | Path
    ) -> ConversionResult:
        """
        转换单个HTML文件为PPTX

        Args:
            input_file: 输入HTML文件路径
            output_file: 输出PPTX文件路径

        Returns:
            ConversionResult对象
        """
        input_path = Path(input_file).resolve()
        output_path = Path(output_file).resolve()

        if not input_path.exists():
            return ConversionResult(
                file=input_path.name,
                success=False,
                method=FixMethod.FAILED,
                error=f"文件不存在: {input_path}"
            )

        # 如果输出路径是目录，自动生成文件名
        if output_path.is_dir():
            output_path = output_path / f"{input_path.stem}.pptx"

        # 处理HTML文件
        result = self.process_single_html(input_path)

        if not result.success:
            return result

        # 转换为PPTX
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            script_dir = Path(__file__).parent
            project_root = script_dir.parent if script_dir.name == 'script' else script_dir

            convert_result = subprocess.run(
                ['node', 'script/convert.js', '--file', str(input_path), '--output', str(output_path)],
                capture_output=True,
                text=True,
                timeout=self.config.timeout,
                encoding='utf-8',
                cwd=project_root
            )

            if convert_result.returncode == 0:
                self._notify_progress('pptx_generated', {'output': str(output_path)})
                return result
            else:
                error = convert_result.stderr.strip() or convert_result.stdout.strip()
                return ConversionResult(
                    file=input_path.name,
                    success=False,
                    method=FixMethod.FAILED,
                    error=f"PPTX生成失败: {error}",
                    tokens=result.tokens
                )

        except Exception as e:
            return ConversionResult(
                file=input_path.name,
                success=False,
                method=FixMethod.FAILED,
                error=f"PPTX生成异常: {str(e)}",
                tokens=result.tokens
            )

    def convert_folder(
            self,
            input_folder: str | Path,
            output_file: str | Path
    ) -> BatchConversionStats:
        """
        转换文件夹中的所有HTML文件并合并为一个PPTX

        Args:
            input_folder: 输入文件夹路径
            output_file: 输出PPTX文件路径

        Returns:
            BatchConversionStats对象
        """
        start_time = time.time()

        folder_path = Path(input_folder).resolve()
        output_path = Path(output_file).resolve()

        # 查找所有HTML文件
        html_files = sorted([
            f for f in folder_path.glob('*.html')
            if '.backup' not in f.name and not f.name.startswith('_skip_')
        ])

        stats = BatchConversionStats(total=len(html_files))

        if not html_files:
            self._notify_progress('no_files', {'folder': str(folder_path)})
            return stats

        self._notify_progress('batch_start', {
            'total': len(html_files),
            'folder': str(folder_path)
        })

        # 处理每个HTML文件
        for i, html_file in enumerate(html_files, 1):
            self._notify_progress('batch_progress', {
                'current': i,
                'total': len(html_files),
                'file': html_file.name
            })

            result = self.process_single_html(html_file)

            # 累计统计
            stats.total_tokens += result.tokens

            if result.success:
                stats.success += 1
                if result.method == FixMethod.DIRECT:
                    stats.direct += 1
                elif result.method == FixMethod.LLM:
                    stats.llm += 1
            elif result.method == FixMethod.SKIPPED:
                stats.skipped += 1
                stats.skipped_files.append({
                    'file': result.file,
                    'error': result.error
                })
            else:
                stats.failed += 1
                stats.failed_files.append({
                    'file': result.file,
                    'error': result.error
                })

                if not self.config.skip_failed_files:
                    self._notify_progress('batch_stopped', {
                        'reason': 'SKIP_FAILED_FILES=False'
                    })
                    break

            # API请求间隔
            if i < len(html_files) and result.tokens.total_tokens > 0:
                time.sleep(self.config.request_interval)

        # 合并为PPTX
        merge_success = self._merge_to_pptx(folder_path, output_path)

        if not merge_success:
            self._notify_progress('merge_failed', {})

        stats.elapsed_time = time.time() - start_time

        self._notify_progress('batch_complete', {
            'stats': stats.__dict__
        })

        return stats

    def _merge_to_pptx(self, folder_path: Path, output_pptx: Path) -> bool:
        """将文件夹中的HTML合并为一个PPTX"""
        try:
            output_pptx.parent.mkdir(parents=True, exist_ok=True)

            script_dir = Path(__file__).parent
            project_root = script_dir.parent if script_dir.name == 'script' else script_dir

            result = subprocess.run(
                ['node', 'script/convert.js', '--folder', str(folder_path), '--output', str(output_pptx)],
                capture_output=True,
                text=True,
                timeout=300,
                encoding='utf-8',
                cwd=project_root
            )

            success = result.returncode == 0

            if success:
                self._notify_progress('merge_success', {'output': str(output_pptx)})
            else:
                error_msg = result.stderr.strip() or result.stdout.strip()
                self._notify_progress('merge_error', {'error': error_msg[:500]})

            return success

        except Exception as e:
            self._notify_progress('merge_exception', {'error': str(e)})
            return False


# ==================== 使用示例 ====================

def example_usage():
    """使用示例"""

    # 1. 创建服务实例
    config = ServiceConfig(
        api_key='sk-ea8d61bdf4d94d6cb3ff6803dbeca6f4',
        enable_llm_fix=True,
        skip_failed_files=True
    )

    service = HTML2PPTXService(config)

    # 2. 设置进度回调（可选）
    def progress_callback(event: str, data: Dict):
        print(f"[{event}] {data}")

    service.on_progress = progress_callback

    # 3. 转换单个文件
    # 项目根目录
    root = Path(__file__).parent.parent.parent.parent.parent.resolve()
    # result = service.convert_file(
    #     input_file=root / 'storage' / '20251204_134543_养鱼知识科普' / 'ppt' / 'slides' / 'slide_01_cover.html',
    #     output_file=root / 'storage' / '20251204_134543_养鱼知识科普' / 'ppt' / 'slides' / 'output' / 'slide_01.pptx'
    # )

    # print(f"转换结果: {result.success}"
    #       f", 方法: {result.method}"
    #       f", 错误: {result.error or '无'}")
    # print(f"使用Token: {result.tokens.total_tokens}")

    # 4. 转换整个文件夹
    stats = service.convert_folder(
        input_folder=root / 'storage' / '20251204_134543_养鱼知识科普' / 'ppt' / 'slides' ,
        output_file=root / 'storage' / '20251204_134543_养鱼知识科普' / 'ppt' / 'slides' / 'output'/ 'all_slides.pptx'
    )

    print(f"总计: {stats.total}, 成功: {stats.success}, 失败: {stats.failed}")
    print(f"Token使用: {stats.total_tokens.total_tokens}")
    print(f"耗时: {stats.elapsed_time:.1f}秒")


if __name__ == '__main__':
    example_usage()
