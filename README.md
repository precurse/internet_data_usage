Provides an interface to pull carrier data plan usage from a simple command line.

Was originally intended to be a method to graph usage in Zabbix, but evolved into a full command line tool.

Currently supports the following carriers:
- Telus Wireline
- Koodo Mobile


Command Line Usage
------

        $ ./internet_data_usage.py -h
        usage: internet_data_usage.py [-h] [-p PASSWORD]
                                      [-c {telus_wireline,koodo_mobile}]
                                      [-a HTTP_USER_AGENT] [-v]
                                      username

        positional arguments:
          username              Username for account access

        optional arguments:
          -h, --help            show this help message and exit
          -p PASSWORD, --password PASSWORD
                                Password for account access (Optional: will prompt if
                                required)
          -c {telus_wireline,koodo_mobile}, --carrier {telus_wireline,koodo_mobile}
                                Carrier to query from (default=telus_wireline)
          -a HTTP_USER_AGENT, --http_user_agent HTTP_USER_AGENT
          -v, --verbose


Command line output:
------

        $ ./internet_data_usage.py -c telus_wireline user@example.com
        Carrier password (will not echo): <enter> 
        TelusWireline Plan: TELUS Internet 50
        Usage: 49/400 GB

