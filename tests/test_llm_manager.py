import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.llm.manager import llm_manager

# 检查所有可用的配置
info = llm_manager.get_manager_info()
print("可用的配置:", info['available_configs'])

# 检查各个配置的详细信息
for config_name in ['outline_generator', 'content_generator', 'design_coordinator']:
    config = llm_manager.get_config(config_name)
    print(f"\n{config_name}:")
    print(f"  Provider: {config.provider}")
    print(f"  Model: {config.model_name}")
    print(f"  Temperature: {config.temperature}")
    print(f"  Max Tokens: {config.max_tokens}")