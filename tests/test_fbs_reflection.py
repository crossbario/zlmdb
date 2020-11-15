import txaio
txaio.use_twisted()

from autobahn.xbr._schema import FbsSchema

schema = FbsSchema.load('/tmp/test/bfbs/climate.bfbs')
print(schema)
