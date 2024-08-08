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

# used by fetch_mcp in analysis.amplicon
MCP_MAX_LINE_COUNT = 300_000

# used by classify_var_regions in analysis.amplicon
MIN_OVERLAP = 0.95
MIN_SEQ_COUNT = 5000
MAX_ERROR_PROPORTION = 0.01
MAX_INTERNAL_PRIMER_PROPORTION = 0.2
