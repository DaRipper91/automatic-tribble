from setuptools import setup, find_packages

setup(
    name="termux-file-manager",
    version="0.1.0",
    description="A TUI for Termux that manages files and folders across Termux and Android shared folders",
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
        ],
    },
    python_requires=">=3.8",
)
