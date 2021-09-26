import json
import psycopg2
from psycopg2 import Error

with open("local.json") as f:
    data = json.load(f)

def create_connection():
    """Create a database connection to the Postgresql database"""

    conn = None
    try: 
        # Connect to database
        conn = psycopg2.connect(user=data["user"],
                                  password=data["pass"],
                                  host=data["host"],
                                  port=data["port"],
                                  database=data["db"])                                  
        return conn
    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL: ", error)
    return conn

def insert_verification(conn, date):
  """
    Records each verification occurance with day, month, year and time
    Param: 
      conn: connection to db
      date: date in UTC 
            datetime.datetime(year, month, day, hour, minute, second, microsecond)
    Return: 
      id of verification
  """
  insert_verification = "INSERT INTO verifications (day, month, year, time) VALUES (%s, %s, %s, %s) RETURNING id"
  day = date.day #int
  month = date.month #int
  year = date.year #int
  time = f'{date.hour}:{date.minute}:{date.second}' #string
  values = (day, month, year, time)
  cursor = conn.cursor()
  cursor.execute(insert_verification, values)
  conn.commit()
  insert_id = cursor.fetchone()
  cursor.close()
  return insert_id

def get_header(conn, table):
  """
    Gets table header row (column name)
    Param: 
      conn: connection to db
      table: 
        var type: string
        context:  table to get the header from 
    Return: 
      list with column names
  """
  cursor = conn.cursor()
  header = f"SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table}'"
  cursor.execute(header)
  table_header = cursor.fetchall() #returns list of tuples
  header_list = []
  for c_header in table_header:
    header_list.append(c_header[0])
  return header_list

def call_table(conn, table):
  """
    Gets table values
    Translates tables into dictionaries
    Param: 
      conn: connection to db
      table: 
        var type: string
        context:  table to get the values from 
    Return: 
      list of dictionaries -> each dictionary is a row. Key/value pairs are headers and respective values per row
  """
  cursor = conn.cursor()
  values_list = []
  header_list = get_header(conn, table) # list with table header values
  sql = f"SELECT * FROM {table}"
  cursor.execute(sql)
  for value in cursor.fetchall(): # iterates over list of tuples
    value_dict = dict() # dictionary to store each row values. keys = column headers, value = respective row value
    for index, c_header in enumerate(header_list):
      value_dict[f"{c_header}"] = value[index]
    values_list.append(value_dict)
  return values_list

def call_status(conn, table):
  """
    Gets the most recent status os tables xxx_status
    Param: 
      conn: connection to db
      table: 
        var type: string
        context:  table to get the values from
    Return: following dictionary
      header_values = {
        "header" = [], # list with header values
        "body" = [] # list of dictionaries. Each dictionary is a row. Key/value pairs are headers and respective values per row
      }
  """
  header_list = get_header(conn, table) # list with column names
  header_list.pop(0) # removes id column
  values_list = []
  header_values = {}
  header_values["header"] = header_list
  sql = f"""SELECT DISTINCT ON ({header_list[0]}) {header_list[0]}, {header_list[1]}, {header_list[2]}
            FROM   {table}
            ORDER  BY {header_list[0]}, {header_list[2]} DESC""" # header_list[0] = sport_id or anoter referenced "table"_id, header_list[1] = available, header_list[2] = verif_id
  cursor = conn.cursor()
  cursor.execute(sql)
  # creates the list of dictionaries for the table
  for value in cursor.fetchall():
    value_dict = dict()
    for index, c_header in enumerate(header_list):
      value_dict[f"{c_header}"] = value[index]
    values_list.append(value_dict)
  header_values["body"] = values_list
  return header_values

def insert_csl(conn, table, sql_param):
  """
    Insert clubs, sports, locations
    Param: 
      conn: connection to db
      table: 
        var type: string
        context:  table to get the values from
      sql_param: tuple of sql parameters to match placeholders
    Return: id of inserted row
  """
  header_list = get_header(conn, table)
  header_list.pop(0)
  translation = {39 : None,
                 91 : 40, 
                 93 : 41}
  place_holders = ["%s" for item in header_list] # creates a list with many place holders as items in header_list
  place_holders = str(place_holders).translate(translation) # list to str and ' -> None, [ -> { and ] -> }
  header_list = str(header_list).translate(translation) # list to str and ' -> None, [ -> { and ] -> }
  insert = f"INSERT INTO {table} {header_list} VALUES {place_holders} RETURNING id"
  cursor = conn.cursor()
  cursor.execute(insert, sql_param)
  conn.commit()
  returned_id = cursor.fetchone()
  cursor.close()
  return returned_id

def insert_status(conn, table, sql_param):
  """
    Insert values to status tables
    Param: 
      conn: connection to db
      table: 
        var type: string
        context:  table to get the values from
      sql_param: tuple of sql parameters to match placeholders
    Return: id of inserted row
  """
  header_list = get_header(conn, table)
  header_list.pop(0)
  insert = f"INSERT INTO {table} ({header_list[0]}, {header_list[1]}, {header_list[2]}) VALUES (%s, %s, %s) RETURNING id"
  cursor = conn.cursor()
  cursor.execute(insert, sql_param)
  conn.commit()
  returned_id = cursor.fetchone()
  cursor.close()
  return returned_id 

def update_table(conn, web_param, table, table_status, verif_id):
  """
    Main funcion: compares values from web data and vice versa. Updates database accordingly
    Param: 
      conn: connection to db
      web_param: list of dicts
      table: string with table name without status
      table_status: string with table_status name
      verif_id: id of actual verification inserted in verifications table  
  """
  db_locations = call_table(conn, table)
  db_table_status = call_status(conn, table_status)

  # compare locations in web against locations in db
  for loc in web_param:
    code = loc['value']
    name = loc['name'] #loc.get_text()
    exist = False
    for db_loc in db_locations:
      if (db_loc["code"] == code):
        if (db_loc["name"] == name):
          # print("exists1")
          exist = True
          # updates available to TRUE if it was previously FALSE
          for status in db_table_status['body']:
            if (status[f"{db_table_status['header'][0]}"] == db_loc["id"] and status[f"{db_table_status['header'][1]}"] == False):
              sql_param = (db_loc["id"], "TRUE", verif_id)
              insert_status(conn, table_status, sql_param)
    # insert location in db if not exists and add it to locations status as TRUE
    if exist == False: #does not exists on table
      # print("not exist in db")
      sql_param = tuple(loc.values())
      location_id = insert_csl(conn, table, sql_param)
      sql_param = (location_id, "TRUE", verif_id)
      insert_status(conn, table_status, sql_param)
  
  # compare locations in db agains locations in web
  for db_loc in db_locations:
    exist = False
    for web_loc in web_param:
      if (web_loc["value"] == db_loc["code"] and web_loc["name"] == db_loc["name"]):
        exist = True
        # print(f'{db_loc["name"]} exists in db')
    # update status to FALSE if location not present in web with the verification date
    if exist == False:
      # print(f'{db_loc["name"]} in db but not in WEB')
      # updates available to FALSE if it was previously TRUE
      for status in db_table_status['body']:
        if (status[f"{db_table_status['header'][0]}"] == db_loc["id"] and status[f"{db_table_status['header'][1]}"] == True):
          sql_param = (db_loc["id"], "FALSE", verif_id)
          insert_status(conn, table_status, sql_param)

def sport_locations(conn, sport):
  """
    Gets sport code and all the locations id's and codes
    Param: 
      conn: connection to db
      sport: var type: tuple with one string ("Padel",)
    Return: tuple with sport code and list of dicts with all id's and codes for the cities
  """
  get_sport_code = "SELECT code FROM sports WHERE name = (%s)"
  #location_select = 'SELECT code FROM locations WHERE name = (?)'
  get_locations_id_code = 'SELECT id, code FROM locations'
  cursor = conn.cursor()
  cursor.execute(get_sport_code, sport)
  retrieved_list = cursor.fetchall()
  sport_code = retrieved_list[0][0]
  cursor.execute(get_locations_id_code)
  locs_param_list = []
  for item in cursor.fetchall():
    locs_param = dict()
    locs_param["id"] = item[0]
    locs_param["code"] = item[1]
    locs_param_list.append(locs_param)
  cursor.close()
  return (sport_code, locs_param_list)



