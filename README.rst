======================
Resolwe SDK for Python
======================

|build| |build-e2e| |coverage| |docs| |pypi_version| |pypi_pyversions|

.. |build| image:: https://travis-ci.org/genialis/resolwe-bio-py.svg?branch=master
    :target: https://travis-ci.org/genialis/resolwe-bio-py
    :alt: Build Status

.. |build-e2e| image:: https://public.ci.genialis.io/buildStatus/icon/resolwe-bio-py/master
    :target: https://ci.genialis.io/blue/organizations/jenkins/resolwe-bio-py/activity
    :alt: Build (End-to-End) Status

.. |coverage| image:: https://img.shields.io/codecov/c/github/genialis/resolwe-bio-py/master.svg
    :target: http://codecov.io/github/genialis/resolwe-bio-py?branch=master
    :alt: Coverage Status

.. |docs| image:: https://readthedocs.org/projects/resdk/badge/?version=latest
    :target: http://resdk.readthedocs.io/
    :alt: Documentation Status

.. |pypi_version| image:: https://img.shields.io/pypi/v/resdk.svg
    :target: https://pypi.python.org/pypi/resdk
    :alt: Version on PyPI

.. |pypi_pyversions| image:: https://img.shields.io/pypi/pyversions/resdk.svg
    :target: https://pypi.python.org/pypi/resdk
    :alt: Supported Python versions

.. |pypi_downloads| image:: https://img.shields.io/pypi/dm/resdk.svg
    :target: https://pypi.python.org/pypi/resdk
    :alt: Number of downloads from PyPI

Resolwe SDK for Python supports interaction with Resolwe_ server
and its extension `Resolwe Bioinformatics`_. You can use it to upload
and inspect biomedical data sets, contribute annotations, run
analysis, and write pipelines.

.. _Resolwe Bioinformatics: https://github.com/genialis/resolwe-bio
.. _Resolwe: https://github.com/genialis/resolwe

Docs & Help
===========

Read the detailed description in documentation_.

.. _documentation: http://resdk.readthedocs.io/

Install
=======

Install from PyPI::

  pip install resdk

If you use macOS, be aware that the version of `Python shipped with the
system doesn't support TLSv1.2`_, which is required for connecting to
any ``genialis.com`` server (and probably others). To solve the issue,
install the latest version of Python 3.6+ `via official
installer from Python.org`_ or `with Homebrew`_.

.. _`Python shipped with the system doesn't support TLSv1.2`:
    http://pyfound.blogspot.si/2017/01/time-to-upgrade-your-python-tls-v12.html
.. _`via official installer from Python.org`:
    https://www.python.org/downloads/mac-osx/
.. _`with Homebrew`:
    http://docs.python-guide.org/en/latest/starting/install/osx/

If you would like to contribute to the SDK codebase, follow the
`installation steps for developers`_.

.. _installation steps for developers: http://resdk.readthedocs.io/en/latest/contributing.html

Quick Start
===========

In this showcase we will download the aligned reads and their
index (BAM and BAI) from the server:

.. code-block:: python

   import resdk

   # Create a Resolwe object to interact with the server
   res = resdk.Resolwe(url='https://app.genialis.com')

   # Enable verbose logging to standard output
   resdk.start_logging()

   # Get sample meta-data from the server
   sample = res.sample.get('resdk-example')

   # Download files associated with the sample
   sample.download()

Both files (BAM and BAI) have downloaded to the working directory.
Check them out. To learn more about the Resolwe SDK continue with
`Getting started`_.

.. _Getting started: http://resdk.readthedocs.io/en/latest/tutorials.html

If you do not have access to the Resolwe server, contact us at
info@genialis.com.
