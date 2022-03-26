
def print_tables(tables, prefix='zlmdb', inherit=False):
    tables = sorted(tables)

    for table in tables:
        print('* :class:`{}.{}`'.format(prefix, table))

    print('')
    print('------')
    print('')

    tmpl = """.. autoclass:: {}.{}
        :members:
    """
    if inherit:
        tmpl += "    :show-inheritance:"

    for table in tables:
        print(tmpl.format(prefix, table))


from zlmdb import __all__ as a1
print_tables([x for x in a1 if x.startswith('Map')], inherit=True)

from zlmdb._types import __dict__ as a2
print_tables([x for x in a2 if x.endswith('KeysMixin')], prefix='zlmdb._types')
print_tables([x for x in a2 if x.endswith('ValuesMixin')], prefix='zlmdb._types')
