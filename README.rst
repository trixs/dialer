Concurrent dialer
#################

.. image:: https://img.shields.io/travis/trixs/dialer/master.svg?style=flat-square&label=TravisCI
    :target: https://travis-ci.org/trixs/dialer

Test application demonstrating multithreading skills.

Build
=====

- Install dependencies ``pip install -r requirements-dev.txt``
- Run stylistic checks ``pylint . dialer test``
- Run unit tests and generate coverage report ``pytest --cov=dialer --cov-branch --cov-fail-under=100 test && coverage report -m``
- Generate documentation ``cd docs && make html``

Design
======

Activities related to concurrent dialing are implemented in methods
``dialing_wrapper`` and ``connect``. The former deals with dialing a single
phone number and processing the result, or handling an exception. The latter
starts multiple concurrent dial attempts, waits for the first successful
connection. In the case that all started dial attempts fail ``connect`` will
fetch new phone numbers from the database and create a new batch of 
concurrent attempts to dial new set of leads.

Unit tests are grouped into two classes: ``TestPowerDialer`` and ``TestConcurrentConnections``.
The first tests that observer methods ``on_agent_login``, ``on_call_started`` and others perform
proper state changes and prevent execution if called when agent is in the wrong state.
The second test suite verifies proper logic while executing concurrent dialing.