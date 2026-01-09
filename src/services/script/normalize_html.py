#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML to PPTX 智能转换工具
替代 smart_convert.js，支持自动错误检测和修复

工作流程：
1. 遍历文件夹中的所有HTML文件
2. 对每个文件尝试转换，LLM可选修复
3. 所有文件处理完后，合并为一个PPTX
"""

import time
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Optional
from openai import OpenAI


# ==================== 配置区域 ====================
class CONFIG:
    # 运行模式: 'file' 或 'folder'
    MODE = 'folder'

    # 输入路径
    INPUT_PATH = '../../../../storage/20260105_105735_步行健身进阶计划从日常散步到减脂健走的方法/ppt/slides/'

    # 输出路径
    # folder模式：PPTX文件路径
    # file模式：输出文件夹路径
    OUTPUT_PATH = '../../../../storage/20260105_105735_步行健身进阶计划从日常散步到减脂健走的方法/ppt/slides/output/allput.pptx'

    # 转换参数
    BACKUP_HTML = False  # 是否备份HTML
    SKIP_FAILED_FILES = True  # 跳过无法修复的文件继续处理
    ENABLE_LLM_FIX = False  # 是否启用LLM智能修复

    # API配置（仅在ENABLE_LLM_FIX=True时需要）
    # API_KEY = 'sk-ea8d61bdf4d94d6cb3ff6803dbeca6f4'
    # API_BASE_URL = 'https://dashscope.aliyuncs.com/compatible-mode/v1'

    API_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    API_KEY = 'sk-ea8d61bdf4d94d6cb3ff6803dbeca6f4'
    MODEL_NAME = 'deepseek-v3.2-exp'

    # TEMPERATURE = 0.1
    REQUEST_INTERVAL = 1

    SYSTEM_PROMPT = """你是一个专业的HTML格式规范化助手。你的任务是修复HTML文件使其能成功转换为PPTX，确保：

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


# 初始化客户端（仅在启用LLM时）
client = None
if CONFIG.ENABLE_LLM_FIX:
    try:
        client = OpenAI(
            api_key=CONFIG.API_KEY,
            base_url=CONFIG.API_BASE_URL,
            timeout=120
        )
    except Exception as e:
        print(f"⚠️  LLM客户端初始化失败: {e}")
        CONFIG.ENABLE_LLM_FIX = False


def convert_html(html_file: Path, output_pptx: Path = None, keep_pptx: bool = False) -> Dict:
    """转换HTML为PPTX

    Args:
        html_file: HTML文件路径
        output_pptx: 输出路径（若keep_pptx=True则保留，否则用临时路径）
        keep_pptx: 是否保留生成的PPTX

    Returns:
        {'success': bool, 'error': str|None, 'pptx_path': str|None, 'warn': str|None}
    """
    temp_pptx = output_pptx if (keep_pptx and output_pptx) else html_file.parent / f"temp_{html_file.stem}.pptx"

    def cleanup():
        if not keep_pptx and temp_pptx.exists():
            temp_pptx.unlink()

    try:
        temp_pptx.parent.mkdir(parents=True, exist_ok=True)

        result = subprocess.run(
            ['node', 'script/convert.js', '--file', str(html_file), '--output', str(temp_pptx)],
            capture_output=True, text=True, timeout=120, encoding='utf-8',
            cwd=Path(__file__).parent.parent
        )

        cleanup()

        # 检查转换成功
        combined = (result.stdout or "") + "\n" + (result.stderr or "")
        success_markers = ["成功转换", "PPTX 文件已保存", "✓ 成功转换", "PPTX文件已保存"]

        if result.returncode == 0 or any(m in combined for m in success_markers):
            return {
                'success': True,
                'error': None,
                'pptx_path': str(temp_pptx) if keep_pptx else None,
                'warn': combined.strip() if result.returncode != 0 else None
            }

        return {'success': False, 'error': result.stderr.strip() or result.stdout.strip(), 'pptx_path': None}

    except subprocess.TimeoutExpired:
        cleanup()
        return {'success': False, 'error': '转换超时', 'pptx_path': None}
    except Exception as e:
        cleanup()
        return {'success': False, 'error': str(e), 'pptx_path': None}


def fix_with_llm(html_file: Path, error_msg: str) -> tuple[bool, Dict]:
    """使用LLM修复，返回修复结果和token统计"""
    token_stats = {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}

    # 检查是否启用LLM修复
    if not CONFIG.ENABLE_LLM_FIX:
        return False, token_stats

    # 检查客户端是否初始化成功
    if client is None:
        return False, token_stats

    try:
        html_content = html_file.read_text(encoding='utf-8')

        # 备份
        if CONFIG.BACKUP_HTML:
            backup = html_file.with_suffix(html_file.suffix + '.backup')
            if not backup.exists():
                backup.write_text(html_content, encoding='utf-8')

        response = client.chat.completions.create(
            model=CONFIG.MODEL_NAME,
            messages=[
                {'role': 'system', 'content': CONFIG.SYSTEM_PROMPT},
                {'role': 'user', 'content': f"修复此HTML（错误：{error_msg}）：\n{html_content}"}
            ],
            # temperature=CONFIG.TEMPERATURE
        )

        # 提取token使用统计
        if hasattr(response, 'usage') and response.usage:
            token_stats['input_tokens'] = getattr(response.usage, 'prompt_tokens', 0)
            token_stats['output_tokens'] = getattr(response.usage, 'completion_tokens', 0)
            token_stats['total_tokens'] = getattr(response.usage, 'total_tokens', 0)

        fixed_html = response.choices[0].message.content.strip()

        # 清理LLM输出
        fixed_html = re.sub(r'^```html\s*', '', fixed_html)
        fixed_html = re.sub(r'^```\s*', '', fixed_html)
        fixed_html = re.sub(r'\s*```$', '', fixed_html)

        # 找到HTML开始
        if not fixed_html.startswith('<'):
            match = re.search(r'<', fixed_html)
            if match:
                fixed_html = fixed_html[match.start():]

        # 找到HTML结束
        if not fixed_html.endswith('>'):
            idx = fixed_html.rfind('>')
            if idx > 0:
                fixed_html = fixed_html[:idx + 1]

        html_file.write_text(fixed_html, encoding='utf-8')
        return True, token_stats

    except Exception as e:
        print(f"    LLM修复异常: {e}")
        return False, token_stats


def process_single_html(html_file: Path, index: int, total: int, output_dir: Path = None) -> Dict:
    """处理单个HTML文件，返回处理结果和token统计"""
    print(f"\n[{index}/{total}] {html_file.name}")

    # 确定输出路径
    output_pptx = output_dir / f"{html_file.stem}.pptx" if output_dir else None
    keep_pptx = bool(output_dir)

    # 尝试直接转换
    print(f"  {'转换' if keep_pptx else '测试转换'}...", end=' ')
    result = convert_html(html_file, output_pptx, keep_pptx)

    tokens = {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}

    if result['success']:
        print("✓")
        if result.get('warn'):
            print(f"  ⚠️ 警告: {result['warn'][:600]}")

        # 将成功的HTML文件复制到临时目录（用于后续合并）
        if output_dir:
            import shutil
            dest_html = output_dir / html_file.name
            shutil.copy2(html_file, dest_html)

        return {'file': html_file.name, 'success': True, 'method': 'direct', 'error': None,
                'tokens': tokens, 'pptx_path': result.get('pptx_path')}

    # 转换失败
    print(f"✗\n  错误: {result['error']}")

    # 尝试LLM修复
    if not CONFIG.ENABLE_LLM_FIX:
        print("  ⏭️  LLM修复已禁用")
        return {'file': html_file.name, 'success': False, 'method': 'skipped',
                'error': result['error'], 'tokens': tokens, 'pptx_path': None}

    print("  LLM修复...", end=' ')
    llm_success, tokens = fix_with_llm(html_file, result['error'])

    if not llm_success:
        print("✗")
        return {'file': html_file.name, 'success': False, 'method': None,
                'error': result['error'], 'tokens': tokens, 'pptx_path': None}

    # LLM修复成功，重新转换
    print(f"✓ (tokens: {tokens['total_tokens']})")
    print(f"  重新{'转换' if keep_pptx else '测试'}...", end=' ')
    result = convert_html(html_file, output_pptx, keep_pptx)

    if result['success']:
        print("✓")

        # 将成功的HTML文件复制到临时目录（用于后续合并）
        if output_dir:
            import shutil
            dest_html = output_dir / html_file.name
            shutil.copy2(html_file, dest_html)

        return {'file': html_file.name, 'success': True, 'method': 'llm', 'error': None,
                'tokens': tokens, 'pptx_path': result.get('pptx_path')}

    print(f"✗\n  ✗ LLM无法修复\n  {result['error']}")
    return {'file': html_file.name, 'success': False, 'method': None,
            'error': result['error'], 'tokens': tokens, 'pptx_path': None}


def process_folder(folder_path: Path, output_pptx: Path) -> Dict:
    """处理文件夹模式，返回统计信息"""
    html_files = sorted([f for f in folder_path.glob('*.html')
                         if '.backup' not in f.name and not f.name.startswith('_skip_')])

    if not html_files:
        print("✗ 未找到HTML文件")
        return {'total': 0, 'success': 0, 'failed': 0, 'skipped': 0, 'direct': 0, 'llm': 0,
                'failed_files': [], 'skipped_files': [],
                'total_tokens': 0, 'total_input_tokens': 0, 'total_output_tokens': 0}

    print(f"\n📂 找到 {len(html_files)} 个HTML文件")
    print(
        f"{'🔧 修复策略: convert.js内置auto_fix → LLM智能修复' if CONFIG.ENABLE_LLM_FIX else '⚙️  修复策略: 仅convert.js内置auto_fix，跳过LLM修复'}")

    # 统计信息
    stats = {
        'total': len(html_files), 'success': 0, 'failed': 0, 'skipped': 0,
        'direct': 0, 'llm': 0,
        'failed_files': [], 'skipped_files': [],
        'total_tokens': 0, 'total_input_tokens': 0, 'total_output_tokens': 0
    }

    # 创建临时目录存放单页PPTX
    temp_dir = folder_path / '_temp_pptx'
    temp_dir.mkdir(exist_ok=True)
    successful_htmls = []

    # 处理每个HTML文件
    for i, html_file in enumerate(html_files, 1):
        result = process_single_html(html_file, i, len(html_files), temp_dir)

        # 累计token统计
        tokens = result.get('tokens', {})
        stats['total_tokens'] += tokens.get('total_tokens', 0)
        stats['total_input_tokens'] += tokens.get('input_tokens', 0)
        stats['total_output_tokens'] += tokens.get('output_tokens', 0)

        # 分类统计
        if result['success']:
            stats['success'] += 1
            successful_htmls.append(result['file'])
            stats['direct' if result['method'] == 'direct' else 'llm'] += 1
        elif result['method'] == 'skipped':
            stats['skipped'] += 1
            stats['skipped_files'].append({'file': result['file'], 'error': result['error']})
        else:
            stats['failed'] += 1
            stats['failed_files'].append({'file': result['file'], 'error': result['error']})
            if not CONFIG.SKIP_FAILED_FILES:
                print("\n✗ 停止处理（SKIP_FAILED_FILES=False）")
                break

        # API间隔
        if i < len(html_files) and tokens.get('total_tokens', 0) > 0:
            time.sleep(CONFIG.REQUEST_INTERVAL)

    # 合并单页PPTX
    if successful_htmls:
        print(f"\n{'=' * 60}\n合并单页PPTX...\n{'=' * 60}")
        try:
            output_pptx.parent.mkdir(parents=True, exist_ok=True)
            result = subprocess.run(
                ['node', 'script/convert.js', '--folder', str(temp_dir), '--output', str(output_pptx)],
                capture_output=True, text=True, timeout=300, encoding='utf-8',
                cwd=Path(__file__).parent.parent
            )
            if result.returncode == 0:
                print(f"✓ 合并成功: {output_pptx}")
            else:
                print(f"✗ 合并失败: {(result.stderr or result.stdout).strip()[:550]}")
        except Exception as e:
            print(f"✗ 合并出错: {e}")
    else:
        print("\n⚠️  没有成功转换的文件，跳过合并")

    # 清理临时目录
    try:
        import shutil
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
    except:
        pass

    return stats


def process_file(html_file: Path, output_pptx: Path) -> tuple[bool, Dict]:
    """处理单文件模式"""
    print(f"\n处理文件: {html_file.name}")
    result = process_single_html(html_file, 1, 1)
    tokens = result.get('tokens', {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0})

    if not result['success']:
        print("\n✗ 文件无法转换")
        return False, tokens

    # 转换为PPTX
    print("\n生成PPTX...", end=' ')
    try:
        output_pptx.parent.mkdir(parents=True, exist_ok=True)
        conv = subprocess.run(
            ['node', 'script/convert.js', '--file', str(html_file), '--output', str(output_pptx)],
            capture_output=True, text=True, timeout=120, encoding='utf-8',
            cwd=Path(__file__).parent.parent
        )

        if conv.returncode == 0:
            print(f"✓\n输出: {output_pptx}")
            return True, tokens

        print(f"✗\n{conv.stderr if conv.stderr else ''}")
        return False, tokens
    except Exception as e:
        print(f"✗ {e}")
        return False, tokens


def main():
    """主函数"""
    sep = '=' * 60
    print(f'\n{sep}\n  HTML to PPTX 智能转换工具\n{sep}')
    print(f"模式: {CONFIG.MODE} | 输入: {CONFIG.INPUT_PATH}\n输出: {CONFIG.OUTPUT_PATH}")
    print(f"修复: convert.js内置 + {'LLM智能修复' if CONFIG.ENABLE_LLM_FIX else 'LLM禁用'}\n{sep}")

    start_time = time.time()

    try:
        if CONFIG.MODE == 'file':
            input_file = Path(CONFIG.INPUT_PATH).resolve()
            output_pptx = Path(CONFIG.OUTPUT_PATH).resolve()

            if not input_file.exists():
                print(f"\n✗ 文件不存在: {input_file}")
                return

            if output_pptx.is_dir():
                output_pptx = output_pptx / f"{input_file.stem}.pptx"

            success, tokens = process_file(input_file, output_pptx)
            elapsed = time.time() - start_time

            print(f"\n{sep}\n{'✓ 成功' if success else '✗ 失败'} | 耗时: {elapsed:.1f}秒")
            if tokens['total_tokens'] > 0:
                print(
                    f"Token: {tokens['total_tokens']} (输入:{tokens['input_tokens']}, 输出:{tokens['output_tokens']})")
            print(sep)

        else:
            input_folder = Path(CONFIG.INPUT_PATH).resolve()
            output_pptx = Path(CONFIG.OUTPUT_PATH).resolve()

            if not input_folder.exists():
                print(f"\n✗ 文件夹不存在: {input_folder}")
                return

            if not output_pptx.suffix:
                output_pptx = output_pptx / 'qwen_code_merged.pptx'

            stats = process_folder(input_folder, output_pptx)
            elapsed = time.time() - start_time

            # 统计报告
            print(f"\n{sep}\n  转换统计报告\n{sep}")
            print(f"总数: {stats['total']} | 成功: {stats['success']} (auto_fix:{stats['direct']}, LLM:{stats['llm']})")
            if stats['skipped'] > 0:
                print(f"跳过: {stats['skipped']} | 失败: {stats['failed']}")
            else:
                print(f"失败: {stats['failed']}")
            print(f"耗时: {elapsed:.1f}秒 | 成功率: {stats['success'] / stats['total'] * 100:.0f}%" if stats[
                                                                                                           'total'] > 0 else "")

            # Token统计
            if stats['total_tokens'] > 0:
                print(
                    f"Token: {stats['total_tokens']} (输入:{stats['total_input_tokens']}, 输出:{stats['total_output_tokens']})")
                if stats['total_tokens'] > 1000:
                    cost = (stats['total_input_tokens'] * 0.001 + stats['total_output_tokens'] * 0.002) / 1000
                    print(f"预估成本: ¥{cost:.4f}")

            # 详情
            if stats['skipped_files']:
                print("\n⏭️  跳过文件:")
                for f in stats['skipped_files']:
                    print(f"  • {f['file']}")

            if stats['failed_files']:
                print("\n❌ 失败文件:")
                for f in stats['failed_files']:
                    print(f"  • {f['file']}")
                    if f['error']:
                        print(f"    {f['error'][:300]}")

            print(sep)

            # 总结
            s = stats['success']
            if s == stats['total']:
                print("🎉 全部成功!")
            elif s > 0:
                print(f"✅ {s}/{stats['total']} 成功")
                if stats['skipped'] > 0:
                    print(f"⏭️  {stats['skipped']} 跳过")
                if stats['failed'] > 0:
                    print(f"❌ {stats['failed']} 失败")
            else:
                print("❌ 全部失败")

    except KeyboardInterrupt:
        print(f"\n\n⚠️  用户中断")
    except Exception as e:
        print(f"\n\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
