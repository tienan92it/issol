from setuptools import setup, find_packages

setup(
    name='issol',
    version='0.3.2',
    packages=find_packages(),
    install_requires=[
        'PyGithub',
        'anthropic',
        'gitpython',
    ],
    entry_points={
        'console_scripts': [
            'issol=issol.cli:main',
        ],
    },
    python_requires='>=3.6',
)