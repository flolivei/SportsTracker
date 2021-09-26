# SportsTracker

SportsTracker is a Python script that tracks the occurrence of Padel sport in cities and the number of Padel clubs in those cities. The script automates Chrome web browser on specific pages from https://www.aircourts.com/ with Selenium WebDriver, extracts HTML data with Beautiful Soup and saves relevant data in a predefined PostgresSQL database. 

**Video Demo:** https://youtu.be/TcYCif1PDWU

## Requirements

- ### Libraries

The packages (libraries) needed to run the script are specified in the configuration file `requirements.txt`.

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install the dependencies stated in the configuration file above.

```bash
pip install -r requirements.txt
```
- ### Database
SportsTracker stores it's data on a PostgreSQL database. Refer to https://www.postgresql.org/ for installation instructions.

Prior to the first execution, 7 predefined tables must be created. The structure of each individual table can be found in `postgresql_tables.txt`.

A relation diagram between all tables is also available bellow. 

![Table Schema](https://user-images.githubusercontent.com/84719851/134774621-bbd1c012-310c-40b4-a31c-b56c26aca33f.png)

- ### Selenium
SportsTracker automates Chrome web browser by means of Selenium WebDriver. Refer to https://www.selenium.dev/ for installation instructions. 

***Note**: correct `chromedriver` version must be installed and driver path must be added to enviroment variables PATH*


## Files
**- local.json**
Stores database credentials. SportsTracker will read this file to establish a connection with the database. 

**- requirements.txt**
Configuration file with the libraries needed for the execution. 

**- postgresql_tables.txt**
File with the structure of each individual table that needs to the created *prio* to the execution of SportsTracker.

**- func.py**
File  with the functions needed for the execution of SportsTracker.  

**- main.py**
Main file from where SportsTracker script is executed. 

## Run the script

After the requirements are in place, simply run the command bellow to run the script and see the automation in place. 

```python
python main.py
```

## Behind the curtains

The main goal of this project is evaluate the progression of Padel sport in Portugal. AirCourts platform is the main reservation tool where most Padel clubs are registered. 

Tracking the number of clubs and cities those clubs are in through a large number of days, an analysis can be done to understand if the sport is increasing it's popularity.

The database was initially thought to be developed in SQLite, but after some research it was decided to stablish the database in PostgreSQL to better migrate the script to an online platform. 

The development of SportsTracker took place on a local platform, but with some small adjustments it can be migrated to on online platform like Heroku and automate the execution of the script once a day. 

By manipulating the tables in the database we are able to retrieve data for further analyses on the availability of clubs in a specific city.
