# internet_usage

Provides an interface to pull carrier data plan usage from a simple command line. 

Was originally intended to be an easy to to graph usage in Zabbix, but evolved into a full command line tool.

Currently supports the following carriers:
- Telus Wireline
- Koodo Mobile

Output in command line mode:
        [precurse@laptop internet_data_usage]$ python2 internet_data_usage.py
        TelusWireline Plan: TELUS Internet 50
        Usage: 49/400 GB

