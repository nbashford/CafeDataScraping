"""
Extracts all hyperlinks of individual cafes from europeancoffeetrip website
"""
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, ElementNotInteractableException
from selenium.webdriver.firefox.options import Options
import os


class ExtractCafeLinks:

    def __init__(self, result_txt_filename):
        self.cafe_website = "https://europeancoffeetrip.com/uk/"
        self.more_cafes_button_id = "cg-more"
        self.initial_cafes_id = "first-cafes"
        self.additional_cafes_loaded_id = "rest-cafes"
        self.individual_cafe_hyperlink_prefix = "https://europeancoffeetrip.com/cafe/"
        self.driver_timeout_time = 10
        self.bsoup = None  # holds the parsed html
        self.cafe_hyperlink_list = None  # holds all hyperlink to individual cafes
        self.driver = None
        self.txt_file_name = result_txt_filename

    def run_webscraping(self):
        run = self.check_if_existing_file()
        if run:
            self.setup_geckodriver() # 1
            self.open_website()  # 2
            self.load_more_cafes() # 3
            self.check_additional_cafes_loaded()  # 4
            self.get_all_links()  # 5
            self.save_cafelinks_to_txt()

    def setup_geckodriver(self):
        firefox_options = Options()
        firefox_options.add_argument("--disable-extensions")
        firefox_options.add_argument("--headless")
        firefox_options.set_preference("dom.push.enabled", False)
        self.driver = webdriver.Firefox(options=firefox_options)  # path to gecko driver already on path

    def open_website(self):
        self.driver.get(self.cafe_website)
        print(f"Website {self.cafe_website} opened")

    def load_more_cafes(self):
        """clicks button to load additional cafe data"""
        try:
            load_more = WebDriverWait(self.driver, self.driver_timeout_time).until(EC.presence_of_element_located(
                (By.ID, self.more_cafes_button_id)))
        except TimeoutException:

            """NEED TO ADD SOME ADDITIONAL CHECKS OR FUNCTIONALITY HERE
            MAYBE COULD EXTRACT ANY DIV CONTAINER NAMES AND THEN UPDATE THE CLASS VARIABLE"""

            print("No load button loaded")

        else:
            try:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                load_more.click()
            except (ElementClickInterceptedException, ElementNotInteractableException):
                # Scroll into view
                self.driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth' });",
                                           load_more)
                time.sleep(3)
                load_more.click()

        print(f"Load more cafes button clicked")

    def check_additional_cafes_loaded(self):
        """checks if the other cafe data has loaded"""
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, self.additional_cafes_loaded_id)))
        except TimeoutException:

            """NEED TO ADD SOME ADDITIONAL CHECKS OR FUNCTIONALITY HERE
            MAYBE COULD EXTRACT ANY DIV CONTAINER NAMES AND THEN UPDATE THE CLASS VARIABLE"""

            print("No other cafes loaded")
        else:
            full_page_html = self.driver.page_source
            self.get_html_soup(full_page_html)

        print(f"additional cafes loaded")

    def get_html_soup(self, page_html):
        """passes page html to create a beautiful soup object"""
        self.bsoup = BeautifulSoup(page_html, 'html.parser')
        print("Extracted beautiful soup html")


    def get_all_links(self):
        """extract all anchor tags from the div containers holding individual cafe data"""

        """may need to add a check again to check and update the id of the containers"""

        first_cafes_containers = self.bsoup.find('div', id=self.initial_cafes_id)
        first_cafes_anchors = first_cafes_containers.find_all('a')

        second_cafes_container = self.bsoup.find('div', id=self.additional_cafes_loaded_id)
        second_cafes_anchors = second_cafes_container.find_all('a')

        self.cafe_hyperlink_list = self.extract_anchor_links(first_cafes_anchors, second_cafes_anchors)

        print("cafe links obtained")

    def extract_anchor_links(self, first_anchor_list, second_anchor_list):
        """extracts the correct hyperlink leading to each individual cafe data"""

        all_anchors_list = [first_anchor_list, second_anchor_list]
        all_cafes_links = []

        for anchor_list in all_anchors_list:
            for anchor in anchor_list:
                link = anchor.get('href')
                if link.startswith(self.individual_cafe_hyperlink_prefix):
                    all_cafes_links.append(link)

        return all_cafes_links

    def update_filename(self):
        """user updates filename for saved cafes data. Checks if valid username."""
        user_filename = input("Please enter filename:\n")

        # check if any invalid filename characters
        invalid_characters = r'<>:"/\|?*\x00'
        if any(char in user_filename for char in invalid_characters):
            print("Invalid character in filename")
            self.update_filename()  # get input again

        num_dots = user_filename.count(".")
        # if invalid name due to +1 '.'
        if num_dots > 1:
            print("filename invalid - unknown extension")
            self.update_filename()  # get input again

        # if extension
        elif num_dots == 1:
            # change extension to txt
            if not user_filename.endswith(".txt"):
                user_filename_without_extension = user_filename.split('.')[0]
                user_filename = f"{user_filename_without_extension}.txt"

        # filename has no extension
        else:
            user_filename = f"{user_filename}.txt"

        self.txt_file_name = user_filename
        print(f"filename updated to: {self.txt_file_name}")

    def save_cafelinks_to_txt(self):
        """writes each extracted hyperlink to txt file"""
        user_input = input(f"\nDefault file name: {self.txt_file_name}\nChange file name: 'Y/N'\n")
        if user_input.lower() == "y":
            self.update_filename()
        with open(self.txt_file_name, "w") as file:
            for cafe_link in self.cafe_hyperlink_list:
                file.write(cafe_link + '\n')
        print(f"Cafe links saved to file: {self.txt_file_name}")

    def check_if_existing_file(self):
        """checks if txt file of cafe links already created. Deletes and updates if user selects."""
        if os.path.exists(f"./{self.txt_file_name}"):
            print(f"file: '{self.txt_file_name}' with cafe links already created")
            user_input = input("Delete and update the previous txt file? 'Y/N'\n")
            if user_input.lower() == 'y':
                self.delete_txt_file()
            else:
                return False
        return True

    def delete_txt_file(self):
        """deletes previous txt file of cafe links"""
        os.remove(f"./{self.txt_file_name}")
        print("Previous cafe links txt file deleted")

    def get_txt_file_name(self):
        return self.txt_file_name
