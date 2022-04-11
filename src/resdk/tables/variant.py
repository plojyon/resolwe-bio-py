""".. Ignore pydocstyle D400.

=============
VariantTables
=============

.. autoclass:: VariantTables
    :members:

"""
import re
import warnings
from functools import lru_cache
from itertools import groupby
from typing import Callable, List, Optional

import numpy as np
import pandas as pd

from resdk.resources import Collection, Data

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

    data_type_to_field_name = {
        VARIANTS: "tsv",
        DEPTH: "tsv",
        DEPTH_A: "tsv",
        DEPTH_C: "tsv",
        DEPTH_G: "tsv",
        DEPTH_T: "tsv",
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
        discard_fakes: Optional[bool] = True,
        mutations: Optional[List[str]] = None,
        cache_dir: Optional[str] = None,
        progress_callable: Optional[Callable] = None,
    ):
        """Initialize class.

        :param collection: collection to use
        :param mutations: only consider these mutations
        :param discard_fakes: discard fake variants
        :param cache_dir: cache directory location, if not specified system specific
                          cache directory is used
        :param progress_callable: custom callable that can be used to report
                                  progress. By default, progress is written to
                                  stderr with tqdm
        """
        super().__init__(collection, cache_dir, progress_callable)

        self.discard_fakes = discard_fakes

        self.mutations = mutations
        if mutations is not None:
            if not isinstance(mutations, list):
                raise ValueError("Mutations must be a list of strings")
        else:
            # Check for heterogeneous mutations only if mutations is not specified
            self.check_heterogeneous_mutations()

    def check_heterogeneous_mutations(self):
        """Ensure variants are selected for the same mutations in all samples."""
        mutations = {str(d.input["mutations"]) for d in self._data}

        if len(mutations) > 1:
            raise ValueError(
                "Variants should be computed with the same mutation input. "
                f"Variants of samples in collection {self.collection.name} "
                f"have been computed with {', '.join(list(mutations))}.\n"
                "Use mutations filter in the VariantTables constructor.\n"
            )

    def parse_mutations_string(self, mutations):
        """Parse mutations string."""
        db = {}
        for mutation in mutations:
            if ":" not in mutation:
                # Only gene is given
                gene = mutation
                aa_changes = set()
            else:
                gene, aa_changes = mutation.split(":")
                aa_changes = set(map(str.strip, aa_changes.split(",")))

            db[gene] = aa_changes

        return db

    def is_mutation_subset(self, first, second):
        """Check if mutations given in first are a a subset of second."""
        db_first = self.parse_mutations_string(first)
        db_second = self.parse_mutations_string(second)

        for first_gene, first_aas in db_first.items():
            if first_gene not in db_second:
                return False
            if not db_second[first_gene]:
                # If the second covers the whole gene, all is good
                continue
            second_aas = db_second[first_gene]
            if not first_aas and second_aas:
                # First covers the whole gene, second does not
                return False
            if not first_aas.issubset(second_aas):
                return False

        return True

    @property
    @lru_cache()
    def _data(self) -> List[Data]:
        """Fetch data objects.

        Fetch Data of type ``self.process_type`` from given collection
        and cache the results in memory. Only the needed subset of
        fields is fetched.

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
            # 1 Filter by mutations, if required
            if self.mutations:
                if not self.is_mutation_subset(
                    self.mutations, datum.input["mutations"]
                ):
                    continue

            # 2 Filter by newest datum in the sample
            if datum.sample.id in sample_ids:
                repeated_sample_ids.add(datum.sample.id)
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

    @property
    @lru_cache()
    def variants(self) -> pd.DataFrame:
        """Return variants table as a pandas DataFrame object."""
        return self._load_fetch(self.VARIANTS)

    @property
    @lru_cache()
    def depth(self) -> pd.DataFrame:
        """Return depth table as a pandas DataFrame object."""
        return self._load_fetch(self.DEPTH)

    @property
    @lru_cache()
    def depth_a(self) -> pd.DataFrame:
        """Return depth table for adenine as a pandas DataFrame object."""
        return self._load_fetch(self.DEPTH_A)

    @property
    @lru_cache()
    def depth_c(self) -> pd.DataFrame:
        """Return depth table for cytosine as a pandas DataFrame object."""
        return self._load_fetch(self.DEPTH_C)

    @property
    @lru_cache()
    def depth_g(self) -> pd.DataFrame:
        """Return depth table for guanine as a pandas DataFrame object."""
        return self._load_fetch(self.DEPTH_G)

    @property
    @lru_cache()
    def depth_t(self) -> pd.DataFrame:
        """Return depth table for thymine as a pandas DataFrame object."""
        return self._load_fetch(self.DEPTH_T)

    def _download_qc(self) -> pd.DataFrame:
        """Download sample QC data and transform into table."""
        # No QC is given for variants data - return empty DataFrame
        return pd.DataFrame()

    def strip_amino_acid(self, amino_acid_string, remove_alt=False):
        """Remove "p." prefix of the amino acid string."""
        # Example Amino acid change:  "p.Gly12Asp"
        if pd.isna(amino_acid_string):
            return ""
        aa_match = re.match(
            r"^p?\.?([A-Z][a-z]{2}\d+[A-Z][a-z]{2})$", amino_acid_string
        )
        if aa_match:
            if remove_alt:
                return aa_match.group(1)[:-3]
            return aa_match.group(1)
        return ""

    def construct_index(self, row) -> str:
        """
        Construct index of the variants table.

        Index should have the form:
        <chr>_<position>_<snp_change>_<aminoacid_pos_change>
        E.g. chr2_1234567_C>T_Gly12Asp

        In cases where nucleotide change or amino-acid change is
        missing, this info is left out from the index.

        """
        chrom = row["CHROM"]
        pos = row["POS"]

        index = f"{chrom}_{pos}"

        # REF & ALT
        ref = row["REF"]
        alt = row.get("ALT", "?")
        if alt in ["A", "C", "G", "T"]:
            index += f"_{ref}>{alt}"

        # Amino acid change
        aa_change = row.get("HGVS.p", "?")
        aa_change = self.strip_amino_acid(aa_change)
        if aa_change:
            index = f"{index}_{aa_change}"

        return index

    @staticmethod
    def encode_mutation(row) -> int:
        """Encode mutation to numerical value.

        Mutations are given as <allele1>/<allele2>, e.g. T/T or C/T

        Encode these mutations as:
            - 0 for wild type (no mutation)
            - 1 for heterozygous mutation
            - 2 for homozygous mutation
        """
        allele_line = row.get("SAMPLENAME1.GT", np.nan)
        hgvs_line = row.get("HGVS.p", np.nan)

        # Handle the obvious cases first:
        if row["REF"] == row["ALT"]:
            return 0
        elif row["ALT"] is None or row["ALT"] == "" or pd.isna(row["ALT"]):
            return 0
        elif allele_line is None or allele_line == "" or pd.isna(allele_line):
            return 0
        elif (
            hgvs_line is None
            or hgvs_line.startswith("no mutation at")
            or pd.isna(hgvs_line)
        ):
            return 0

        try:
            allele1, allele2 = re.match(r"([ACGT])/([ACGT])", allele_line).group(1, 2)
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
        sample_data = pd.read_csv(file_obj, sep="\t")

        # Filter mutations if specified
        if self.mutations:
            keep = set()
            for gene, aa_change in self.parse_mutations_string(self.mutations).items():
                for sample, gene2, aa_change2 in zip(
                    sample_data.index, sample_data["Gene_Name"], sample_data["HGVS.p"]
                ):
                    if not aa_change:
                        if gene == gene2:
                            keep.add(sample)
                    else:
                        if gene == gene2 and aa_change == {
                            self.strip_amino_acid(aa_change2, remove_alt=True)
                        }:
                            keep.add(sample)

            sample_data = sample_data.loc[keep]

        # Construct index
        sample_data["index"] = sample_data.apply(
            self.construct_index, axis=1, result_type="reduce"
        )
        sample_data.set_index("index", inplace=True)
        sample_data.index.name = None

        if data_type == self.VARIANTS:
            s = sample_data.apply(self.encode_mutation, axis=1, result_type="reduce")
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

        s.name = sample_id
        return s

    def postprocess_variants_table(self, df, data_type):
        """
        Propagate info from "fake" to the "real" variants.

        "fake variants" are referred as positions for which we know that
        do not contain variants. The absence of variants is still a valuable
        information and should be propagated further when mergeing info
        from multiple samples in matrix form.
        """

        def chrom_pos(column_name):
            """Return only chromosome and position from index."""
            chrom, pos = column_name.split("_")[:2]
            return f"{chrom}_{pos}"

        to_discard = list()

        for _, group in groupby(df.columns, key=chrom_pos):
            # Sorting moves fake variant to the first position
            group = sorted(group)
            if len(group) <= 1:
                continue

            fake_variant = group[0]
            true_variants = group[1:]
            to_discard.append(fake_variant)

            # Propagate info from fake variants to the true ones
            for dst in true_variants:
                for sample, fake, true in zip(df.index, df[fake_variant], df[dst]):
                    if data_type == self.VARIANTS:
                        if fake == 0.0 and pd.isna(true):
                            # Copy 0.0 from all fake to the true ones
                            df.loc[sample, dst] = fake
                    else:
                        if not pd.isna(fake) and pd.isna(true):
                            # Copy depth from all false to the true ones
                            df.loc[sample, dst] = fake

        if self.discard_fakes:
            df = df.drop(columns=to_discard)

        return df

    async def _download_data(self, data_type: str) -> pd.DataFrame:
        df = await super()._download_data(data_type)
        return self.postprocess_variants_table(df, data_type=data_type)
