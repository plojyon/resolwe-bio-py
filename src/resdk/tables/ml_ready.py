""".. Ignore pydocstyle D400.

=============================
Machine learning ready tables
=============================

.. autoclass:: MLTables
    :members:

    .. automethod:: __init__

"""
import warnings
from io import BytesIO
from urllib.parse import urljoin

import pandas as pd


class MLTables:
    """Machine-learning ready tables."""

    DATA_FIELDS = [
        "id",
        "slug",
        "name",
        "modified",
        "output",
    ]

    def __init__(self, collection, name):
        """Initialize class.

        :param collection: Collection to use

        """
        self.resolwe = collection.resolwe
        self.collection = collection
        self.name = name

    def _get_ref_space(self):
        """Get reference space Data with specified name."""
        ref_spaces = self.resolwe.data.filter(
            type="data:ml:space",
            status="OK",
            fields=["id", "name"],
            collection__slug="reference-spaces",
            name=self.name,
        )
        if ref_spaces.count() == 0:
            raise ValueError(f"No Reference space with name {self.name}.")
        elif ref_spaces.count() > 1:
            raise ValueError(f"Multiple Reference spaces with name {self.name}.")
        return ref_spaces[0]

    def _get_datum(self):
        """Get ML ready expressions Data object."""
        ref_space = self._get_ref_space()
        # Get ID's of ref_space children
        children_ids = [
            item["id"]
            for item in self.resolwe.api.data(ref_space.id).children.get(fields="id")
        ]

        data = self.collection.data.filter(
            type="data:ml:table:expressions",
            id__in=children_ids,
            status="OK",
            fields=self.DATA_FIELDS,
        )
        if data.count() == 0:
            raise ValueError(f"No ML-ready data in collection {self.collection.name}.")
        elif data.count() > 1:
            warnings.warn(
                f"Multiple ML-ready data in collection {self.collection.name}. "
                "Using the latest one."
            )

        return data[0]

    @property
    def exp(self):
        """
        Get ML ready expressions as pandas.DataFrame.

        These expressions are normalized and batch effect corrected -
        thus ready to be taken into ML procedures.
        """
        datum = self._get_datum()

        url = urljoin(
            self.resolwe.url, f"data/{datum.id}/{datum.output['exp']['file']}"
        )
        response = self.resolwe.session.get(url)
        response.raise_for_status()
        with BytesIO() as f:
            f.write(response.content)
            f.seek(0)
            df = pd.read_csv(f, sep="\t", index_col=0)

        return df
