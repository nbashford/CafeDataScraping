"""Extracts information from the individual cafe hyperlinks, saves to a csv file."""

import time
import os
import csv
import requests
import json


def geocode_address(postcode, street=None, city=None, country="UK"):
    """
    Gets and returns the Latitude and Longitude, from; street address, postcode, town/city, provided in the UK.
    Passes the full address first to openstreetmap api, but if unsuccessful, passes only the postcode to get a
    more approximate address.
    """
    lat = None
    lon = None
    url = "https://nominatim.openstreetmap.org/search"

    if street and city:  # full address details
        params = {
            'street': street,
            'city': city,
            'country': country,
            'postalcode': postcode,
            'format': 'json',
            'addressdetails': 1
        }

    else:  # only pass the postcode for search - less specific
        params = {
            'postalcode': postcode,
            'format': 'json',
            'addressdetails': 1
        }

    headers = {
        'User-Agent': os.getenv("OSM_USER_AGENT")
    }


    # get API response
    response = requests.get(url, params=params, headers=headers)

    try:
        data = response.json()
        try:
            if data:  # extract latitude and longitude
                lat = data[0]["lat"]
                lon = data[0]["lon"]
            else:  # issue with identifying openstreetmap location from full address
                time.sleep(1)
                if street and city:
                    # call function again with lower precision
                    lat, lon = geocode_address(postcode)

        except KeyError:
            print("OpenStreetMap response data for latitude / longitude has changed. please review:")
            print(json.dumps(data, indent=4))  # print response data for review

    except requests.exceptions.JSONDecodeError:
        print("Failed to parse JSON:")
        print(response.text)

    return lat, lon


class CafeData:
    def __init__(self, soup, number, link, cafe_data_csvfile, report_level):
        self.id = number  # current link index number
        self.link = link  # cafe hyperlink
        self.bSoup = soup  # beautiful soup object
        self.save_filename = cafe_data_csvfile  # csv filename

        # individual cafa data to extract
        self.name = None  # cafe name
        self.name_html_class = "cafe-name"
        self.city = None  # location town/city
        self.postcode = None
        self.street_location = None
        self.location_html_class = "cafe-address"
        self.opening = None  # opening time string
        self.opening_html_class = "cafe-open"
        self.url_location = None  # currently NONE
        self.wifi = None  # if wifi friendly cafe
        self.laptop_friendly = None  # if laptop friendly cafe
        self.pet_friendly = None  # if pet friendly cafe
        self.service_friendly_html_class = "cafe-services"
        self.latitude = None
        self.longitude = None

        self.detailed_report = report_level

    def extract_all_data(self):
        """extracts all information from cafe hyperlink"""
        self.get_name()
        self.get_opening()
        self.get_services()
        self.get_location()
        self.get_latitude_longitude()

    def get_name(self):
        """find and extract the cafe name"""
        try:
            name = self.bSoup.find("h1", class_=self.name_html_class)
            self.name = name.get_text().title()  # update the name attribute
        except:
            if self.detailed_report:
                print("No name found for")

        if self.detailed_report:
            print(f"Name: {self.name}")


    def get_location(self):
        """
        Gets formatted street address, postcode and city from the address text - since the address format is not
        always consistent.
        Sets: Postcode, City, Street.
        """
        location = self.bSoup.find("div", class_=self.location_html_class)
        location_text = location.get_text()

        # split into street, and postcode + city ('[-1]' is just 'UK' - not needed)
        location_text = location_text.split(', ')[:-1]

        # 1. get the postcode and city location from the location text
        postcode_city = location_text[-1].split(" ")  # postcode and city
        postcode = []
        city = []
        # postcode - either singular or including space must contain a digit
        for text in postcode_city:
            postcode_text = False
            for char in text:
                # if digit in word = postcode
                if char.isdigit():
                    postcode.append(text)
                    postcode_text = True
                    break
            # if no digit in word - is city/town name
            if not postcode_text:
                city.append(text)

        # format postcode - each postcode inward code is always 3 characters long - add space before last 3 chars
        postcode_joined = "".join(postcode).strip()
        self.postcode = postcode_joined[0:-3] + " " + postcode_joined[-3:]

        self.city = " ".join(city).strip()  # set city name

        # 2. get the street location
        street = " ".join(location_text[:-1]).strip()  # '[-1]' is postcode and city name
        if "UK" in street:
            street = street.replace("UK", "")  # remove redundant 'UK' from address
        if self.city in street:
            street = street.replace(self.city, "")  # remove redundant 'City' - occasionally repeats
        self.street_location = street

        if self.detailed_report:
            print(f"Postcode: {self.postcode}")
            print(f"city: {self.city}")
            print(f"street_location: {self.street_location}")

    def get_opening(self):
        """
        Condenses multiple row opening time table into a single line string.
        Condenses redundant opening times information if weekday, weekend, or every day has same opening times.
        """
        try:
            # 1. get each row of opening time text
            opening_div = self.bSoup.find("div", class_=self.opening_html_class)
            div_rows = opening_div.find_all("tr")
            opening_times = []
            for row in div_rows:  # join each row of text
                text = row.get_text(separator=' ', strip=True)
                opening_times.append(text)

            # 2. get the formatted opening string from the joined opening text
            self.opening = self.get_opening_string(opening_times)

        except:
            """could put functionality to adjust the opening html_class name fot the container for opening, then 
            re-run
            is there an error logging file i can create?
            """
            print("Could not get opening times")

        if self.detailed_report:
            print(f"opening: {self.opening}")

    def get_opening_string(self, open_string):
        """
        condenses/reformats the opening times - to reduce the amount of text needed if weekdays or weekend opening
        times are the same - returns open_string list as a single string, with each day opening times separated by '|'
        :param open_string: list of opening times for each day, format: "Day: open time"
        :return: string
        """
        times = [entry.split(": ")[1] for entry in open_string]
        weekday_same_time = all(time == times[0] for time in times[:5])
        weekend_same_time = all(time == times[5] for time in times[-2:])

        # weekday is same but weekends not
        if weekday_same_time and not weekend_same_time:
            open_string = f"Monday - Friday: {times[0]}|Saturday: {times[5]}|Sunday: {times[6]}"

        # weekdays same and weekends same
        elif weekday_same_time and weekend_same_time:
            open_string = f"Monday - Friday: {times[0]}|Saturday - Sunday: {times[5]}"

        # weekdays not same but weekend is
        elif not weekend_same_time and weekend_same_time:
            open_string = (f"Monday: {times[0]}|Tuesday: {times[1]}|Wednesday: {times[2]}|Thursday: {times[3]}"
                           f"|Friday: {times[4]}|Saturday - Sunday: {times[5]}")

        # weekdays and weekends not the same
        else:
            open_string = "|".join(open_string)

        return open_string

    def get_latitude_longitude(self):
        """get the latitude and longitude for the cafe address"""
        if self.street_location and self.postcode and self.city:  # get lat lon with more precision
            self.latitude, self.longitude = geocode_address(self.postcode, street=self.street_location, city=self.city)


        elif self.postcode:  # get lat lon with less precision
            self.latitude, self.longitude = geocode_address(self.postcode, street=self.street_location, city=self.city)

        else:
            print("Address has not been obtained to determine latitude and longitude")

        if self.detailed_report:
            print(f"latitude and longitude: {self.latitude}, {self.longitude}")

    def get_url_location(self):
        """Placeholder function - not currently used"""
        url = None
        try:
            pass
        except:
            pass
        return url

    def get_services(self):
        """get the wi-fi, pet, and laptop friendly text from cafe link if present"""
        try:
            # get container
            cafe_service_container = self.bSoup.find("div", class_=self.service_friendly_html_class)
            # get rows
            service_rows = cafe_service_container.find_all("tr")
            for row in service_rows:
                # get all text from row
                text = row.get_text(separator=': ', strip=True)
                if "Free Wi-Fi" in text:
                    self.wifi = "Free Wi-Fi"
                if "Dog" in text:
                    self.pet_friendly = "Pet Friendly"
                if "Laptop" in text:
                    self.laptop_friendly = "Laptop Friendly"

        except:
            if self.detailed_report:
                print("No Service data available")

        if self.detailed_report:
            print(f"Has Wifi: {self.wifi}")
            print(f"Allows Pets: {self.pet_friendly}")
            print(f"Laptop Friendly: {self.laptop_friendly}")

    def save_entry(self):
        """
        saves cafe data to csv file.
        Creates csv headers if no previous file created then adds data as row in csv file.
        Update row headers and column position if editing or re-ordering data.
        """
        # if file not yet created
        if not os.path.isfile(self.save_filename):
            with open(self.save_filename, "w") as file:
                writer = csv.writer(file)
                # create csv header
                writer.writerow(["ID", "Name", "Link", "City", "Street", "Opening", "Postcode", "Url Location",
                                 "Wifi", "Laptop Friendly", "Pet Friendly", "Latitude", "Longitude"])

        # add extracted cafe data to csv
        with open(self.save_filename, "a") as file:
            writer = csv.writer(file)
            writer.writerow([self.id, self.name, self.link, self.city, self.street_location, self.opening, self.postcode,
                             self.url_location, self.wifi, self.laptop_friendly,
                             self.pet_friendly, self.latitude, self.longitude])
