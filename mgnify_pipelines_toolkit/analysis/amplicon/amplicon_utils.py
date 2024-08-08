#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2024 EMBL - European Bioinformatics Institute
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from collections import defaultdict, Counter
import logging
import gzip
import os
import subprocess

from mgnify_pipelines_toolkit.constants.regex_ambiguous_bases import (
    _AMBIGUOUS_BASES_DICT,
    _AMBIGUOUS_BASES_DICT_REV,
)

logging.basicConfig(level=logging.DEBUG)


def split_dir_into_sample_paths(dir):

    file_list = os.listdir(dir)
    file_list = [
        file
        for file in file_list
        if ".fastq" in file and ("_1" in file or "_2" in file)
    ]
    sample_set = set()
    [sample_set.add(f"{dir}/{file.split('_')[0]}") for file in file_list]
    sample_list = sorted(list(sample_set))

    return sample_list


def get_read_count(read_path, type="fastq"):

    cmd = []
    stdout = ""

    if type == "fastq":
        cmd = ["zcat", read_path]
        zcat_proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        cmd = ["wc", "-l"]
        wc_proc = subprocess.Popen(
            cmd, stdin=zcat_proc.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = wc_proc.communicate()

    elif type == "fasta":
        cmd = ["grep", "-c", "^>", read_path]
        grep_proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = grep_proc.communicate()

    read_count = stdout.strip() if stdout is not None else ""

    if not read_count.isdigit():
        logging.error(
            f"Read count is not a digit, something is wrong. stdout: '{stdout}', stderr: '{stderr}'"
        )
        exit(1)

    read_count = int(read_count)

    if type == "fastq":
        read_count /= 4

    return read_count


def build_cons_seq(
    cons_list,
    read_count,
    cons_threshold=0.80,
    do_not_include=None,
    counter=1,
    max_line_count=None,
):
    """
    Generate consensus sequence using a list of base conservation dictionaries most likely
    generated by the `build_mcp_cons_dict_list()` function.
    Also returns a list containing the conservation value of the most conserved base at every
    position in the list of base conservation dictionaries.
    """

    cons_seq = ""
    cons_confs = []

    if do_not_include is None:
        do_not_include = []

    for count_dict in cons_list:
        max_count = 0
        cons_dict = defaultdict(float)

        if counter in do_not_include:
            counter += 1
            cons_seq += "N"
            continue

        for base, count in count_dict.items():
            if base not in ("A", "T", "C", "G"):
                continue

            if max_line_count is None:
                cons_dict[base] = count / read_count
            else:
                cons_dict[base] = count / max_line_count

            if count > max_count:
                max_count = count

        counter += 1

        try:
            max_prop = max_count / read_count

            cons_bases = []
            curr_prop = 0.0
            sorted_cons_dict = dict(
                sorted(cons_dict.items(), key=lambda x: x[1], reverse=True)
            )

            for base, prop in sorted_cons_dict.items():
                cons_bases.append(base)
                curr_prop += prop
                if curr_prop >= cons_threshold:
                    break

            cons_bases = sorted(cons_bases)

            if len(cons_bases) == 1:
                cons_seq += cons_bases[0]
            else:
                amb_string = ",".join(cons_bases)
                amb_base = _AMBIGUOUS_BASES_DICT_REV[amb_string]
                cons_seq += amb_base

        except ZeroDivisionError:
            max_prop = 0.0

        cons_confs.append(max_prop)

    return cons_seq, cons_confs


def primer_regex_query_builder(primer):
    """
    Takes an input nucleotide sequence that can contain IUPAC ambiguous codes
    Returns a string formatted as a regex query that considers the different
    potential bases valid at a position with am abiguity code.
    """

    query = ""

    for char in primer:
        if char in ("A", "C", "T", "G"):
            query += char
        else:
            query += str(_AMBIGUOUS_BASES_DICT[char])

    query = f"(.*{query}){{e<=1}}"

    return query


def build_mcp_cons_dict_list(mcp_count_dict, mcp_len):
    """
    Generate list of dictionaries of base conservation for mcp output (mcp_cons_list)
    e.g. [{'A':0.9, 'C':0.1}, {'T':1.0}, ....] for every base position
    """

    mcp_cons_list = []

    for i in range(mcp_len):
        index_base_dict = defaultdict(int)
        for mcp in mcp_count_dict.keys():
            if len(mcp) < mcp_len:
                continue
            base = mcp[i]
            index_base_dict[base] += mcp_count_dict[mcp]
        mcp_cons_list.append(index_base_dict)

    return mcp_cons_list


def fetch_mcp(fastq, prefix_len, start=1, rev=False, max_line_count=None):
    """
    Generates the most common prefix sequences along with their counts in a fastq file.
    Outputs dictionary containing counts for each generated MCP in the fastq.
    """

    selected_lines = []

    with gzip.open(fastq, "rt") as file:
        for i, line in enumerate(file):
            line = line.strip()
            if i % 4 == 1:
                if not rev:
                    selected_lines.append(line[start - 1 : start + prefix_len - 1])
                else:
                    rev_line = line[::-1]
                    selected_lines.append(rev_line[start - 1 : start + prefix_len - 1])
            if max_line_count is not None:
                if len(selected_lines) > max_line_count:
                    break

    sequence_counts = Counter(selected_lines)
    mcp_count_dict = dict(
        sorted(sequence_counts.items(), key=lambda x: x[1], reverse=True)
    )

    return mcp_count_dict
