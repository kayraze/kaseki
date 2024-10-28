from setuptools import setup, find_packages

setup(
    name="kaseki",
    version="0.3.0",
    packages=find_packages(),
    install_requires=[
        # List dependencies here, e.g., 'requests'
        "paramiko",
        "termcolor",
    ],
    entry_points={
        'console_scripts': [
            'kaseki=kaseki.main:main',  # Links 'your-tool' command to main() in your_tool/main.py
        ],
    },
)