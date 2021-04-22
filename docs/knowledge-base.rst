.. _knowleedge-base:

==============
Knowledge base
==============

Genialis Knowledge base (KB) is a collection of "features" (genes,
transcripts, ...) and "mappings" between these features. It comes
very handy when performing various tasks with genomic features e.g.:

    - find all aliases of gene ``BRCA2``
    - finding all genes of type ``protein_coding``
    - find all transcripts of gene ``FHIT``
    - converting ``gene_id`` to ``gene_symbol``
    - ...


Feature
=======
``Feature`` object represents a genomic feature: a gene, a transcript, etc.
You can query ``Feature`` objects by ``feature`` endpoint, similarly like
``Data``, ``Sample`` or any other ReSDK resource::

    feature = res.feature.get(feature_id="BRCA2")

To examine all attributes of a ``Feature``, see the :ref:`reference`.
Here we will list a few most commonly used ones::

    # Get the feature:
    feature = res.feature.get(feature_id="BRCA2")

    # Database where this feature is defined, e.g. ENSEMBL, UCSC, NCBI, ...
    feature.source

    # Unique identifier of a feature
    feature.feature_id

    # Feature species
    feature.species

    # Feature type, e.g. gene, transcript, exon, ...
    feature.type

    # Feature name
    feature.name

    # List of feature aliases
    feature.aliases

The real power is in the filter capabilities. Here are some examples::

    # Count number of Human "protein-conding" transcripts in ENSEMBL database
    res.feature.filter(
        species="Homo sapiens",
        type="transcript",
        subtype="protein-coding",
        source="ENSEMBL",
    ).count()

    # Convert all gene IDs in a list ``gene_ids`` to gene symbols::
    gene_ids = ["ENSG00000139618", "ENSG00000189283"]
    genes = res.feature.filter(
        feature_id__in=gene_ids,
        type="gene",
        species="Homo sapiens",
    )
    mapping = {g.feature_id: g.name for g in genes}
    gene_symbols = [mapping[gene_id] for gene_id in gene_ids]

.. warning::

  It might look tempting to simplify the last example with::

    gene_symbols = [g.name for g in genes]

  Don't do this. The order of entries in the ``genes`` can be arbitrary
  and therefore cause that the resulting list ``gene_symbols`` is not
  ordered in the same way as ``gene_ids``.


Mapping
=======
Mapping is a *connection* between two features. Features can be related
in various ways. The type of mapping is indicated by ``relation_type``
attribute. It is one of the following options:

    - ``crossdb``: Two features from different sources (databases)
      that describe same feature. Example: connection for gene BRCA2
      between database "UniProtKB" and "UCSC".
    - ``ortholog``: Two features from different species that
      describe orthologous gene.
    - ``transcript``: Connection between gene and it's transcripts.
    - ``exon``: Connection between gene / transcript and it's exons.

Again, we will only list an example and then let your imagination
fly::

    # Find UniProtKB ID for gene with given ENSEMBL ID:
    mapping = res.mapping.filter(
        source_id="ENSG00000189283",
        source_db="ENSEMBL",
        target_db="UniProtKB",
        source_species="Homo sapiens",
        target_species="Homo sapiens",
    )
    uniprot_id = mapping[0].target_id
