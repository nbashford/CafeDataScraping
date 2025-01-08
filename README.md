# CafeDataScraping
extracts and processes UK cafe data from europeancoffeetrip to CSV, for use in subsequent best cafes website.

  Prerequisites
- Install Firefox and ensure it is up to date.
- Download [geckodriver](https://github.com/mozilla/geckodriver/releases) for your operating system.
- Add `geckodriver` to system's PATH. For example:
  - On macOS/Linux:
    ```bash
    export PATH=$PATH:/path/to/geckodriver
    ```
  - On Windows:
    Add the directory containing `geckodriver.exe` to your system’s environment variables.


This project will result in two file created: 
1. "cafes_links.txt" - containing hyperlinks to individual UK cafes from europeancoffeetrip
2. "all_cafes_csv.csv" - containing all the extracted information from each cafe, with the data:
   "ID", "Cafe Name", "Link to website", "City", "Street", "Opening times", "Postcode", 
    "Url Location (currently None)", "Has Free Wifi", "Is Laptop Friendly", "Is Pet Friendly", 
    "Latitude", "Longitude".
