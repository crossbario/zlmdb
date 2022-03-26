# automatically generated by the FlatBuffers compiler, do not modify

# namespace: reflection

import flatbuffers
from flatbuffers.compat import import_numpy
np = import_numpy()

class Schema(object):
    __slots__ = ['_tab']

    @classmethod
    def GetRootAs(cls, buf, offset=0):
        n = flatbuffers.encode.Get(flatbuffers.packer.uoffset, buf, offset)
        x = Schema()
        x.Init(buf, n + offset)
        return x

    @classmethod
    def GetRootAsSchema(cls, buf, offset=0):
        """This method is deprecated. Please switch to GetRootAs."""
        return cls.GetRootAs(buf, offset)
    @classmethod
    def SchemaBufferHasIdentifier(cls, buf, offset, size_prefixed=False):
        return flatbuffers.util.BufferHasIdentifier(buf, offset, b"\x42\x46\x42\x53", size_prefixed=size_prefixed)

    # Schema
    def Init(self, buf, pos):
        self._tab = flatbuffers.table.Table(buf, pos)

    # Schema
    def Objects(self, j):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(4))
        if o != 0:
            x = self._tab.Vector(o)
            x += flatbuffers.number_types.UOffsetTFlags.py_type(j) * 4
            x = self._tab.Indirect(x)
            from reflection.Object import Object
            obj = Object()
            obj.Init(self._tab.Bytes, x)
            return obj
        return None

    # Schema
    def ObjectsLength(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(4))
        if o != 0:
            return self._tab.VectorLen(o)
        return 0

    # Schema
    def ObjectsIsNone(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(4))
        return o == 0

    # Schema
    def Enums(self, j):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(6))
        if o != 0:
            x = self._tab.Vector(o)
            x += flatbuffers.number_types.UOffsetTFlags.py_type(j) * 4
            x = self._tab.Indirect(x)
            from reflection.Enum import Enum
            obj = Enum()
            obj.Init(self._tab.Bytes, x)
            return obj
        return None

    # Schema
    def EnumsLength(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(6))
        if o != 0:
            return self._tab.VectorLen(o)
        return 0

    # Schema
    def EnumsIsNone(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(6))
        return o == 0

    # Schema
    def FileIdent(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(8))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None

    # Schema
    def FileExt(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(10))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None

    # Schema
    def RootTable(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(12))
        if o != 0:
            x = self._tab.Indirect(o + self._tab.Pos)
            from reflection.Object import Object
            obj = Object()
            obj.Init(self._tab.Bytes, x)
            return obj
        return None

    # Schema
    def Services(self, j):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(14))
        if o != 0:
            x = self._tab.Vector(o)
            x += flatbuffers.number_types.UOffsetTFlags.py_type(j) * 4
            x = self._tab.Indirect(x)
            from reflection.Service import Service
            obj = Service()
            obj.Init(self._tab.Bytes, x)
            return obj
        return None

    # Schema
    def ServicesLength(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(14))
        if o != 0:
            return self._tab.VectorLen(o)
        return 0

    # Schema
    def ServicesIsNone(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(14))
        return o == 0

    # Schema
    def AdvancedFeatures(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(16))
        if o != 0:
            return self._tab.Get(flatbuffers.number_types.Uint64Flags, o + self._tab.Pos)
        return 0

    # All the files used in this compilation. Files are relative to where
    # flatc was invoked.
    # Schema
    def FbsFiles(self, j):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(18))
        if o != 0:
            x = self._tab.Vector(o)
            x += flatbuffers.number_types.UOffsetTFlags.py_type(j) * 4
            x = self._tab.Indirect(x)
            from reflection.SchemaFile import SchemaFile
            obj = SchemaFile()
            obj.Init(self._tab.Bytes, x)
            return obj
        return None

    # Schema
    def FbsFilesLength(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(18))
        if o != 0:
            return self._tab.VectorLen(o)
        return 0

    # Schema
    def FbsFilesIsNone(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(18))
        return o == 0

def Start(builder): builder.StartObject(8)
def SchemaStart(builder):
    """This method is deprecated. Please switch to Start."""
    return Start(builder)
def AddObjects(builder, objects): builder.PrependUOffsetTRelativeSlot(0, flatbuffers.number_types.UOffsetTFlags.py_type(objects), 0)
def SchemaAddObjects(builder, objects):
    """This method is deprecated. Please switch to AddObjects."""
    return AddObjects(builder, objects)
def StartObjectsVector(builder, numElems): return builder.StartVector(4, numElems, 4)
def SchemaStartObjectsVector(builder, numElems):
    """This method is deprecated. Please switch to Start."""
    return StartObjectsVector(builder, numElems)
def AddEnums(builder, enums): builder.PrependUOffsetTRelativeSlot(1, flatbuffers.number_types.UOffsetTFlags.py_type(enums), 0)
def SchemaAddEnums(builder, enums):
    """This method is deprecated. Please switch to AddEnums."""
    return AddEnums(builder, enums)
def StartEnumsVector(builder, numElems): return builder.StartVector(4, numElems, 4)
def SchemaStartEnumsVector(builder, numElems):
    """This method is deprecated. Please switch to Start."""
    return StartEnumsVector(builder, numElems)
def AddFileIdent(builder, fileIdent): builder.PrependUOffsetTRelativeSlot(2, flatbuffers.number_types.UOffsetTFlags.py_type(fileIdent), 0)
def SchemaAddFileIdent(builder, fileIdent):
    """This method is deprecated. Please switch to AddFileIdent."""
    return AddFileIdent(builder, fileIdent)
def AddFileExt(builder, fileExt): builder.PrependUOffsetTRelativeSlot(3, flatbuffers.number_types.UOffsetTFlags.py_type(fileExt), 0)
def SchemaAddFileExt(builder, fileExt):
    """This method is deprecated. Please switch to AddFileExt."""
    return AddFileExt(builder, fileExt)
def AddRootTable(builder, rootTable): builder.PrependUOffsetTRelativeSlot(4, flatbuffers.number_types.UOffsetTFlags.py_type(rootTable), 0)
def SchemaAddRootTable(builder, rootTable):
    """This method is deprecated. Please switch to AddRootTable."""
    return AddRootTable(builder, rootTable)
def AddServices(builder, services): builder.PrependUOffsetTRelativeSlot(5, flatbuffers.number_types.UOffsetTFlags.py_type(services), 0)
def SchemaAddServices(builder, services):
    """This method is deprecated. Please switch to AddServices."""
    return AddServices(builder, services)
def StartServicesVector(builder, numElems): return builder.StartVector(4, numElems, 4)
def SchemaStartServicesVector(builder, numElems):
    """This method is deprecated. Please switch to Start."""
    return StartServicesVector(builder, numElems)
def AddAdvancedFeatures(builder, advancedFeatures): builder.PrependUint64Slot(6, advancedFeatures, 0)
def SchemaAddAdvancedFeatures(builder, advancedFeatures):
    """This method is deprecated. Please switch to AddAdvancedFeatures."""
    return AddAdvancedFeatures(builder, advancedFeatures)
def AddFbsFiles(builder, fbsFiles): builder.PrependUOffsetTRelativeSlot(7, flatbuffers.number_types.UOffsetTFlags.py_type(fbsFiles), 0)
def SchemaAddFbsFiles(builder, fbsFiles):
    """This method is deprecated. Please switch to AddFbsFiles."""
    return AddFbsFiles(builder, fbsFiles)
def StartFbsFilesVector(builder, numElems): return builder.StartVector(4, numElems, 4)
def SchemaStartFbsFilesVector(builder, numElems):
    """This method is deprecated. Please switch to Start."""
    return StartFbsFilesVector(builder, numElems)
def End(builder): return builder.EndObject()
def SchemaEnd(builder):
    """This method is deprecated. Please switch to End."""
    return End(builder)