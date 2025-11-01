import random
import zlmdb


class Foo(object):

    oid: int
    value: float
    msg: str

    def __init__(self, oid=None, value=None, msg=None):
        self.oid = oid
        self.value = value
        self.msg = msg

    @staticmethod
    def unmarshal(obj):
        return Foo(obj['oid'], obj['value'], obj['msg'])

    def marshal(self):
        return {'oid': self.oid, 'value': self.value, 'msg': self.msg}


class MySchema(zlmdb.Schema):

    tab1: zlmdb.MapOidPickle = zlmdb.MapOidPickle(1)
    # tab1: zlmdb.MapOidJson = zlmdb.MapOidJson(1, marshal=Foo.marshal, unmarshal=Foo.unmarshal)
    # tab1: zlmdb.MapOidCbor = zlmdb.MapOidCbor(1, marshal=Foo.marshal, unmarshal=Foo.unmarshal)


schema = MySchema()

with schema.open('.testdb') as db:

    with db.begin(write=True) as txn:

        o1 = Foo(23, random.random(), 'Hello, world!')

        schema.tab1[txn, o1.oid] = o1
        print('object saved:', o1.oid, o1.value, o1.msg)

        o2 = schema.tab1[txn, o1.oid]
        assert o2
        print('object loaded:', o2.oid, o2.value, o2.msg)

    print('transaction committed')

print('database closed')
