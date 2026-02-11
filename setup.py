from setuptools import setup, find_packages

setup(
    name="termux-file-manager",
    version="0.1.0",
    description="A TUI file manager for managing files and folders",
    author="DaRipper91",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "textual>=0.47.0",
        "rich>=13.7.0",
    ],
    entry_points={
        "console_scripts": [
            "tfm=file_manager.app:main",
            "tfm-auto=file_manager.cli:main",
        ],
    },
    python_requires=">=3.8",
)
