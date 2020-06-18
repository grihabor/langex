from setuptools import setup, find_packages

setup(
    name='langex',
    version='0.0.1',
    author='Borodin Gregory',
    author_email='grihabor@gmail.com',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    install_requires=[
        'beautifulsoup4==4.9',
        'requests',
        'click',
    ]
)