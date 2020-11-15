import txaio
txaio.use_twisted()

from autobahn.xbr._schema import FbsSchema

fn = '/tmp/test/bfbs/climate.bfbs'

schema = FbsSchema.load(fn)
print(schema)

obj = schema._root

print(obj)
print('{} enums in schema'.format(obj.EnumsLength()))

print('{} objects in schema:'.format(obj.ObjectsLength()))
for i in range(obj.ObjectsLength()):
    o = obj.Objects(i)
    print(o.Name())
print('')

print('{} services in schema:'.format(obj.ServicesLength()))
for i in range(obj.ServicesLength()):
    svc = obj.Services(i)
    print(svc.Name().decode())
    for j in range(svc.CallsLength()):
        call = svc.Calls(j)
        print(call.Name().decode())
        for k in range(call.AttributesLength()):
            attr = call.Attributes(k)
            print(attr.Key().decode(), attr.Value().decode())
print('')
