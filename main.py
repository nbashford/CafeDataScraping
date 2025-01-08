"""
Main file runs the cafe data link extraction using selenium and firefox geckodriver browser from cafelinks.py, 
then passes extracted links to extractCafeData.py to extract the information from the links. 
Cafe information extracted: 
    "ID", "Cafe Name", "Link to website", "City", "Street", "Opening times", "Postcode", 
    "Url Location (currently None)", "Has Free Wifi", "Is Laptop Friendly", "Is Pet Friendly", 
    "Latitude", "Longitude".
Latitude and Longitude collected for potential geolocation use with interactive map functionality. 
links to extract
"""
import requests
from bs4 import BeautifulSoup
from cafelinks import ExtractCafeLinks  # extracting cafe links from "https://europeancoffeetrip.com/uk/"
from extractCafeData import CafeData  # extract and process individual cafe data from each cafe hyperlink
import csv
import time
from tqdm import tqdm
import os


def get_html_from_link(link):
    """returns a beautiful soup object from passed hyperlink"""
    response = requests.get(link)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup


def user_continue(start_number, csv_file):
    """option for user to continue from last extracted cafe link - or to restart"""
    print(f"Information extraction will continue from link number: {start_number}\n")
    restart = input("Would you like to DELETE saved CSV data and RESTART the cafe information extraction? "
                    "'Y/N'\n")
    if restart.lower() == 'y':  # delete saved csv file and set start to index 0
        delete_file(csv_file)
        start_number = 0

    return start_number


def user_restart_csv(csv_file):
    print("All cafe information already extracted.")
    re_do = input("Would you like to delete and restart the cafe information extraction? 'Y/N'\n")
    if re_do.lower() == 'y':
        # delete previous csv file
        delete_file(csv_file)
        return True
    else:
        return False


def get_starting_link_number(cafe_data_csvfile):
    """
    Gets the last processed cafe index. If none processed yet - returns index 0. Else (due to runtime stopped or
    interrupted) gets the last cafe data saved index and returns this index
    """
    starting_number = 0
    try:
        # get the last cafe index number
        with open(cafe_data_csvfile, "r") as file:
            print("\nCafe CSV data previously exists")
            reader = csv.reader(file, delimiter=',')
            rows = list(reader)
            header = rows[0]
            id_index = header.index('ID')
            last_row = rows[-1]
            id_value = last_row[id_index]  # obtain last saved cafe index
            starting_number = int(id_value)

            # option for user to delete csv and restart extraction
            starting_number = user_continue(starting_number, cafe_data_csvfile)

    except FileNotFoundError:  # no csv file created yet - do nothing
        pass

    return starting_number


def delete_file(file_name):
    os.remove(f"./{file_name}")


def create_cafe_data(link_filename, cafe_data_csvfile):
    """
    opens the txt file with the individual cafe hyperlinks, passes to CafeData class to extract all the
    required data. If data extraction is interrupted then it resumes from the next link not previously processed.
    :param link_filename: cafe links txt file
    :param cafe_data_csvfile: csv file for extracted cafe data
    """
    next_link_index = get_starting_link_number(cafe_data_csvfile)  # get next non-processed cafe link index
    with open(link_filename, "r") as file:

        level_needed = input("Display individual link extracted information?: 'Y/N'\n")
        detailed_report = True if level_needed.lower() == 'y' else False

        links = file.readlines()
        # loop through all non previously processed links
        for link in tqdm(links[next_link_index:], desc="No. Links Processed", colour="green",
                         initial=next_link_index, total=len(links)):
            try:
                if next_link_index == len(links):
                    raise IndexError
                link = link.strip()
                """could make below function a part of the class methods"""
                soup_html = get_html_from_link(link)
                # pass to CafeData class to extract cafe data
                link_data = CafeData(soup_html, next_link_index+1, link, cafe_data_csvfile, detailed_report)
                link_data.extract_all_data()
                link_data.save_entry()
                time.sleep(2)
            except AttributeError as e:
                print(f"Cafe {next_link_index} unavailable")
            next_link_index += 1


# define filenames
cafe_links_txt_filename = "cafes_links.txt"  # filename for holding initial individual cafe hyperlinks
extracted_cafe_data_csv = "all_cafes_csv.csv"  # csv filename for holding processed individual cafes data


if __name__ == "__main__":

    # get the initial cafe hyperlinks
    cafe_scraper = ExtractCafeLinks(result_txt_filename=cafe_links_txt_filename)  # initialise
    cafe_scraper.run_webscraping()  # get all target cafe links from website

    # pass txt file with links and destination csv file
    create_cafe_data(cafe_scraper.get_txt_file_name(), extracted_cafe_data_csv)

