"""
实时图表包安装配置
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="realtime-chart-package",
    version="2.0.0",
    author="AIDCIS3 Team",
    author_email="team@aidcis3.com",
    description="模块化的实时图表组件包",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/aidcis3/realtime-chart-package",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Visualization",
    ],
    python_requires='>=3.8',
    install_requires=[
        'PySide6>=6.0.0',
        'matplotlib>=3.5.0',
        'numpy>=1.20.0',
        'pandas>=1.3.0',
        'psutil>=5.8.0',
    ],
    extras_require={
        'dev': [
            'pytest>=6.0',
            'pytest-qt>=4.0',
            'playwright>=1.20.0',
            'pytest-playwright>=0.3.0',
        ],
    },
)