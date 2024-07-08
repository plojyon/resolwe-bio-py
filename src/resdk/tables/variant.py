""".. Ignore pydocstyle D400.

=============
VariantTables
=============

.. autoclass:: VariantTables
    :members:
    :inherited-members:

"""

import re
import warnings
from functools import lru_cache
from typing import Callable, List, Optional, Union

import numpy as np
import pandas as pd

from resdk.resources import Collection, Data, Geneset

from .base import BaseTables


class VariantTables(BaseTables):
    """A helper class to fetch collection's variant and meta data.

    This class enables fetching given collection's data and returning it
    as tables which have samples in rows and variants in columns.

    A simple example:

    .. code-block:: python

        # Get Collection object
        collection = res.collection.get("collection-slug")

        tables = VariantTables(collection)
        # Get variant data
        tables.variants
        # Get depth per variant or coverage for specific base
        tables.depth
        tables.depth_a
        tables.depth_c
        tables.depth_g
        tables.depth_t

    """

    process_type = "data:mutationstable"
    VARIANTS = "variants"
    DEPTH = "depth"
    DEPTH_A = "depth_a"
    DEPTH_C = "depth_c"
    DEPTH_G = "depth_g"
    DEPTH_T = "depth_t"
    FILTER = "FILTER"

    data_type_to_field_name = {
        VARIANTS: "tsv",
        DEPTH: "tsv",
        DEPTH_A: "tsv",
        DEPTH_C: "tsv",
        DEPTH_G: "tsv",
        DEPTH_T: "tsv",
        FILTER: "tsv",
    }

    DATA_FIELDS = [
        "id",
        "slug",
        "modified",
        "entity__name",
        "entity__id",
        "input",
        "output",
        "process__output_schema",
        "process__slug",
    ]

    def __init__(
        self,
        collection: Collection,
        geneset: Optional[List[str]] = None,
        filtering: bool = True,
        cache_dir: Optional[str] = None,
        progress_callable: Optional[Callable] = None,
    ):
        """Initialize class.

        :param collection: Collection to use.
        :param geneset: Only consider mutations from this gene-set.
            Can be a list of gene symbols or a valid geneset Data
            object id / slug.
        :param filtering: Only show variants that pass QC filters.
        :param cache_dir: Cache directory location, if not specified
            system specific cache directory is used.
        :param progress_callable: Custom callable that can be used to
            report progress. By default, progress is written to stderr
            with tqdm.
        """
        super().__init__(collection, cache_dir, progress_callable)
        self.filtering = filtering

        self._geneset = None
        if geneset is None:
            self._check_heterogeneous_mutations()
            # Assign geneset from the Genialis Platform
            self.geneset = self._get_obj_geneset(self._data[0])
        else:
            self.geneset = geneset

    @property
    def geneset(self):
        """Get geneset."""
        return self._geneset

    @geneset.setter
    def geneset(self, value: Union[str, int, Geneset, List[str]]):
        """Set geneset.

        Geneset can be set only once. On attempt to re-set, ValueError is raised.
        """
        # Geneset can be set only once, prevent modifications
        if self._geneset is not None:
            raise ValueError("It is not allowed to change geneset value.")

        if value is None:
            return

        # If id / slug of a geneset is given, get it from the Resolwe server
        if isinstance(value, (int, str)):
            gs = self.resolwe.geneset.get(value)
            value = gs.genes
        elif isinstance(value, Geneset):
            value = value.genes

        if isinstance(value, (list, set, tuple, pd.Series)):
            self._geneset = set(value)
        else:
            raise ValueError(f'Unsupported type of "geneset" input: {value}.')

    @property
    @lru_cache()
    def variants(self) -> pd.DataFrame:
        """Get variants table.

        There are 4 possible values:

            - 0 - wild-type, no variant
            - 1 - heterozygous mutation
            - 2 - homozygous mutation
            - NaN - QC filters are failing - mutation status is unreliable

        """
        df = self._load_fetch(self.VARIANTS)

        # Variants that are not reported (NaN) were not detected:
        # they are wild type.
        df = df.fillna(0)

        if self.filtering:
            # Keep values in case .filter == PASS or .variants == 0
            df = df.where((self.filter == "PASS") | (df == 0), other=np.nan)

        return df

    @property
    @lru_cache()
    def depth(self) -> pd.DataFrame:
        """Get depth table."""
        return self._load_fetch(self.DEPTH)

    @property
    @lru_cache()
    def depth_a(self) -> pd.DataFrame:
        """Get depth table for adenine."""
        return self._load_fetch(self.DEPTH_A)

    @property
    @lru_cache()
    def depth_c(self) -> pd.DataFrame:
        """Get depth table for cytosine."""
        return self._load_fetch(self.DEPTH_C)

    @property
    @lru_cache()
    def depth_g(self) -> pd.DataFrame:
        """Get depth table for guanine."""
        return self._load_fetch(self.DEPTH_G)

    @property
    @lru_cache()
    def depth_t(self) -> pd.DataFrame:
        """Get depth table for thymine."""
        return self._load_fetch(self.DEPTH_T)

    # TODO: consider better name
    @property
    @lru_cache()
    def filter(self) -> pd.DataFrame:
        """Get filter table.

        Values can be:

            - PASS - Variant has passed filters:
            - DP : Insufficient read depth (< 10.0)
            - QD: insufficient quality normalized by depth (< 2.0)
            - FS: insufficient phred-scaled p-value using Fisher's exact
                test to detect strand bias (> 30.0)
            - SnpCluster: Variant is part of a cluster

        For example, if a variant has read depth 8, GATK will mark it as DP.

        """
        return self._load_fetch(self.FILTER)

    def _check_heterogeneous_mutations(self):
        """Check there are not heterogeneous mutations / genesets.

        Genes for which mutations are computed are given either with mutations
        (list of genes) or geneset (geneset ID) input. Ensure all the data has
        the same value of this.
        """
        # Currently, frontend assigns empty list if this value is not entered.
        mutations = {str(d.input.get("mutations", [])) for d in self._data}
        genesets = {str(d.input.get("geneset", "")) for d in self._data}

        if len(mutations) > 1:
            name = "mutations"
            multiple = mutations
        elif len(genesets) > 1:
            name = "genesets"
            multiple = genesets
        else:
            return

        raise ValueError(
            f"Variants should be computed with the same {name} input. "
            f"Variants of samples in collection {self.collection.name} "
            f"have been computed with {', '.join(list(multiple))}.\n"
            "Use geneset filter in the VariantTables constructor.\n"
        )

    def _get_obj_geneset(self, obj):
        """Get genes for which mutations are computed in an object."""
        obj_geneset = set(obj.input.get("mutations", []))
        if not obj_geneset:
            # Geneset is given via geneset input:
            gs = self.resolwe.geneset.get(obj.input["geneset"])
            obj_geneset = set(gs.genes)

            # Convert to gene symbols in case genes are given as feature ID's
            if gs.output["source"] != "UCSC":
                qs = self.resolwe.feature.filter(feature_id__in=list(obj_geneset))
                id_2_name = {obj.feature_id: obj.name for obj in qs}
                # Sometimes, genes defined in obj.input[geneset/mutations] are
                # missing in KnowledgeBase. This can happen due to KB updates.
                mapping_yes, mapping_no = set(), set()
                for gene_id in obj_geneset:
                    if gene_id in id_2_name:
                        mapping_yes.add(id_2_name[gene_id])
                    else:
                        mapping_no.add(gene_id)
                if mapping_no:
                    warnings.warn(
                        f"{len(mapping_no)} genes in sample {obj.sample.id} are "
                        "missing from KnowledgeBase. These genes are ignored in "
                        "further analysis."
                    )
                obj_geneset = mapping_yes

        return obj_geneset

    @property
    @lru_cache()
    def _data(self) -> List[Data]:
        """Fetch data objects.

        Fetch Data of type ``self.process_type`` from given collection
        and cache the results in memory.

        :return: list of Data objects
        """
        data = []
        sample_ids, repeated_sample_ids = set(), set()
        for datum in self.collection.data.filter(
            type=self.process_type,
            status="OK",
            ordering="-created",
            fields=self.DATA_FIELDS,
        ):
            # 1 Filter by newest datum in the sample
            if datum.sample.id in sample_ids:
                repeated_sample_ids.add(datum.sample.id)
                continue

            # 2 Filter by genes, if geneset is given
            if self.geneset:
                obj_geneset = self._get_obj_geneset(datum)
                if not self.geneset.issubset(obj_geneset):
                    warnings.warn(
                        f"Sample {datum.sample} (Data {datum.id}) does not "
                        "contain the genes requested in geneset input."
                    )
                    continue

            sample_ids.add(datum.sample.id)
            data.append(datum)

        if repeated_sample_ids:
            repeated = ", ".join(map(str, repeated_sample_ids))
            warnings.warn(
                f"The following samples have multiple data of type {self.process_type}: "
                f"{repeated}. Using only the newest data of this sample.",
                UserWarning,
            )

        if not data:
            raise ValueError(
                f"Collection {self.collection.name} has no {self.process_type} "
                "data or there is no data with the requested mutations."
            )

        return data

    def _download_qc(self) -> pd.DataFrame:
        """Download sample QC data and transform into table."""
        # No QC is given for variants data - return empty DataFrame
        return pd.DataFrame()

    def _construct_index(self, row) -> str:
        """
        Construct index of the variants table.

        Index should have the form:
        <chr>_<position>_<snp_change>
        E.g. chr2_1234567_C>T

        """
        chrom = row["CHROM"]
        pos = row["POS"]
        ref = row["REF"]
        alt = row["ALT"]

        return f"{chrom}_{pos}_{ref}>{alt}"

    @staticmethod
    def _encode_mutation(row) -> int:
        """Encode mutation to numerical value.

        Mutations are given as <allele1>/<allele2>, e.g. T/T or C/T

        Encode these mutations as:
            - 0 for wild type (no mutation)
            - 1 for heterozygous mutation
            - 2 for homozygous mutation
        """
        try:
            allele_line = row.get("SAMPLENAME1.GT", np.nan)
            allele_re = r"^([ATGC*]+)/([ATGC*]+)$"
            allele1, allele2 = re.match(allele_re, allele_line).group(1, 2)
        except AttributeError:
            # AttributeError is raised when there is no match, e.g.
            # there is a string value for column "SAMPLENAME1.GT" but
            # the above regex can't parse it
            warnings.warn(f'Cannot encode mutation from value "{allele_line}".')
            return np.nan

        if allele1 == allele2 == row["REF"]:
            return 0
        elif allele1 == allele2 == row["ALT"]:
            return 2
        else:
            return 1

    def _parse_file(self, file_obj, sample_id, data_type) -> pd.Series:
        """Parse file - get encoded variants / depth of a single sample."""
        sample_data = pd.read_csv(file_obj, sep="\t", low_memory=False)

        # Filter mutations if specified
        if self.geneset:
            out = sample_data.loc[sample_data["Gene_Name"].isin(self.geneset)]
            if out.empty:
                out = sample_data.loc[sample_data["Feature_ID"].isin(self.geneset)]

            sample_data = out

        # Construct index
        sample_data["index"] = sample_data.apply(
            self._construct_index, axis=1, result_type="reduce"
        )
        sample_data.set_index("index", inplace=True)
        sample_data.index.name = None

        if data_type == self.VARIANTS:
            s = sample_data.apply(self._encode_mutation, axis=1, result_type="reduce")
        elif data_type == self.DEPTH:
            # Depth, as computed by GATK is reported by "DP" column
            s = sample_data["Total_depth"]
        elif data_type == self.DEPTH_A:
            s = sample_data["Base_A"]
        elif data_type == self.DEPTH_C:
            s = sample_data["Base_C"]
        elif data_type == self.DEPTH_G:
            s = sample_data["Base_G"]
        elif data_type == self.DEPTH_T:
            s = sample_data["Base_T"]
        elif data_type == self.FILTER:
            s = sample_data["FILTER"]

        s.name = sample_id

        # Sometimes mutations_table.tsv to contains duplicate variants
        # For now, keep the first one and drop the rest of them.
        s = s[~s.index.duplicated(keep="first")]

        return s
