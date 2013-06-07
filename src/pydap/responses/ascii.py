try:                                                                            
    from functools import singledispatch                                        
except ImportError:                                                             
    from singledispatch import singledispatch
import itertools

import numpy as np

from pydap.model import *
from pydap.lib import walk, encode
from pydap.responses.lib import BaseResponse
from pydap.responses.dds import dds


class ASCIIResponse(BaseResponse):
    def __init__(self, dataset):
        BaseResponse.__init__(self, dataset)
        self.headers.extend([
            ('Content-description', 'dods_ascii'),
            ('Content-type', 'text/plain; charset=utf-8'),
        ])

    def __iter__(self):
        for line in dds(self.dataset):
            yield line
        yield 45 * '-'
        yield '\n'

        for line in ascii(self.dataset):
            yield line

        if hasattr(self.dataset, 'close'):
            self.dataset.close()


@singledispatch
def ascii(var, printname=True):
    raise StopIteration


@ascii.register(SequenceType)
def _(var, printname=True):
    yield ', '.join(child.id for child in var.children())
    yield '\n'
    for rec in var:
        out = var.clone()
        out.__class__ = StructureType
        out.data = rec
        for i, line in enumerate(ascii(out, printname=False)):
            line = line.strip()
            if line and i > 0:
                yield ', '
            yield line
        yield '\n'


@ascii.register(StructureType)
def _(var, printname=True):
    for child in var.children():
        for line in ascii(child, printname):
            yield line
        yield '\n'


@ascii.register(BaseType)
def _(var, printname=True):
    if printname:
        yield var.id
        yield '\n'

    if not var.shape:
        yield encode(var.data)
    else:
        for indexes, value in itertools.izip(np.ndindex(var.shape), var.data):
            yield "{indexes} {value}\n".format(
                indexes="[" + "][".join(str(idx) for idx in indexes) + "]",
                value=encode(value))