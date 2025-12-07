#!/usr/bin/env python3
"""
Quick start script for Seed Voice Conversion V2 API
"""

import os
import sys
import subprocess

def check_requirements():
    """Check if required packages are installed."""
    required_packages = [
        "fastapi",
        "uvicorn",
        "python-multipart",
        "pydantic",
        "requests"
    ]

    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print("缺少以下依赖包:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\n请安装依赖:")
        print("pip install fastapi uvicorn python-multipart pydantic requests")
        return False

    return True

def main():
    """Main function to start the API server."""
    print("Seed Voice Conversion V2 API - 启动器")
    print("=" * 50)

    # Check requirements
    if not check_requirements():
        return

    # Check if api_v2.py exists
    if not os.path.exists("api_v2.py"):
        print("错误: 找不到 api_v2.py 文件")
        print("请确保在正确的目录中运行此脚本")
        return

    # Default arguments
    args = ["python", "api_v2.py"]

    # Parse command line arguments
    if len(sys.argv) > 1:
        args.extend(sys.argv[1:])

    print("启动API服务器...")
    print("命令:", " ".join(args))
    print("=" * 50)

    # Start the API server
    try:
        subprocess.run(args)
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except Exception as e:
        print(f"启动服务器时出错: {e}")

if __name__ == "__main__":
    main()