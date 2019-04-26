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
with open(os.path.join(base_dir, 'resdk', '__about__.py')) as fh:
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
    packages=setuptools.find_packages(
        exclude=['tests', 'tests.*', '*.tests', '*.tests.*']
    ),
    install_requires=(
        'requests>=2.6.0',
        'slumber>=0.7.1',
        'pyyaml>=3.11',
        'wrapt>=1.10.8',
        'pytz>=2018.4',
        'tzlocal>=1.5.1',
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
            'check-manifest',
            'isort',
            'mock==1.3.0',
            'pycodestyle~=2.5.0',
            'pydocstyle~=3.0.0',
            'pylint~=2.3.1',
            'pytest-cov',
            'setuptools_scm',
            'twine',
        ],
    },
    entry_points={
        'console_scripts': [
            'resolwe-upload-reads = resdk.scripts:upload_reads',
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
    ],
    keywords='bioinformatics resolwe bio pipelines dataflow django python sdk',
)
