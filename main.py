from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
import datetime
import time
import func

# If chromedriver not added to enviroment variables PATH, specify the location of it
# driver = webdriver.Chrome(executable_path="C:\\Users\\flavi\\Documents\\chromedriver.exe")
driver = webdriver.Chrome()

driver.get("https://www.aircourts.com/index.php/")
WebDriverWait(driver, 10).until(lambda x: x.find_element(By.ID, "location"))

date = datetime.datetime.utcnow()
page_source = driver.page_source
soup = BeautifulSoup(page_source, 'lxml')

web_sports = []
for sport in soup.find('select', id = 'sport').find_all('option', class_ = 'ac-translate'):
    sport_dict = dict()
    sport_dict['value'] = int(sport['value'])
    sport_dict['name'] = sport.get_text()
    web_sports.append(sport_dict)

web_locations = []
for loc in soup.find('select', id = 'location').find_all('option', class_ = 'ac-translate'):
    loc_dict = dict()
    loc_dict['value'] = int(loc['value'])
    loc_dict['name'] = loc.get_text()
    web_locations.append(loc_dict)


conn = func.create_connection()
print("Connection to db created!")

with conn:

    verif_id = func.insert_verification(conn, date)
    
    func.update_table(conn, web_sports, "sports", "sports_status", verif_id)
    func.update_table(conn, web_locations, "locations", "locations_status", verif_id)

    sport_city_ids = func.sport_locations(conn, ("Padel",))
    #sport_city_ids = [4, [{"id" : 1, "code" : 13}, {"id" : 2, "code" : 12}]]

    web_clubs = []
    for city in sport_city_ids[1]:
        driver.get(f"https://www.aircourts.com/site/search?sport={sport_city_ids[0]}&city={city['code']}&date=&start_time=")
        time.sleep(8)
        page_source = driver.page_source
        time.sleep(2)

        soup = BeautifulSoup(page_source, 'lxml')
        
        if soup.find('div', id = 'empty-text')["style"] == "display: none;": #if  clubs in the c
            print(f'City {city}, with clubs')
            clubs = soup.find('div', id = 'court_container').find_all('div', class_ = 'club-container') # list of padel clubs in "Grande Lisboa"
            for club in clubs:
                club_dict = dict()
                club_dict['value'] = int(club["data-club-id"])
                club_dict['name'] = club.find('div', class_ = 'club-info').h2.text
                club_dict['zone'] = club.find("span", class_ = "club-zone").text
                club_dict['loc_id'] = city["id"]
                web_clubs.append(club_dict)
        else:
            print(f'City {city}, without clubs')

    func.update_table(conn, web_clubs, "clubs", "clubs_status", verif_id)
            
if conn: 
    conn.close()
    print("The SQLite connection is closed")

driver.close()


