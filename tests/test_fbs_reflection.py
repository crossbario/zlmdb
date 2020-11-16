import txaio
txaio.use_twisted()

from autobahn.xbr._schema import FbsSchema

for filename in [
    '/tmp/test/bfbs/climate.bfbs',
    '/tmp/test/bfbs/network.bfbs',
    '/tmp/test/bfbs/location.bfbs']:
    schema = FbsSchema.load(filename)
    print(schema)
