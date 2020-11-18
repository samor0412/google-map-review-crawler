import psycopg2
from requests import get
import re
import html
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time

MAX_REVIEW = 10

def rateToNum(rate):
  return {
    " 1 star ": 1,
    " 2 stars ": 2,
    " 3 stars ": 3,
    " 4 stars ": 4,
    " 5 stars ": 5
  }.get(rate)

def ago_to_time(ago):
  regex = re.search(r'([\w\d]*) (\w*) ago', ago)
  date = datetime.now()

  if regex:
    number = regex.group(1)
    unit = regex.group(2)

    if number == 'a':
      number = '1'

    time_diff = None
    if 'year' in unit:
      time_diff = timedelta(days=365 * int(number))
    elif 'month' in unit:
      time_diff = timedelta(days=30 * int(number))
    elif 'day' in unit:
      time_diff = timedelta(days=int(number))
    else:
      time_diff = timedelta(days=int(number))
    date = date - time_diff
  return date.strftime("%Y-%m-%d %H:%M:%S.000000")

def configure_driver():
    chrome_options = Options()
    chrome_options.add_argument("--lang=en")
    driver = webdriver.Chrome(options = chrome_options)
    return driver


def search_shop_in_google_map(driver, wait, keyword):
  driver.get('''https://www.google.com.hk/maps/search/%s/@51.528308,-0.3817802,10z''' % (keyword.replace(" ", "+")))
  time.sleep(4)
  try:
    click_more_review(driver, wait)
    return True
  except Exception as e:
    try:
      search_result = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='section-result']")))
      search_result.click()
      time.sleep(4)
    except Exception as e:
      pass
      return False
    try:
      click_more_review(driver, wait)
      return True
    except:
      pass
      return True



def click_more_review(driver, wait):
  menu_bt = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'More reviews')]")))
  menu_bt.click()
  time.sleep(4)

def click_most_relevent_review(driver, wait):
  try:
    # menu_bt = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@data-value=\'Sort\']')))
    # menu_bt.click()
    # time.sleep(2)
    # recent_rating_bt = driver.find_elements_by_xpath('//li[@role=\'menuitemradio\']')[1]
    # recent_rating_bt.click()
    # time.sleep(3)
    expand_review_btns = driver.find_elements_by_xpath('//button[contains(text(),\'More\')]')

    for btn in expand_review_btns:
      btn.click()
    time.sleep(1)
    return True
  except Exception as e:
    pass
    return False

def __scroll(driver):
  try:
    scrollable_div = driver.find_element_by_css_selector('div.section-layout.section-scrollbox.scrollable-y.scrollable-show')
    driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', scrollable_div)
  except Exception as e:
    pass
  time.sleep(4)

def extract_review_data(driver):
  response = BeautifulSoup(driver.page_source, 'html.parser')
  __scroll(driver)
  rblock = response.find_all('div', class_='section-review-content')
  parsed_reviews = []
  for index, review in enumerate(rblock):
      if index != MAX_REVIEW:
          parsed_reviews.append(review)

  reviews = []
  for r in parsed_reviews:
    # id_r = r.find('button', class_='section-review-action-menu')['data-review-id']
    username = r.find('div', class_='section-review-title').find('span').text
    try:
        review_text = r.find('span', class_='section-review-text').text
        review_text = review_text + '\n(source: google reviews)' if review_text != '' else '(source: google reviews)'
    except Exception:
        review_text = None
    rating = r.find('span', class_='section-review-stars')['aria-label']
    rel_date = r.find('span', class_='section-review-publish-date').text
    # print(id_r)
    # print(username)
    # print(rating)
    # print(rel_date)
    # print(review_text)
    reviews.append({
      'username': re.sub('\'', '\'\'',username),
      'rating': rating,
      'rel_date': ago_to_time(rel_date),
      'review_text': re.sub('\n', '\'||chr(10)||\'',re.sub('\'', '\'\'',review_text)),  # replace \n and single quote
    })
  if (len(reviews) == 0):
    return
  print(reviews)


def crawlReview(driver, rows): 
  wait = WebDriverWait(driver, 5)
  for index, row in enumerate(rows):
    name = row
    is_searchable = search_shop_in_google_map(driver, wait, name)
    has_reviews = False
    click_most_relevent_review(driver, wait)
    extract_review_data(driver)

driver = configure_driver()
crawlReview(driver, ['London Bridge', 'London Eye'])
