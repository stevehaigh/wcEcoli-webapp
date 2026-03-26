"""Constants from wcEcoli's tablewriter module needed by TableReader.

Vendored from wholecell/io/tablewriter.py in CovertLab/wcEcoli.
Do not add logic here — this file is constants only.
"""

import struct
import numpy as np

VERSION = 3

FILE_ATTRIBUTES = "attributes.json"

CHUNK_HEADER = struct.Struct('>4s I')
COLUMN_CHUNK_TYPE = b'COLM'
VARIABLE_COLUMN_CHUNK_TYPE = b'VCOL'
BLOCK_CHUNK_TYPE = b'BLOC'
ROW_SIZE_CHUNK_TYPE = b'RWSZ'

ROW_SIZE_CHUNK_DTYPE = np.uint32
VARIABLE_COLUMN_DATA_DTYPE = np.float64

COLUMN_STRUCT = struct.Struct('>2I 2H')
VARIABLE_COLUMN_STRUCT = struct.Struct('H')

COMPRESSION_TYPE_NONE = 0
COMPRESSION_TYPE_ZLIB = 1
