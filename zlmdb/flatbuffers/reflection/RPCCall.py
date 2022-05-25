# automatically generated by the FlatBuffers compiler, do not modify

# namespace: reflection

import flatbuffers
from flatbuffers.compat import import_numpy
np = import_numpy()

class RPCCall(object):
    __slots__ = ['_tab']

    @classmethod
    def GetRootAs(cls, buf, offset=0):
        n = flatbuffers.encode.Get(flatbuffers.packer.uoffset, buf, offset)
        x = RPCCall()
        x.Init(buf, n + offset)
        return x

    @classmethod
    def GetRootAsRPCCall(cls, buf, offset=0):
        """This method is deprecated. Please switch to GetRootAs."""
        return cls.GetRootAs(buf, offset)
    @classmethod
    def RPCCallBufferHasIdentifier(cls, buf, offset, size_prefixed=False):
        return flatbuffers.util.BufferHasIdentifier(buf, offset, b"\x42\x46\x42\x53", size_prefixed=size_prefixed)

    # RPCCall
    def Init(self, buf, pos):
        self._tab = flatbuffers.table.Table(buf, pos)

    # RPCCall
    def Name(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(4))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None

    # RPCCall
    def Request(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(6))
        if o != 0:
            x = self._tab.Indirect(o + self._tab.Pos)
            from zlmdb.flatbuffers.reflection.Object import Object
            obj = Object()
            obj.Init(self._tab.Bytes, x)
            return obj
        return None

    # RPCCall
    def Response(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(8))
        if o != 0:
            x = self._tab.Indirect(o + self._tab.Pos)
            from zlmdb.flatbuffers.reflection.Object import Object
            obj = Object()
            obj.Init(self._tab.Bytes, x)
            return obj
        return None

    # RPCCall
    def Attributes(self, j):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(10))
        if o != 0:
            x = self._tab.Vector(o)
            x += flatbuffers.number_types.UOffsetTFlags.py_type(j) * 4
            x = self._tab.Indirect(x)
            from zlmdb.flatbuffers.reflection.KeyValue import KeyValue
            obj = KeyValue()
            obj.Init(self._tab.Bytes, x)
            return obj
        return None

    # RPCCall
    def AttributesLength(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(10))
        if o != 0:
            return self._tab.VectorLen(o)
        return 0

    # RPCCall
    def AttributesIsNone(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(10))
        return o == 0

    # RPCCall
    def Documentation(self, j):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(12))
        if o != 0:
            a = self._tab.Vector(o)
            return self._tab.String(a + flatbuffers.number_types.UOffsetTFlags.py_type(j * 4))
        return ""

    # RPCCall
    def DocumentationLength(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(12))
        if o != 0:
            return self._tab.VectorLen(o)
        return 0

    # RPCCall
    def DocumentationIsNone(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(12))
        return o == 0

def Start(builder): builder.StartObject(5)
def RPCCallStart(builder):
    """This method is deprecated. Please switch to Start."""
    return Start(builder)
def AddName(builder, name): builder.PrependUOffsetTRelativeSlot(0, flatbuffers.number_types.UOffsetTFlags.py_type(name), 0)
def RPCCallAddName(builder, name):
    """This method is deprecated. Please switch to AddName."""
    return AddName(builder, name)
def AddRequest(builder, request): builder.PrependUOffsetTRelativeSlot(1, flatbuffers.number_types.UOffsetTFlags.py_type(request), 0)
def RPCCallAddRequest(builder, request):
    """This method is deprecated. Please switch to AddRequest."""
    return AddRequest(builder, request)
def AddResponse(builder, response): builder.PrependUOffsetTRelativeSlot(2, flatbuffers.number_types.UOffsetTFlags.py_type(response), 0)
def RPCCallAddResponse(builder, response):
    """This method is deprecated. Please switch to AddResponse."""
    return AddResponse(builder, response)
def AddAttributes(builder, attributes): builder.PrependUOffsetTRelativeSlot(3, flatbuffers.number_types.UOffsetTFlags.py_type(attributes), 0)
def RPCCallAddAttributes(builder, attributes):
    """This method is deprecated. Please switch to AddAttributes."""
    return AddAttributes(builder, attributes)
def StartAttributesVector(builder, numElems): return builder.StartVector(4, numElems, 4)
def RPCCallStartAttributesVector(builder, numElems):
    """This method is deprecated. Please switch to Start."""
    return StartAttributesVector(builder, numElems)
def AddDocumentation(builder, documentation): builder.PrependUOffsetTRelativeSlot(4, flatbuffers.number_types.UOffsetTFlags.py_type(documentation), 0)
def RPCCallAddDocumentation(builder, documentation):
    """This method is deprecated. Please switch to AddDocumentation."""
    return AddDocumentation(builder, documentation)
def StartDocumentationVector(builder, numElems): return builder.StartVector(4, numElems, 4)
def RPCCallStartDocumentationVector(builder, numElems):
    """This method is deprecated. Please switch to Start."""
    return StartDocumentationVector(builder, numElems)
def End(builder): return builder.EndObject()
def RPCCallEnd(builder):
    """This method is deprecated. Please switch to End."""
    return End(builder)