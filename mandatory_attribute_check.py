from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import time
import csv
import undetected_chromedriver.v2 as uc

class Scraper:
    def __init__(self):
        '''
        When we initialize a scraper object, we need to create our webdriver
        instance
        '''
        # Please note that this is the directory of my webdriver instance
        co = uc.ChromeOptions()

        co.add_argument("--disable-extensions")
        co.add_argument("--disable-popup-blocking")
        co.add_argument("--profile-directory=Default")
        co.add_argument("--disable-plugins-discovery")
        co.add_argument("--incognito")
        # co.add_argument("--headless")
        co.add_argument('--no-sandbox')
        co.add_argument("--disable-setuid-sandbox")
        co.add_argument("user_agent=DN")
        co.add_argument("--start-maximized")
        # pxy = "2.56.46.10:8800"

        # co.add_argument('--proxy-server=%s' % pxy)

        # driver = uc.Chrome(options=co)
        self.browser = uc.Chrome(options=co)
        self.browser.delete_all_cookies()
        # self.browser = webdriver.Chrome('C:/Users/iamso/Desktop/chromedriver')

    def search(self):
        '''
        This method is used to fetch the ibba.org address and find the search
        bar element to enter in a search that we are concerned with, in this
        case, we are searching for all brokers in the Los Angeles area
        '''
        self.browser.get('https://www.ibba.org')
        search = self.browser.find_element_by_id('places')
        search.send_keys("Los Angeles")
        search.send_keys(u'\ue007')
        time.sleep(1)

    def display_result_list(self):
        '''
        This method is not in use by the main instructions, but it is useful
        for if we would like to find the general information of the brokers on
        the main seach page within our search
        '''
        result = self.browser.find_elements_by_class_name("result")
        for item in result:
            print(item.text)

    def get_num_of_brokers(self):
        '''
        Fetches the number of brokers displayed at the top of a screen after a
        search
        '''
        return int(self.browser.find_element_by_xpath("""//*[@id="CPRLocator"]/
        div[1]""").text[16:])

    def more_details(self, broker_index):
        '''
        Takes in the broker_index'th broker, and clicks the more_details button
        that corresponds to that broker
        '''
        time.sleep(1)
        details = self.browser.find_element_by_xpath("""//*[@id="CPRLocator"]/
        div[2]/div[""" + str(broker_index) + """]/section/div[2]/a""")
        details.click()

    def get_email(self):
        '''
        This method tries to find the "show email" butotn associated with the
        broker profile, if it exists on the page
        '''
        # We can easily find the web element associate with email using the
        # find_element_by_class_name method, however we will need to have the
        # xpath in order to click the object to display the email
        email_section = self.browser.find_element_by_class_name("email")

        # We must initialize finding_email in some sense, in the cases where
        # finding email cannot be set to the xpaths we are trying to match up
        finding_email = None

        # For a range of information indexes, we are trying to match the email
        # with the correct xpath in order to obtain the correct email
        for index in range(0, 10):
            # It is possible that the xpaths we are iterating through do not
            # translate to real webelements, in which case we handle this error
            try:
                finding_email = self.browser.find_element_by_xpath("""//*
                [@id="broker-data"]/tbody/tr[""" + str(index) + """]""")
            except NoSuchElementException:
                pass
            # In the case that we found the email button, we click it in order
            # to display the email and collect it
            if email_section == finding_email:
                email_button = self.browser.find_element_by_xpath("""//*
                [@id="broker-data"]/tbody/tr[""" + str(index) + """]/td[2]/
                a""")
                time.sleep(0.1)
                email_button.click()
                time.sleep(0.1)
                break
        return self.browser.find_element_by_xpath("""//*[@id="broker-data"]/
        tbody/tr[""" + str(index) + """]/td[2]/a""").text

    def get_info(self):
        '''
        This method is the meat and potatoes of this program, it tries to
        collect all of the key parameters we track:name, phone number, address,
        company and email of the broker on the profile page we are currently
        navigated to. In the case where there is no such information to be
        displayed (the broker didn't input that parameter), it adds an empty
        string to the list of info (translates to an empty cell in the CSV file
        this generates)
        '''
        time.sleep(1)
        info = []
        email = self.get_email()
        # name
        try:
            info += [self.browser.find_element_by_class_name("page-title").
                     text]
        except (NoSuchElementException, AttributeError):
            info += [""]
        # phone
        try:
            info += [self.browser.find_elements_by_class_name("phone")[1].
                     text[6:]]
        except (NoSuchElementException, AttributeError, IndexError):
            info += [""]
        # address
        try:
            info += [self.browser.find_element_by_class_name("address").
                     text[8:].replace("\n", ", ")]
        except (NoSuchElementException, AttributeError):
            info += [""]
        # company
        try:
            info += [self.browser.find_element_by_class_name("company").
                     text[8:]]
        except (NoSuchElementException, AttributeError):
            info += [""]
        # email
        try:
            info += [email]
        except (NoSuchElementException, AttributeError):
            info += [""]
        return info

    def go_back(self):
        '''
        Call this method to back one element in the search history
        '''
        self.browser.execute_script("window.history.go(-1)")

    def quit(self):
        '''
        Call this method to close the browser instance
        '''
        self.browser.quit()

# Initialize our scraper and browser instance
scraper = Scraper()
# Create the initial search, defined by our search method
scraper.search()
# Create and empty list for the raw data to be added to
raw_data = []

# We use the get_num_of_brokers method to determine the upper bound on our
# broker indices and we iterate through them
for broker_index in range(1, scraper.get_num_of_brokers() + 1):
    # We want to count how many errors we catch, if we catch too many we need
    # to restart the search since the chances are, we landed on a broken link.
    # This makes this part bug-proof.
    error_counter = 0
    while True:
        if error_counter >= 10:
            scraper.search()
            break
        time.sleep(1)
        # Try to obtain the information, but if we cannot, simply add another
        # error to the error counter
        try:
            scraper.more_details(broker_index)
            raw_data += [scraper.get_info()]
            scraper.go_back()
            break
        except NoSuchElementException:
            error_counter += 1
    try:
        # Displaying the last item of the data list, just as a check to make
        # sure we are always tracking the most recent broker page
        print(raw_data[-1])
    except IndexError:
        pass
# Close our browser instance, we collected all the data!
scraper.quit()

# Now we want to write all the data we just collected to a CSV file, this
# simply creates a new CSV file and writes a row for every broker. All of the
# information lines up with header containing the tracked parameters
with open('Los_Angeles_Broker_Data.csv', 'w', newline='') as new_file:
    csv_writer = csv.writer(new_file)
    # Header
    csv_writer.writerow(['Name', 'Phone Number', 'Address', 'Company',
                         'Email'])
    for line in raw_data:
        csv_writer.writerow(line)