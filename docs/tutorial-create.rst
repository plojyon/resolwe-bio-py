.. _tutorial-create:

================================
Create, modify and organize data
================================

To begin, we need some sample data to work with. You may use your own reads
(.fastq) files, or download an example set we have provided:

.. literalinclude:: files/tutorial-create.py
   :lines: 2-13

.. note::

  To avoid copy-pasting of the commands, you can
  :download:`download all the code <files/tutorial-create.py>` used in this section.

Upload files
============

We will upload fastq single end reads with the `upload-fastq-single`_ process.

.. _upload-fastq-single: http://resolwe-bio.readthedocs.io/en/latest/catalog-definitions.html#process-upload-fastq-single

.. literalinclude:: files/tutorial-create.py
   :lines: 15-21

What just happened? First, we chose a process to run, using its slug
``upload-fastq-single``. Each process requires some inputs---in this case there
is only one input with name ``src``, which is the location of reads on our
computer. Uploading a fastq file creates a new ``Data`` on the server
containing uploaded reads.

The upload process also created a Sample object for the reads data to be
associated with. You can access it by:

.. literalinclude:: files/tutorial-create.py
   :lines: 23

.. note::

  You can also upload your files by providing url. Just replace path to your
  local files with the url. This comes handy when your files are large and/or
  are stored on a remote server and you don't want to download them to your
  computer just to upload them to Resolwe server again...

Modify data
===========

Both ``Data`` with reads and ``Sample`` are owned by you and you have
permissions to modify them. For example:

.. literalinclude:: files/tutorial-create.py
   :lines: 25-27

Note the ``save()`` part! Without this, the change is only applied locally (on
your computer). But calling ``save()`` also takes care that all changes are
applied on the server.

.. note::

  Some fields cannot (and should not) be changed. For example, you cannot
  modify ``created`` or ``contributor`` fields. You will get an error if you
  try.

Annotate Samples and Data
=========================

The obvious next thing to do after uploading some data is to annotate it.
Annotations are encoded as bundles of descriptors, where each descriptor
references a value in a descriptor schema (*i.e.* a template). Annotations for
data objects, samples, and collections each follow a different descriptor
format. For example, a reads data object can be annotated with the 'reads'
descriptor schema, while a sample can be annotated by the 'sample' annotation
schema. Each data object that is associated with the sample is also connected
to the sample's annotation, so that the annotation for a sample (or collection)
represents all Data objects attached to it. `Descriptor schemas`_ are described
in detail (with `accompanying examples`_) in the
`Resolwe Bioinformatics documentation`_.

.. _Resolwe Bioinformatics documentation: http://resolwe-bio.readthedocs.io
.. _Descriptor schemas: https://resolwe-bio.readthedocs.io/en/latest/descriptor.html
.. _accompanying examples: https://github.com/genialis/resolwe-bio/tree/master/resolwe_bio/descriptors

Here, we show how to annotate the ``reads`` data object by defining the
descriptor information that populates the annotation fields as defined in the
'reads' descriptor schema:

.. literalinclude:: files/tutorial-create.py
   :lines: 29-38

We can annotate the sample object using a similar process with a 'sample'
descriptor schema:

.. literalinclude:: files/tutorial-create.py
   :lines: 40-55

.. warning::

    Many descriptor schemas have required fields with a limited set of choices
    that may be applied as annotations. For example, the 'species' annotation
    in a sample descriptor must be selected from the list of options in the
    `sample descriptor schema`_, represented by its Latin name.

.. _sample descriptor schema: https://github.com/genialis/resolwe-bio/blob/master/resolwe_bio/descriptors/sample.yml

We can also define descriptors and descriptor schema directly when calling
``res.run`` function. This is described in the section about the ``run()``
method below.

Organize resources
==================

After uploading a set of reads/samples, one typically wants to group and
organize them. So let's create a collection and put some data inside!

.. literalinclude:: files/tutorial-create.py
   :lines: 57-64

Run analyses
============

Various bioinformatic processes are available to properly analyze sequencing
data. Many of these pipelines are available via Resolwe SDK, and are listed in
the `Process catalog`_ of the `Resolwe Bioinformatics documentation`_.

.. _Process catalog: http://resolwe-bio.readthedocs.io/en/latest/catalog.html
.. _Resolwe Bioinformatics documentation: http://resolwe-bio.readthedocs.io

After uploading reads file, the next step is to align reads to a genome. We
will use STAR aligner, which is wrapped in a process with slug
``alignment-star``. Inputs and outputs of this process are described in
`STAR process catalog`_. We will define input files and the process will run
its algorithm that transforms inputs into outputs.

.. _STAR process catalog: https://resolwe-bio.readthedocs.io/en/latest/catalog-definitions.html#process-alignment-star

.. literalinclude:: files/tutorial-create.py
   :lines: 67-76

Lets take a closer look to the code above. We defined the alignment process, by
its slug ``'alignment-star'``. For inputs we defined data objects ``reads``
and ``genome``. ``Reads`` object was created with 'upload-fastq-single'
process, while ``genome`` data object was already on the server and we just
used its slug to identify it. The ``alignment-star`` processor will
automatically take the right files from data objects, specified in inputs and
create output files: ``bam`` alignment file, ``bai`` index and some more...

You probably noticed that we get the result almost instantly, while the
typical assembling process runs for hours. This is because
processing runs asynchronously, so the returned data object does not
have an OK status or outputs when returned.

.. literalinclude:: files/tutorial-create.py
   :lines: 78-85

Status ``OK`` indicates that processing has finished successfuly, but you will
also find other statuses. They are given with two-letter abbreviations. To
understand their meanings, check the
:obj:`status reference <resdk.resources.Data.status>`. When processing is done,
all outputs are witten to disk and you can inspect them:

.. literalinclude:: files/tutorial-create.py
   :lines: 87-88

Unitl now, we used ``run()`` method twice: to upload reads (yes, uploading
files is just a matter of using an upload process) and to run alignment. You
can check the full signature of the :obj:`run() <resdk.Resolwe.run>` method.

Run workflows
=============

Typical data analysis is often a sequence of processes. Raw data or initial
input is analysed by running a process on it that outputs some data. This data
is fed as input into another process that produces another set of outputs. This
output is then again fed into another process and so on. Sometimes, this
sequence is so commonly used that one wants to simplify it's execution. This
can be done by using so called "workflow". Workflows are special processes that
run a stack of processes. On the outside, they look exactly the same as a
normal process and have a process slug, inputs... For example, we
can run workflow "General RNA-seq pipeline" on our reads:

.. literalinclude:: files/tutorial-create.py
   :lines: 90-102

Solving problems
================

Sometimes the data object will not have an "OK" status. In such case, it is
helpful to be able to check what went wrong (and where). The :obj:`stdout()
<resdk.resources.Data.stdout>` method on data objects can help---it returns the
standard output of the data object (as string). The output is long but
exceedingly useful for debugging. Also, you can inspect the info, warning and
error logs.

.. literalinclude:: files/tutorial-create.py
   :lines: 104-117
