# Python Scone client module

A simple python3 module to interact with a scone-server.

Basic example:

    >>> from scone_client import SconeClient
    >>> client = SconeClient()

    >>> client.query('(new-indv {Dumbo} {elephant})')
    '{Dumbo}'

    >>> client.predicate('(is-x-a-y? {Dumbo} {mammal})')
    'YES'

    >>> client.predicate('(is-x-a-y? {Dumbo} {air transport})')
    'MAYBE'

    >>> client.query('(new-is-a {Dumbo} {bird})')
    Traceback (most recent call last):
	  ...
      File "...", line 65, in check_error
        raise SconeError(msg)
    scone_client.SconeError: {Dumbo} cannot be a {bird}.

    >>> client.close()