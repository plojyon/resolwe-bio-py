.. _contributing:

============
Contributing
============

Installing prerequisites
========================

Make sure you have Python_ 3.6+ installed on your system. If you don't
have it yet, follow `these instructions
<https://docs.python.org/3/using/index.html>`__.

.. _Python: https://www.python.org/

Preparing environment
=====================

`Fork <https://help.github.com/articles/fork-a-repo>`__ the main
`Resolwe SDK for Python git repository`_.

If you don't have Git installed on your system, follow `these
instructions <http://git-scm.com/book/en/v2/Getting-Started-Installing-Git>`__.

Clone your fork (replace ``<username>`` with your GitHub account name) and
change directory::

    git clone https://github.com/<username>/resolwe-bio-py.git
    cd resolwe-bio-py

Prepare Resolwe SDK for Python for development::

    pip install -e .[docs,package,test]

.. note::

    We recommend using `venv <http://docs.python.org/3/library/venv.html>`_
    to create an isolated Python environment.

.. _Resolwe SDK for Python git repository: https://github.com/genialis/resolwe-bio-py

Running tests
=============

Run unit tests::

    py.test

Coverage report
===============

To see the tests' code coverage, use::

    py.test --cov=resdk

To generate an HTML file showing the tests' code coverage, use::

    py.test --cov=resdk --cov-report=html

Building documentation
======================

.. code-block:: none

    python setup.py build_sphinx

Preparing release
=================

Checkout the latest code and create a release branch::

    git checkout master
    git pull
    git checkout -b release-<new-version>

Replace the *Unreleased* heading in ``docs/CHANGELOG.rst`` with the new
version, followed by release's date (e.g. *13.2.0 - 2018-10-23*).

Commit changes to git::

    git commit -a -m "Prepare release <new-version>"

Push changes to your fork and open a pull request::

    git push --set-upstream <resdk-fork-name> release-<new-version>

Wait for the tests to pass and the pull request to be approved. Merge the code
to master::

    git checkout master
    git merge --ff-only release-<new-version>
    git push <resdk-upstream-name> master <new-version>

Tag the new release from the latest commit::

    git checkout master
    git tag -sm "Version <new-version>" <new-version>

Push the tag to the main ReSDK's git repository::

    git push <resdk-upstream-name> master <new-version>

Now you can release the code on PyPI. Clean ``build`` directory::

    python setup.py clean -a

Remove previous distributions in ``dist`` directory::

    rm dist/*

Remove previous ``egg-info`` directory::

    rm -r *.egg-info

Create source distribution::

    python setup.py sdist

Build wheel::

    python setup.py bdist_wheel

Upload distribution to PyPI::

    twine upload dist/*
