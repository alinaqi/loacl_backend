from setuptools import find_packages, setup

setup(
    name="loacl",
    version="0.1.0",
    packages=find_packages(),
    package_dir={"": "src"},
    install_requires=[
        "fastapi>=0.109.2",
        "uvicorn[standard]>=0.27.1",
        "supabase>=2.3.4",
        "python-dotenv>=1.0.1",
        "pydantic>=2.6.1",
        "pydantic-settings>=2.1.0",
        "openai>=1.12.0",
        "structlog>=24.1.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-asyncio>=0.23.5",
            "httpx>=0.24.0",
            "black>=24.1.1",
            "isort>=5.13.2",
            "pylint>=3.0.3",
            "mypy>=1.8.0",
        ]
    },
)
