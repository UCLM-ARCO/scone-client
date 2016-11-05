# Python3 Scone client module

A simple python3 module to interact with a scone-server.

Basic example:

    >>> from scone_client import SconeClient
    >>> client = SconeClient(host='localhost', port=6517)  # default params

    >>> client.sentence('(new-indv {Dumbo} {elephant})')
    '{Dumbo}'

    >>> client.predicate('(is-x-a-y? {Dumbo} {mammal})')
    'YES'

    >>> client.predicate('(is-x-a-y? {Dumbo} {air transport})')
    'MAYBE'

    >>> client.sentence('(new-is-a {Dumbo} {bird})')
    Traceback (most recent call last):
	  ...
      File "...", line 65, in check_error
        raise SconeError(msg)
    scone_client.SconeError: {Dumbo} cannot be a {bird}.

    >>> client.close()


The results for methods `query` and `predicate` are cached to improving performance. Any
invocation to method `sentence` invalidates de cache.
