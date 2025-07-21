#!/usr/bin/env python3
"""
工业内窥镜图像处理系统安装配置
"""

from setuptools import setup, find_packages
import os

# 读取README文件
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# 读取requirements文件
def read_requirements():
    requirements = []
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#"):
                requirements.append(line)
    return requirements

setup(
    name="industrial-endoscope-processor",
    version="1.0.0",
    author="工业内窥镜图像处理团队",
    author_email="your-email@example.com",
    description="专为工业内窥镜检测设计的高性能图像处理系统",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/industrial-endoscope-processor",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Manufacturing",
        "Topic :: Scientific/Engineering :: Image Recognition",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=read_requirements(),
    extras_require={
        "gpu": ["torch[cuda]", "torchvision[cuda]"],
        "dev": ["pytest", "black", "flake8", "mypy"],
        "docs": ["sphinx", "sphinx-rtd-theme"],
    },
    entry_points={
        "console_scripts": [
            "endoscope-processor=main:main",
            "endoscope-batch=image_batch_processor:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.json"],
    },
    keywords="endoscope, image-processing, computer-vision, industrial-inspection",
    project_urls={
        "Bug Reports": "https://github.com/your-username/industrial-endoscope-processor/issues",
        "Source": "https://github.com/your-username/industrial-endoscope-processor",
        "Documentation": "https://github.com/your-username/industrial-endoscope-processor/wiki",
    },
) 