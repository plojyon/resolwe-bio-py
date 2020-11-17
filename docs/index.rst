
.. _index:

======================
Resolwe SDK for Python
======================

Resolwe SDK for Python supports interaction with `Genialis Server`_. Genialis Server is based on Resolwe_ workflow engine
and its plugin `Resolwe Bioinformatics`_. You can use it to upload
and inspect biomedical data sets, contribute annotations and run
analysis.

.. _Genialis server: https://app.genialis.com
.. _Resolwe Bioinformatics: https://github.com/genialis/resolwe-bio
.. _Resolwe: https://github.com/genialis/resolwe

Install
=======

Install from PyPI::

  pip install resdk

.. TODO: Remove this warning when not needed anymore: Miha, Domen is this still relevant?
.. warning::

   If you use macOS, be aware that the version of `Python shipped with the
   system doesn't support TLSv1.2`_, which is required for connecting to
   any Genialis Server (and probably others). To solve the issue,
   install the latest version of Python 3.6+ `via official
   installer from Python.org`_ or `with Homebrew`_.

.. _`Python shipped with the system doesn't support TLSv1.2`:
    http://pyfound.blogspot.si/2017/01/time-to-upgrade-your-python-tls-v12.html
.. _`via official installer from Python.org`:
    https://www.python.org/downloads/mac-osx/
.. _`with Homebrew`:
    http://docs.python-guide.org/en/latest/starting/install/osx/

If you would like to contribute to the SDK code base, follow the
:ref:`installation steps for developers <contributing>`.

Usage example
=============

We will download a sample containing raw sequencing reads that were aligned to
a genome:

.. literalinclude:: files/index.py
   :lines: 2-

Multiple files (fastq, fastQC report, bam, bai...) have downloaded to the
working directory. Check them out. To learn more about the Resolwe SDK continue
with :doc:`tutorials`.

If you have problems connecting to our server, please contact us at
info@genialis.com.

Documentation
=============

.. toctree::
   :maxdepth: 2

   start
   tutorials
   topical
   ref
   contributing
