Provides an interface to pull carrier data plan usage from a simple command line.

Was originally intended to be a method to graph usage in Zabbix, but evolved into a full command line tool.

Currently supports the following carriers:
- Telus Wireline
- Koodo Mobile


Command Line Usage
------

        $ ./internet_data_usage.py -h
        usage: internet_data_usage.py [-h] {term,zabbix} ...

        internet_data_usage 0.2-HEAD Copyright (c) 2015 Andrew Klaus
        (andrewklaus@gmail.com)

        optional arguments:
          -h, --help     show this help message and exit

        subcommands:
          {term,zabbix}  valid subcommands
            term         all output will echo in a terminal
            zabbix       all output will be sent to a Zabbix server


Terminal Usage
------

        $ ./internet_data_usage.py term -h
        usage: internet_data_usage.py term [-h] [-p PASSWORD]
                                           [-c {telus_wireline,koodo_mobile}]
                                           [-a HTTP_USER_AGENT] [-v]
                                           username

        positional arguments:
          username              Username for account access

        optional arguments:
          -h, --help            show this help message and exit
          -p PASSWORD, --password PASSWORD
                                Carrier password for account access (will prompt if
                                not specified)
          -c {telus_wireline,koodo_mobile}, --carrier {telus_wireline,koodo_mobile}
                                Carrier to query from (default=telus_wireline)
          -a HTTP_USER_AGENT, --http_user_agent HTTP_USER_AGENT
                                Defaults to 'Mozilla/5.0 (X11; Linux x86_64)'
          -v, --verbose


Zabbix/Monitoring Usage
------

        $ ./internet_data_usage.py zabbix -h
        usage: internet_data_usage.py zabbix [-h]
                                             [-i {data_usage,data_use_unit,data_plan_total,plan}]
                                             [-c {telus_wireline,koodo_mobile}]
                                             [-a HTTP_USER_AGENT] [-v]
                                             username password

        positional arguments:
          username              Username for account access
          password              Carrier password for account access

        optional arguments:
          -h, --help            show this help message and exit
          -i {data_usage,data_use_unit,data_plan_total,plan}, --item {data_usage,data_use_unit,data_plan_total,plan}
                                Item to request (default=data_usage)
          -c {telus_wireline,koodo_mobile}, --carrier {telus_wireline,koodo_mobile}
                                Carrier to query from (default=telus_wireline)
          -a HTTP_USER_AGENT, --http_user_agent HTTP_USER_AGENT
                                Defaults to 'Mozilla/5.0 (X11; Linux x86_64)'
          -v, --verbose


Command line output:
------

Terminal:

        $ ./internet_data_usage.py term -c telus_wireline user@example.com
        Carrier password (will not echo): <password. <enter>
        TelusWireline Plan: TELUS Internet 50
        Usage: 49/400 GB

Zabbix:

        $ ./internet_data_usage.py zabbix -i data_usage user@example.com password
        49

