Provides an interface to pull carrier data plan usage from a simple command line.

Was originally intended to be a method to graph usage in Zabbix, but evolved into a full command line tool.

Currently supports the following carriers:
- Telus Wireline
- Koodo Mobile

Additional carriers can easily be added if requested.

Installation
------
Install `internet_data_usage` from [Github](http://www.github.com) using git:

    git clone https://github.com/precurse/internet_data_usage.git

Install module requirements using [pip](http://www.pip-installer.org/en/latest/), a
package manager for Python.

    pip install -r requirements.txt

Need pip? Try installing it by running the following from the command
line:

    $ curl https://raw.github.com/pypa/pip/master/contrib/get-pip.py | python


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

        $ ./internet_data_usage.py  -h
        usage: internet_data_usage.py [-h] {term,zabbix,influxdb} ...

        internet_data_usage 0.2-HEAD Copyright (c) 2015 Andrew Klaus
        (andrewklaus@gmail.com)

        optional arguments:
          -h, --help            show this help message and exit

        subcommands:
          {term,zabbix,influxdb}
                                valid subcommands
            term                all output will echo in a terminal
            zabbix              all output will be sent to a Zabbix server
            influxdb            all output will be sent to an influxdb database


Influxdb Usage
------

        $ ./internet_data_usage.py influxdb -h
        usage: internet_data_usage.py influxdb [-h] [-p PORT]
                                               [-c {telus_wireline,koodo_mobile}]
                                               [-a HTTP_USER_AGENT] [-v]
                                               username password i_user i_pass i_host
                                               i_db

        positional arguments:
          username              Username for account access
          password              Carrier password for account access
          i_user                Influxdb username
          i_pass                Influxdb password
          i_host                Influxdb hostname
          i_db                  Influxdb database

        optional arguments:
          -h, --help            show this help message and exit
          -p PORT, --port PORT  Port for influxdb access (default=8086)
          -c {telus_wireline,koodo_mobile}, --carrier {telus_wireline,koodo_mobile}
                                Carrier to query from (default=telus_wireline)
          -a HTTP_USER_AGENT, --http_user_agent HTTP_USER_AGENT
                                Defaults to 'Mozilla/5.0 (X11; Linux x86_64)'
          -v, --verbose


Command line output:
------

Terminal:

        $ ./internet_data_usage.py term -c telus_wireline user@example.com
        Carrier password (will not echo): <password> <enter>
        TelusWireline Plan: TELUS Internet 50
        Usage: 49/400 GB

Zabbix:

        $ ./internet_data_usage.py zabbix -i data_usage user@example.com password
        49

Influxdb:

        $ ./internet_data_usage.py influxdb user@example.com mypass root root localhost internet_usage

