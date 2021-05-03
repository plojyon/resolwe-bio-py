"""Resolwe SDK for Python.

See: https://github.com/genialis/resolwe-bio-py

"""
import os.path
import setuptools


# Get long description from README.
with open('README.rst') as f:
    long_description = f.read()

# Get package metadata from '__about__.py' file.
about = {}
base_dir = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(base_dir, 'src', 'resdk', '__about__.py')) as fh:
    exec(fh.read(), about)

setuptools.setup(
    name=about['__title__'],
    use_scm_version=True,
    description=about['__summary__'],
    long_description=long_description,
    long_description_content_type='text/x-rst',
    author=about['__author__'],
    author_email=about['__email__'],
    url=about['__url__'],
    license=about['__license__'],
    # Exclude tests from built/installed package.
    packages=setuptools.find_packages("src"),
    package_dir={"": "src"},
    install_requires=(
        'aiohttp',
        # required by aiohttp
        'chardet<=4.0,>=2.0',
        'requests>=2.6.0',
        'slumber>=0.7.1',
        'wrapt',
        'pytz>=2018.4',
        'tzlocal>=1.5.1',
        'pandas>=1.0.0',
        'tqdm',
        'openpyxl',
        'xlrd',
    ),
    python_requires='>=3.6',
    extras_require={
        'docs': [
            'sphinx>=1.4.1',
            'sphinx_rtd_theme>=0.1.9',
        ],
        'package': [
            'twine',
            'wheel',
        ],
        'test': [
            'black>=20.8b0',
            'build<0.3.0',
            'check-manifest',
            'cryptography<3.4',
            'flake8~=3.7.0',
            'isort~=4.3.12',
            'mock',
            'pydocstyle~=3.0.0',
            'pytest-cov',
            'setuptools_scm~=5.0',
            'twine',
        ],
    },
    test_suite='resdk.tests.unit',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    keywords='bioinformatics resolwe bio pipelines dataflow django python sdk',
)
