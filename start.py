#!/usr/bin/env python3
"""
AIPPT 服务启动脚本
懒人启动方式: python start.py
"""
import uvicorn

if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   🚀 AIPPT API Server                                         ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    print("📖 API文档: http://localhost:8000/docs")
    print("🔍 健康检查: http://localhost:8000/health")
    print("🔗 OpenAPI: http://localhost:8000/openapi.json")
    print("")

    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
