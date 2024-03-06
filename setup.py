from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='fastfiz_renderer',
    version='0.0.1',
    packages=find_packages(),
    license='MIT',
    install_requires=requirements,
    py_modules=['fastfiz_renderer']
)
