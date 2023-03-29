import os
from time import sleep, strftime
from random import randint
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import smtplib
from email.mime.multipart import MIMEMultipart


def load_more():
    """Shows more results button is clicked, so that more page scraping can be done"""
    try:
        more_results = '//div[@class = "resultsPaginator"]'
        driver.find_element_by_xpath(more_results).click()
        print('sleeping.....')
        sleep(randint(25,35))
    except:
        pass


def start_kayak(city_from, city_to, date_start, date_end):
    """City codes - it's the IATA codes!
    Date format -  YYYY-MM-DD"""

    kayak = ('https://www.kayak.com/flights/' + city_from + '-' + city_to +
             '/' + date_start + '-flexible/' + date_end + '-flexible?sort=bestflight_a')
    driver.get(kayak)
    sleep(randint(8, 10))

    # sometimes a popup shows up, so we can use a try statement to check it and close
    try:
        xp_popup_close = '//div[contains(@aria-label,"Close") and contains(@class,"dDYU-close ' \
                         'dDYU-mod-variant-right-corner-outside dDYU-mod-size-default")]'
        driver.find_elements(By.XPATH, xp_popup_close)[0].click()
    except Exception as e:
        print("No pop up button")
        pass

    # sometimes a second popup shows up, so we can use a try statement to check it and close
    try:
        xp_popup_close = '//div[contains(@aria-label,"Close") and contains(@class,"bBPb-close")]'
        driver.find_elements(By.XPATH, xp_popup_close)[0].click()
    except Exception as e:
        print("No pop up button")
        pass

    # sometimes a third popup shows up, so we can use a try statement to check it and close
    try:
        xp_popup_close = '//div[contains(@aria-label,"Close") and contains(@class,"dDYU-close ' \
                         'dDYU-mod-variant-right-corner-outside dDYU-mod-size-default")]'
        driver.find_elements(By.XPATH, xp_popup_close)[0].click()
    except Exception as e:
        print("No pop up button")
        pass
    sleep(randint(60, 95))
    print('loading more.....')

    #     load_more()

    print('starting first scrape.....')
    df_flights_best = page_scrape()
    df_flights_best['sort'] = 'best'
    sleep(randint(60, 80))

    # Let's also get the lowest prices from the matrix on top
    matrix = driver.find_elements(By.XPATH, '//div[contains(@class,"jvgZ")]')
    matrix_prices = [price.text.replace('$', '') for price in matrix]
    matrix_prices = matrix_prices[0].split('\n')
    # if price is greater than $999, it will remove any ","
    counter = 0
    for thousand in matrix_prices:
        matrix_prices[counter] = thousand.replace(",", "")
        counter += 1
    matrix_prices = list(map(int, matrix_prices))
    matrix_min = min(matrix_prices)
    matrix_avg = sum(matrix_prices) / len(matrix_prices)

    print('switching to cheapest results.....')
    cheap_results = '//div[@aria-label = "Cheapest"]'
    driver.find_elements(By.XPATH, cheap_results)[0].click()
    sleep(randint(60, 90))
    print('loading more.....')

    #     load_more()

    print('starting second scrape.....')
    df_flights_cheap = page_scrape()
    df_flights_cheap['sort'] = 'cheap'
    sleep(randint(60, 80))

    print('switching to quickest results.....')
    quick_results = '//div[@aria-label = "Quickest"]'
    driver.find_elements(By.XPATH, quick_results)[0].click()
    sleep(randint(60, 90))
    print('loading more.....')

    #     load_more()

    print('starting third scrape.....')
    df_flights_fast = page_scrape()
    df_flights_fast['sort'] = 'fast'
    sleep(randint(60, 80))

    # saving a new dataframe as an excel file. the name is custom made to your cities and dates
    final_df = pd.concat([df_flights_cheap, df_flights_best, df_flights_fast])
    final_df.to_excel('/Users/connor/Desktop//{}_flights_{}-{}_from_{}_to_{}.xlsx'.format(strftime("%Y%m%d-%H%M"),
                                                                                   city_from, city_to,
                                                                                   date_start, date_end), index=False)
    print('saved df.....')

    # We can keep track of what they predict and how it actually turns out!
    xp_loading = '//div[contains(@id,"advice")]'
    loading = str(driver.find_elements(By.XPATH, xp_loading))
    xp_prediction = '//span[@class="info-text"]'
    prediction = str(driver.find_elements(By.XPATH, xp_prediction))
    print(loading + '\n' + prediction)

    # sometimes we get this string in the loading variable, which will conflict with the email we send later
    # just change it to "Not Sure" if it happens
    weird = '¯\\_(ツ)_/¯'
    if loading == weird:
        loading = 'Not sure'

    username = 'connorrkoch@outlook.com'
    password = 'SixersFan#1!'

    server = smtplib.SMTP('smtp.outlook.com', 587)
    server.ehlo()
    server.starttls()
    server.login(username, password)
    msg = ('Subject: Flight Scraper\n\n\
    Cheapest Flight: {}\nAverage Price: {}\n\nRecommendation: {}\n\nEnd of message'.format(matrix_min, matrix_avg, (
                loading + '\n' + prediction)))
    message = MIMEMultipart()
    message['From'] = 'connorrkoch@outlook.com'
    message['to'] = 'connor.koch@yahoo.com'
    server.sendmail('connorrkoch@outlook.com', 'connor.koch@yahoo.com', msg)
    print('sent email.....')


def page_scrape():
    """This function takes care of the scraping part"""

    print("in page scrape func")
    xp_sections = '//div[@class="xdW8"]'
    sections = driver.find_elements(By.XPATH, xp_sections)
    sections_list = [value.text for value in sections]
    section_a_list = sections_list[::2]  # This is to separate the two flights
    section_b_list = sections_list[1::2]  # This is to separate the two flights

    # if you run into a reCaptcha, you might want to do something about it
    # you will know there's a problem if the lists above are empty
    # this if statement lets you exit the bot or do something else
    # you can add a sleep here, to let you solve the captcha and continue scraping
    # i'm using a SystemExit because i want to test everything from the start
    if section_a_list == []:
        print("empty")
        raise SystemExit

    # I'll use the letter A for the outbound flight and B for the inbound
    a_duration = []
    a_section_names = []
    for n in section_a_list:
        # Separate the time from the cities
        a_section_names.append(''.join(n.split()[2:5]))
        a_duration.append(''.join(n.split()[0:2]))
    b_duration = []
    b_section_names = []
    for n in section_b_list:
        # Separate the time from the cities
        b_section_names.append(''.join(n.split()[2:5]))
        b_duration.append(''.join(n.split()[0:2]))

    xp_dates = '//div[@class="c9L-i"]'
    dates = driver.find_elements(By.XPATH, xp_dates)
    dates_list = [value.text for value in dates]
    a_date_list = dates_list[::2]
    b_date_list = dates_list[1::2]
    # Separating the weekday from the day
    a_day = [value.split()[0] for value in a_date_list]
    a_weekday = [value.split()[1] for value in a_date_list]
    b_day = [value.split()[0] for value in b_date_list]
    b_weekday = [value.split()[1] for value in b_date_list]
    print("a_day")
    print(len(a_day))
    print("a_weekday")
    print(len(a_weekday))
    print("b_day")
    print(len(b_day))
    print("b_weekday")
    print(len(b_weekday))
    #sleep(3600)

    # getting the prices
    print("getting prices")
    xp_prices = '//div[@class="f8F1-price-text"]'
    prices = driver.find_elements(By.XPATH, xp_prices)
    prices_list = [price.text.replace('$', '') for price in prices if price.text != '']
    # if price is greater than $999, it will remove any ","
    counter = 0
    for thousand in prices_list:
        prices_list[counter] = thousand.replace(",", "")
        counter += 1
    prices_list = list(map(int, prices_list))

    # the stops are a big list with one leg on the even index and second leg on odd index
    xp_stops = '//div[@class="JWEO"]'
    stops = driver.find_elements(By.XPATH, xp_stops)
    stops_list = [stop.text[0].replace('n', '0') for stop in stops]
    a_stop_list = stops_list[::2]
    b_stop_list = stops_list[1::2]

    xp_stops_cities = '//div[@class="JWEO"]'
    stops_cities = driver.find_elements(By.XPATH, xp_stops_cities)
    stops_cities_list = [stop.text for stop in stops_cities]
    a_stop_name_list = stops_cities_list[::2]
    b_stop_name_list = stops_cities_list[1::2]

    # this part gets me the airline company and the departure and arrival times, for both legs
    xp_schedule = '//div[@class="VY2U"]'
    schedules = driver.find_elements(By.XPATH, xp_schedule)
    hours_list = []
    carrier_list = []
    for schedule in schedules:
        hours_list.append(schedule.text.split('\n')[0])
        carrier_list.append(schedule.text.split('\n')[1])
    # split the hours and carriers, between a and b legs
    a_hours = hours_list[::2]
    a_carrier = carrier_list[::2]
    b_hours = hours_list[1::2]
    b_carrier = carrier_list[1::2]

    cols = (
    ['Out Day', 'Out Time', 'Out Weekday', 'Out Airline', 'Out Cities', 'Out Duration', 'Out Stops', 'Out Stop Cities',
     'Return Day', 'Return Time', 'Return Weekday', 'Return Airline', 'Return Cities', 'Return Duration', 'Return Stops'
     , 'Return Stop Cities', 'Price'])

    flights_df = pd.DataFrame({'Out Day': a_day,
                               'Out Weekday': a_weekday,
                               'Out Duration': a_duration,
                               'Out Cities': a_section_names,
                               'Return Day': b_day,
                               'Return Weekday': b_weekday,
                               'Return Duration': b_duration,
                               'Return Cities': b_section_names,
                               'Out Stops': a_stop_list,
                               'Out Stop Cities': a_stop_name_list,
                               'Return Stops': b_stop_list,
                               'Return Stop Cities': b_stop_name_list,
                               'Out Time': a_hours,
                               'Out Airline': a_carrier,
                               'Return Time': b_hours,
                               'Return Airline': b_carrier,
                               'Price': prices_list})[cols]

    flights_df['timestamp'] = strftime("%Y%m%d-%H%M")  # so we can know when it was scraped
    print("end of page scrape func")
    return flights_df


# Install Chrome Web browser
driver_service = Service(executable_path=ChromeDriverManager().install())
driver = webdriver.Chrome(service=driver_service)
sleep(2)

print('Welcome to the Kayak Flight Web Scraper')
while True:
    print("Option 1: Start the Kayak Web Scraper")
    print("Option 2: Exit the Kayak Web Scraper")
    option = int(input("Please select either option 1 or 2: "))
    if option == 1:
        city_from = input('From which city? ')
        city_to = input('Where to? ')
        date_start = input('Search around which departure date? Please use YYYY-MM-DD format only ')
        date_end = input('Return when? Please use YYYY-MM-DD format only ')

        # city_from = 'LAX'
        # city_to = 'HNL'
        # date_start = '2023-03-28'
        # date_end = '2023-04-02'

        kayak = ('https://www.kayak.com/flights/' + city_from + '-' + city_to +
                 '/' + date_start + '/' + date_end + '?sort=bestflight_a')
        driver.get(kayak)
        sleep(3)

        start_kayak(city_from, city_to, date_start, date_end)
    elif option == 2:
        break
    else:
        print("Not an option, please select a number from 1-2")

# Bonus: save a screenshot!
driver.save_screenshot('pythonscraping.png')

driver.quit()