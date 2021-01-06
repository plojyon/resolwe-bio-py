.. _collection-tables:

=================
Collection Tables
=================

Imagine you are modelling gene expression data from a given collection.
Ideally, you would want all expression values organized in a table where
rows represents samples and columns represent genes. Class
``CollectionTables`` gives you just that (and more).

We will present the functionality of ``CollectionTables`` through an
example. We will:

- Create an instance of ``CollectionTables`` and examine it's attributes
- Fetch raw expressions and select `TIS signature genes`_ with
  sufficient coverage
- Normalize expression values (log-transform) and visualize samples in a
  simple PCA plot

.. _`TIS signature genes`: https://translational-medicine.biomedcentral.com/articles/10.1186/s12967-019-2100-3

First, connect to a Resolwe server, pick a collection and create
and instance of ``CollectionTables``::

    import resdk
    res = resdk.Resolwe(url='https://app.genialis.com/')
    res.login()
    collection = res.collection.get("sum149-fresh-for-rename")
    sum149 = resdk.CollectionTables(collection)

Object ``sum149`` is an instance of ``CollectionTables`` and has many attributes. For a complete list see
the :ref:`reference`, here we list the most commonly used ones::

    # Expressions raw counts
    sum149.rc

    # Expressions normalized counts
    sum149.exp
    # See normalization method
    sum149.exp.attrs["exp_type"]

    # Sample metadata
    sum149.meta

    # Dictionary that maps gene ID's into gene symbols
    sum149.id_to_symbol
    # This is handy to rename column names (gene ID's) to gene symbols
    sum149.rc.rename(columns=sum149.id_to_symbol)


.. note::

  Expressions and metadata are cached in memory as well as on disk. At
  each time they are re-requested a check is made that local and server side
  of data is synced. If so, cached data is used. Otherwise, new data
  will be pulled from server.

In our example we will only work with a set of `TIS signature genes`_::

    TIS_GENES = ["CD3D", "IDO1", "CIITA", "CD3E", "CCL5", "GZMK", "CD2", "HLA-DRA", "CXCL13", "IL2RG", "NKG7", "HLA-E", "CXCR6", "LAG3", "TAGAP", "CXCL10", "STAT1", "GZMB"]

We will identify low expressed genes and only keep the ones with average raw
expression above 20::

    tis_rc = sum149.rc.rename(columns=sum149.id_to_symbol)[TIS_GENES]
    mean = tis_rc.mean(axis=0)
    high_expressed_genes = mean.loc[mean > 20].index

Now, lets select TPM normalized expressions and keep only highly
expressed tis genes. We also transform to ``log2(TPM + 1)``::

    import numpy as np
    tis_tpm = sum149.exp.rename(columns=sum149.id_to_symbol)[high_expressed_genes]
    tis_tpm_log = np.log(tis_tpm + 1)

Finally, we perform PCA and visualize the results::

    from sklearn.decomposition import PCA
    pca = PCA(n_components=2, whiten=True)
    Y = pca.fit_transform(tis_tpm_log)

    import matplotlib.pyplot as plt
    for ((x, y), sample_name) in zip(Y, tis_tpm.index):
        plt.plot(x, y, 'bo')
        plt.text(x, y, sample_name)
    plt.xlabel(f"PC1 ({pca.explained_variance_ratio_[0]})")
    plt.ylabel(f"PC2 ({pca.explained_variance_ratio_[1]})")
    plt.show()