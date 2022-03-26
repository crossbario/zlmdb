from zlmdb import __all__

tables = sorted([x for x in __all__ if x.startswith('Map')])

for table in tables:
    print('* :class:`zlmdb.{}`'.format(table))

print('')
print('------')
print('')

tmpl = """.. autoclass:: zlmdb.{}
    :members:
    :show-inheritance:
"""

for table in tables:
    print(tmpl.format(table))
