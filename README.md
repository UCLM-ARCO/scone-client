# Scone client module

Basic example:

    In [1]: from scone_client import SconeClient

    In [2]: client = SconeClient()

    In [3]: client.query('(new-indv {Dumbo} {elephant})')
    Out[3]: '{Dumbo}'

    In [4]: client.predicate('(is-x-a-y? {Dumbo} {mammal})')
    Out[4]: 'YES'

    In [5]: client.predicate('(is-x-a-y? {Dumbo} {air transport})')
    Out[5]: 'MAYBE'

    In [6]: client.close()
