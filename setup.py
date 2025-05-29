from setuptools import setup

setup(name='py_extractor_calculators',
    version='0.0.1',
    description='....... for PortADa project',
    author='PortADa team',
    author_email='jcbportada@gmail.com',
    license='MIT',
    url="https://github.com/portada-git/py_extractor_calculators",
    packages=['py_extractor_calculators'],
    py_modules=['sm'],
    install_requires=[
        'datetime',
        'difflib'
    ],
    python_requires='>=3.9',
    zip_safe=False)
