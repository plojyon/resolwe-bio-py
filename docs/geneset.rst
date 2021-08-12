.. _geneset:

========
Genesets
========

Geneset is a special kind of ``Data`` resource. In addition to all of
the functionality of ``Data``, it also has ``genes`` attribute and
support for set-like operations (intersection, union, etc...).

In the most common case, genesets exist somewhere on Resolwe
server and user just fetches them::

    # Get one geneset by slug
    gs = res.geneset.get("my-slug")

    # Get all human genesets in a given collection:
    genesets = res.geneset.filter(collection=<my-collection>, species="Homo sapiens"):

What one gets is an object (or list of them) of type ``Geneset``. This
object has all the attributes of ``Data`` plus some additional ones::

    # Set of genes in the geneset:
    gs.genes
    # Source of genes, e.g. ENSEMBL, UCSC, NCBI...
    gs.source
    # Species of the genes in the geneset
    gs.species

A common thing to do with ``Geneset`` objects is to perform set-like
operations on them to create new ``Geneset``. This is easily done with
exactly the same syntax as for Python ``set`` objects::

    gs1 = res.geneset.get("slug-1")
    gs2 = res.geneset.get("slug-2")

    # Union
    gs3 = gs1 | gs2
    # Intersection
    gs3 = gs1 & gs2
    # Difference
    gs3 = gs1 - gs2

.. note::

  Performing these operations is only possible on genesets that have equal values
  of ``species`` and ``source`` attribute. Otherwise newly created sets would not
  make sense and would be inconsistent.

So far, geneset ``gs3`` only exists locally. One can easily save it to Resolwe server::

    gs3.save()
    # As with Data, it is a good practice to include it in a collection:
    gs3.collection = <my_collection>
    gs.save()

Alternative way of creating genesets is to use
``Resolwe.geneset.create`` method. In such case, you need to enter the
``genes``, ``species`` and ``source`` information manually::

    res.geneset.create(genes=["MYC", "FHT"], source="UCSC", species="Homo sapiens")

