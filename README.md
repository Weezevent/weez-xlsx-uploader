# WEEZ-XLSX-UPLOADER

Python tool to process an xlsx file and update or create attendee contained inside a WeezTicket event.

Using legacy API "/v3" [Doc](https://api.weezevent.com/doctest/#/legacy/v3)



## How to install this tool

1/ Create a python3 virtualenv, using `python3 -m venv env` (for python >= 3.3) 

2/ Activate this virtualenv `source env/bin/activate`

3/ Install dependencies `pip install -r requirements.txt`



## How to use this tool

1/ Ensure virtualenv is activated, if not `source env/bin/activate`

2/ Launch `python -m weez-xlsx-uploader <file.xlsx> <api-key> <api-username> <api-password> <event_id>`

 - <file.xlsx> is the file you want to import (see [here](#file-content) for more details about the columns required in file)
 
 - To retrieve api-key/api-username and api-password : "To obtain an API Key, please open your back-office, go to the "tools" tabs, there is there a menu "API KEY" where you can obtains your API Key and add users."
 
 - <event_id> is the event ID where you want to import the file. 


## How to update this tool

1/ Retrieve latest version of code `git pull`

2/ Update dependencies 

 - Ensure virtualenv is activated, if not `source env/bin/activate`

 - Ensure new requirements if any are installed `pip install -r requirements.txt`


## File content

- First line won't be imported, we wait headers in it (column name used to know which value is in each row)

- Each line will be mapped to a Ticket to import. 

- Some default header name, will be mapped to default form value : (case unsensitive)

    - first_name (alias: firstname, prenom)  
    
    - last_name (alias: lastname, nom)
    
    - email (alias: mail)
    
    - company (alias: societe)
    
    - rate_name (alias: tarif, rate)
        
        In case no rate name are provided the script will create one named "WEEZ XLSX IMPORT" and apply it.
        
        If a rate_name column exists, lines without rate_name will be ignored.
        
        The script will do a get_or_create of a rate with this name inside the event, and use it to link the associated row. 
        
    - barcode
    
        If a barcode is provided it will be used to allow update_or_create.
        We strongly suggest to define barcode yourself before importing in order to allow future re-import of the file
        in case of edition needed.

    - ALL OTHER COLUMNS
    
        Scripts will ensure a form exists in this event, named "WEEZ XSLX IMPORT", this form will auto-contains as questions
        all the columns present here (get_or_create by label, being the name of the column).
        
        And then import the cell value, as being the form answer for this label for this attendee.
