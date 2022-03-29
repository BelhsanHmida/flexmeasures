.. _tut_toy_schedule:

Toy example: Scheduling a battery, from scratch
===============================================

Let's walk through an example from scratch! We'll ... 

- install FlexMeasures
- create an account with a battery asset
- load hourly prices
- optimize a 12h-schedule for a battery that is half full

Below are the ``flexmeasures`` CLI commands we'll run, and which we'll explain step by step. There are some other crucial steps for installation and setup, so this becomes a complete example from scratch, but this is the meat:

.. code-block:: console

    # setup an account with a user, a battery (Id 2) and a market (Id 3)
    $ flexmeasures add toy-account --kind battery
    # load prices to optimise the schedule against
    $ flexmeasures add beliefs --sensor-id 3 --source toy-user prices-tomorrow.csv
    # make the schedule
    $ flexmeasures add schedule --sensor-id 2 --optimization-context-id 3 \
        --start ${TOMORROW}T07:00+01:00 --duration PT12H \
        --soc-at-start 50% --roundtrip-efficiency 90%


Okay, let's get started!


Install Flexmeasures and the database
---------------------------------------

This example is from scratch, so we'll assume you have nothing prepared but a (Unix) computer with Python and two well-known developer tools, `pip <https://pip.pypa.io>`_ and `docker <https://www.docker.com/>`_

We install the FlexMeasures platform, use Docker to run a postgres database and tell FlexMeasures to create all tables.

.. code-block:: console

    $ pip install flexmeasures
    $ docker pull postgres; docker run --name pg-docker -e POSTGRES_PASSWORD=docker -e POSTGRES_DB=flexmeasures-db -d -p 5433:5432 postgres:latest 
    $ export SQLALCHEMY_DATABASE_URI="postgresql://postgres:docker@127.0.0.1:5433/flexmeasures-db" SECRET_KEY=notsecret LOGGING_LEVEL="WARNING" DEBUG=0 
    $ flexmeasures db upgrade


Add some structural data
---------------------------------------

The data we need for our example is both structural (e.g. a company account, a user, an asset) and numeric (we want market prices to optimize against).

Let's create the structural data first.

FlexMeasures offers a command to create a toy account with a battery:

.. code-block:: console

    $ flexmeasures add toy-account --kind battery

    Toy account Toy Account with user toy-user@flexmeasures.io created successfully. You might want to run `flexmeasures show account --id 1`
    The sensor for battery charging is <Sensor 2: charging, unit: MW res.: 0:15:00>.
    The sensor for Day ahead prices is <Sensor 3: Day ahead prices, unit: EUR/MWh res.: 1:00:00>.

And with that, we're done with the structural data for this tutorial! 

If you want, you can inspect what you created:

.. code-block:: console

    $ flexmeasures show account --id 1                       
    
    =============================
    Account Toy Account (ID:1):
    =============================

    Account has no roles.

    All users:
    
      Id  Name      Email                     Last Login    Roles
    ----  --------  ------------------------  ------------  -------------
       1  toy-user  toy-user@flexmeasures.io                account-admin

    All assets:
    
      Id  Name          Type      Location
    ----  ------------  --------  -----------------
       3  toy-battery   battery   (52.374, 4.88969)
       2  toy-building  building  (52.374, 4.88969)
       1  toy-solar     solar     (52.374, 4.88969)

    $ flexmeasures show asset --id
    
    ===========================
    Asset toy-battery (ID:3):
    ===========================

    Type     Location           Attributes
    -------  -----------------  ---------------------
    battery  (52.374, 4.88969)  capacity_in_mw:0.5
                                min_soc_in_mwh:0.05
                                max_soc_in_mwh:0.45

    All sensors in asset:
    
      Id  Name      Unit    Resolution    Timezone          Attributes
    ----  --------  ------  ------------  ----------------  ------------
       2  charging  MW      15 minutes    Europe/Amsterdam


Yes, that is quite a large battery :)

.. note:: Obviously, you can use the ``flexmeasures`` command to create your own, custom account and assets. See :ref:`cli`. And to create, edit or read asset data via the API, see :ref:`v3_0`.

We can also look at the battery asset in the UI of FlexMeasures (start FlexMeasures with ``flexmeasures run``, username is "toy-user@flexmeasures.io", password is "toy-password"):

.. image:: https://github.com/FlexMeasures/screenshots/raw/main/tut/toy-schedule/asset-view.png
    :align: center


Add some price data
---------------------------------------

Now to add price data. First, we'll create the csv file with prices (EUR/MWh, see the setup for sensor 3 above) for tomorrow.

.. code-block:: console

    $ TOMORROW=$(date --date="next day" '+%Y-%m-%d')
    $ echo "Hour,Price                                      
    $ ${TOMORROW}T00:00:00,10
    $ ${TOMORROW}T01:00:00,11
    $ ${TOMORROW}T02:00:00,12
    $ ${TOMORROW}T03:00:00,15
    $ ${TOMORROW}T04:00:00,18
    $ ${TOMORROW}T05:00:00,17
    $ ${TOMORROW}T06:00:00,10.5
    $ ${TOMORROW}T07:00:00,9
    $ ${TOMORROW}T08:00:00,9.5
    $ ${TOMORROW}T09:00:00,9
    $ ${TOMORROW}T10:00:00,8.5
    $ ${TOMORROW}T11:00:00,10
    $ ${TOMORROW}T12:00:00,8
    $ ${TOMORROW}T13:00:00,5
    $ ${TOMORROW}T14:00:00,4
    $ ${TOMORROW}T15:00:00,4
    $ ${TOMORROW}T16:00:00,5.5
    $ ${TOMORROW}T17:00:00,8
    $ ${TOMORROW}T18:00:00,12
    $ ${TOMORROW}T19:00:00,13
    $ ${TOMORROW}T20:00:00,14
    $ ${TOMORROW}T21:00:00,12.5
    $ ${TOMORROW}T22:00:00,10
    $ ${TOMORROW}T23:00:00,7" > prices-tomorrow.csv

This is time series data, in FlexMeasures we call "beliefs". Beliefs can also be sent to FlexMeasures via API or imported from open data hubs like `ENTSO-E <https://github.com/SeitaBV/flexmeasures-entsoe>`_ or `OpenWeatherMap <https://github.com/SeitaBV/flexmeasures-openweathermap>`_. However, in this tutorial we'll show how you can read data in from a CSV file. Sometimes that's just what you need :)

.. code-block:: console

    $ flexmeasures add beliefs --sensor-id 3 --source toy-user prices-tomorrow.csv
    Successfully created beliefs

In FlexMeasures, all beliefs have a data source. Here, we use the username of the user we created earlier. We could also pass a user ID, or the name of a new data source we want to use for CLI scripts.

.. note:: Attention: We created and imported prices where the times have no time zone component! That happens a lot. FlexMeasures will then interpret them as UTC time. So if you are in Amsterdam time, the start time for the first price, when expressed in your time zone, is actually `2022-03-03 01:00:00+01:00`.

Let's look at the price data we just loaded:

.. code-block:: console

    $ flexmeasures show beliefs --sensor-id 3 --start ${TOMORROW}T01:00:00+01:00 --duration PT24H
    Beliefs for Sensor 'Day ahead prices' (Id 3).
    Data spans a day and starts at 2022-03-03 01:00:00+01:00.
    The time resolution (x-axis) is an hour.
    ┌────────────────────────────────────────────────────────────┐
    │         ▗▀▚▖                                               │ 18EUR/MWh
    │         ▞  ▝▌                                              │ 
    │        ▐    ▚                                              │ 
    │       ▗▘    ▐                                              │ 
    │       ▌      ▌                                     ▖       │ 
    │      ▞       ▚                                  ▗▄▀▝▄      │ 
    │     ▗▘       ▐                                ▗▞▀    ▚     │ 13EUR/MWh
    │   ▗▄▘         ▌                              ▐▘       ▚    │ 
    │ ▗▞▘           ▚                              ▌         ▚   │ 
    │▞▘             ▝▄           ▗                ▐          ▝▖  │ 
    │                 ▚▄▄▀▚▄▄   ▞▘▚               ▌           ▝▖ │ 
    │                        ▀▀▛   ▚             ▐             ▚ │ 
    │                               ▚           ▗▘              ▚│ 8EUR/MWh
    │                                ▌         ▗▘               ▝│ 
    │                                ▝▖        ▞                 │ 
    │                                 ▐▖     ▗▀                  │ 
    │                                  ▝▚▄▄▄▄▘                   │ 
    └────────────────────────────────────────────────────────────┘
            5           10           15           20
                        ██ Day ahead prices



Again, we can also view these prices in the FlexMeasures UI:

.. image:: https://github.com/FlexMeasures/screenshots/raw/main/tut/toy-schedule/sensor-data-prices.png
    :align: center

.. note:: Technically, these prices for tomorrow may be forecasts (depending on whether you are running through this tutorial before or after the day-ahead market's gate closure). You can also use FlexMeasures to compute forecasts yourself. See :ref:`tut_forecasting_scheduling`.


Make a schedule
---------------------------------------

Finally, we can create the schedule, which is the main benefit of FlexMeasures (smart real-time control).

We'll ask FlexMeasures for a schedule for our charging sensor (Id 2). We also need to specify what to optimise against. Here we pass the Id of our market price sensor (3).
To keep it short, we'll only ask for a 12-hour window starting at 7am. Finally, the scheduler should know what the state of charge of the battery is when the schedule starts (50%) and what its roundtrip efficiency is (90%).

.. code-block:: console

    $ flexmeasures add schedule --sensor-id 2 --optimization-context-id 3 \
        --start ${TOMORROW}T07:00+01:00 --duration PT12H \
        --soc-at-start 50% --roundtrip-efficiency 90%
    New schedule is stored.

Great. Let's see what we made:

.. code-block:: console

    $ flexmeasures show beliefs --sensor-id 2 --start ${TOMORROW}T07:00:00+01:00 --duration PT12H
    Beliefs for Sensor 'charging' (Id 2).
    Data spans 12 hours and starts at 2022-03-04 07:00:00+01:00.
    The time resolution (x-axis) is 15 minutes.
    ┌────────────────────────────────────────────────────────────┐
    │   ▐                      ▐▀▀▌                           ▛▀▀│ 
    │   ▞▌                     ▞  ▐                           ▌  │ 0.4MW
    │   ▌▌                     ▌  ▐                          ▐   │ 
    │  ▗▘▌                     ▌  ▐                          ▐   │ 
    │  ▐ ▐                    ▗▘  ▝▖                         ▐   │ 
    │  ▞ ▐                    ▐    ▌                         ▌   │ 0.2MW
    │ ▗▘ ▐                    ▐    ▌                         ▌   │ 
    │ ▐  ▝▖                   ▌    ▚                        ▞    │ 
    │▀▘───▀▀▀▀▀▀▀▀▀▀▀▀▀▀▌────▐─────▝▀▀▀▀▀▀▀▀▜─────▐▀▀▀▀▀▀▀▀▀─────│ 0MW
    │                   ▌    ▞              ▐    ▗▘              │ 
    │                   ▚    ▌              ▐    ▐               │ 
    │                   ▐   ▗▘              ▝▖   ▌               │ -0.2MW
    │                   ▐   ▐                ▌   ▌               │ 
    │                   ▐   ▐                ▌  ▗▘               │ 
    │                    ▌  ▞                ▌  ▐                │ 
    │                    ▌  ▌                ▐  ▐                │ -0.4MW
    │                    ▙▄▄▌                ▐▄▄▞                │ 
    └────────────────────────────────────────────────────────────┘
            10           20           30          40
                            ██ charging


Here, negative values denote output from the grid, so that's when the battery gets charged. 

We can also look at the charging schedule in the FlexMeasures UI (reachable via the asset page for the battery):

.. image:: https://github.com/FlexMeasures/screenshots/raw/main/tut/toy-schedule/sensor-data-charging.png
    :align: center

Recall that we only asked for a 12 hour schedule here. We started our schedule *after* the high price peak (at 5am) and it also had to end *before* the second price peak fully realised (at 9pm). Our scheduler didn't have many opportunities to optimize, but it found some. For instance, it does buy at the lowest price (around 3pm) and sells it off when prices start rising again (around 6pm).


.. note:: The ``flexmeasures add schedule`` command also accepts state-of-charge targets, so the schedule can be more sophisticated. But that is not the point of this tutorial. See ``flexmeasures add schedule --help``. 