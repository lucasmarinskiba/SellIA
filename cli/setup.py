from setuptools import setup, find_packages

setup(
    name="sellias-cli",
    version="1.0.0",
    description="SellIA — Automated sales agent CLI",
    author="SellIA Team",
    author_email="support@sellias.com",
    url="https://github.com/lucasmarinskiba/sellias",
    py_modules=["sellias_cli"],
    install_requires=[
        "typer[all]==0.9.0",
        "httpx==0.24.1",
        "click==8.1.7",
    ],
    entry_points={
        "console_scripts": [
            "sellias=sellias_cli:app",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
)
