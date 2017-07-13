from setuptools import setup, find_packages

setup(
    name='todo',
    version='0.0.2',
    description='TODO list for your terminal',
    long_description='Currently missing',
    url='https://github.com/Jonksar/todo',
    author='Joonatan Samuel',
    author_email='none',
    license='none',
    packages=['todo', 'todo.bin'],
    install_requires=['pynacl', 'requests'],
    scripts=['todo/bin/todo']
)