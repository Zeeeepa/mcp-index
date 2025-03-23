"""
服务端包
提供MCP代码检索服务的服务端实现
"""

# 不要在包初始化时直接导入模块，避免循环导入问题
# 改为在需要时导入

# 导出主要函数，方便用户直接从包中导入
from .unified_server import (
    initialize_components,
    setup_routes,
    run_rest_api,
    run_mcp_server,
    main
)

__all__ = [
    "initialize_components",
    "setup_routes",
    "run_rest_api",
    "run_mcp_server",
    "main"
]

# 定义懒加载函数
def main(*args, **kwargs):
    from .app import main as app_main
    return app_main(*args, **kwargs)

def setup_routes(*args, **kwargs):
    from .api import setup_routes as api_setup_routes
    return api_setup_routes(*args, **kwargs)