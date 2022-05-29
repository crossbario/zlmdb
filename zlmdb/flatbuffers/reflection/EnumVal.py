# automatically generated by the FlatBuffers compiler, do not modify

# namespace: reflection

import flatbuffers
from flatbuffers.compat import import_numpy
np = import_numpy()

class EnumVal(object):
    __slots__ = ['_tab']

    @classmethod
    def GetRootAs(cls, buf, offset=0):
        n = flatbuffers.encode.Get(flatbuffers.packer.uoffset, buf, offset)
        x = EnumVal()
        x.Init(buf, n + offset)
        return x

    @classmethod
    def GetRootAsEnumVal(cls, buf, offset=0):
        """This method is deprecated. Please switch to GetRootAs."""
        return cls.GetRootAs(buf, offset)
    @classmethod
    def EnumValBufferHasIdentifier(cls, buf, offset, size_prefixed=False):
        return flatbuffers.util.BufferHasIdentifier(buf, offset, b"\x42\x46\x42\x53", size_prefixed=size_prefixed)

    # EnumVal
    def Init(self, buf, pos):
        self._tab = flatbuffers.table.Table(buf, pos)

    # EnumVal
    def Name(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(4))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None

    # EnumVal
    def Value(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(6))
        if o != 0:
            return self._tab.Get(flatbuffers.number_types.Int64Flags, o + self._tab.Pos)
        return 0

    # EnumVal
    def UnionType(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(10))
        if o != 0:
            x = self._tab.Indirect(o + self._tab.Pos)
            from zlmdb.flatbuffers.reflection.Type import Type
            obj = Type()
            obj.Init(self._tab.Bytes, x)
            return obj
        return None

    # EnumVal
    def Documentation(self, j):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(12))
        if o != 0:
            a = self._tab.Vector(o)
            return self._tab.String(a + flatbuffers.number_types.UOffsetTFlags.py_type(j * 4))
        return ""

    # EnumVal
    def DocumentationLength(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(12))
        if o != 0:
            return self._tab.VectorLen(o)
        return 0

    # EnumVal
    def DocumentationIsNone(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(12))
        return o == 0

def EnumValStart(builder): builder.StartObject(5)
def Start(builder):
    return EnumValStart(builder)
def EnumValAddName(builder, name): builder.PrependUOffsetTRelativeSlot(0, flatbuffers.number_types.UOffsetTFlags.py_type(name), 0)
def AddName(builder, name):
    return EnumValAddName(builder, name)
def EnumValAddValue(builder, value): builder.PrependInt64Slot(1, value, 0)
def AddValue(builder, value):
    return EnumValAddValue(builder, value)
def EnumValAddUnionType(builder, unionType): builder.PrependUOffsetTRelativeSlot(3, flatbuffers.number_types.UOffsetTFlags.py_type(unionType), 0)
def AddUnionType(builder, unionType):
    return EnumValAddUnionType(builder, unionType)
def EnumValAddDocumentation(builder, documentation): builder.PrependUOffsetTRelativeSlot(4, flatbuffers.number_types.UOffsetTFlags.py_type(documentation), 0)
def AddDocumentation(builder, documentation):
    return EnumValAddDocumentation(builder, documentation)
def EnumValStartDocumentationVector(builder, numElems): return builder.StartVector(4, numElems, 4)
def StartDocumentationVector(builder, numElems):
    return EnumValStartDocumentationVector(builder, numElems)
def EnumValEnd(builder): return builder.EndObject()
def End(builder):
    return EnumValEnd(builder)
