# -*- coding: utf-8 -*-
'''
Created on Sun Aug  2 05:05:24 2020

@author: Ari Argoud
'''
import requests
from bs4 import BeautifulSoup
import mysql.connector
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager


"""Allows for SQL to be written 'easily' in python"""
class SQL_Framework():
    
    def __init__(self, host = 'localhost', user = 'root', password = 'Sin_shadow1'):
        self.host = host
        self.user = user
        self.password = password
    
    #Writes SQL NOT requiring database specification
    def dbc(self, cmd):  #Acronym dbc = database commands.    
        db = mysql.connector.connect(
            host = self.host,
            user = self.user,
            passwd = self.password,
            autocommit = True
            )
        myCursor = db.cursor()
        myCursor.execute(cmd)
        dbcList = []
        for x in myCursor:
            dbcList.append(x)
        return dbcList
    
    #Writes SQL requiring database specification
    def tc(self, name, cmd): #Acronym tc = table commands. 
        db = mysql.connector.connect(
            host = self.host,
            user = self.user,
            passwd = self.password,
            database = name,
            autocommit = True
            )        
        myCursor = db.cursor()
        myCursor.execute(cmd)
        tcList = []
        for x in myCursor:
            tcList.append(x)
        return tcList
    
    
"""
pdr.net is structured such that each index page (sorted alphabetically by brand name)
is split into seperate web adderesses consisting of 20 or less alphabetized results.

Example: https://www.pdr.net/browse-by-drug-name?letter=G&currentpage=3 displays 
41-60 of 91 results starting with G.

""" 
def main():  
    db = SQL_Framework() #Used here to set up database and tables to contain scraped information from pdr.net. instantiate with your username, password, etc.
        
    #Checks if database 'pdr_db' has already been created, if not, creates appropriate database.
    if len(db.dbc("SHOW DATABASES LIKE 'pdr_db'")) > 0:
        print("Database 'pdr_db' Already Created")
    else:
        try:
            db.dbc("CREATE DATABASE pdr_db")
            print("Database Created - 'pdr_db'")
        except:
            print("Something has gone wrong creating database 'pdr_db'")
            pass
        
        
    #Checks if tables 'drug_index' and 'drug_interactions' have already been created, if not, attempts to create appropriate tables.    
    if len(db.tc("pdr_db","SHOW TABLES LIKE 'drug_index'")) > 0 and \
    len(db.tc("pdr_db","SHOW TABLES LIKE 'drug_interactions'")) > 0:
        print("Tables 'drug_index' and 'drug interactions' already created in database 'pdr_db'")
        
    if len(db.tc("pdr_db","SHOW TABLES LIKE 'drug_index'")) <= 0:
        try:
            #Creates table drug_index containing columns brand_name(primary key), chemical_name, and summary_link .
            db.tc("pdr_db", "CREATE TABLE drug_index \
                    (brand_name VARCHAR(255) PRIMARY KEY, \
                    chemical_name VARCHAR(255), \
                    summary_link VARCHAR(255) \
                    )")
            print("Created Table in database 'pdr_db' - 'drug_index'")
        except:
            print("Something has gone wrong creating table 'drug_index'")
            pass
        
    if len(db.tc("pdr_db","SHOW TABLES LIKE 'drug_interactions'")) <= 0:
        try:
            #Creates table drug_interactions containing columns brand_name(foreign key referencing drug_index.brand_name), interaction_name, and interaction_description.
            db.tc("pdr_db", "CREATE TABLE drug_interactions \
                (brand_name VARCHAR(255), \
                interaction_name VARCHAR(255), \
                interaction_strength VARCHAR(20), \
                interaction_description TEXT, \
                FOREIGN KEY(brand_name) REFERENCES drug_index(brand_name) \
                ON DELETE CASCADE \
                ON UPDATE CASCADE \
                )")
            print("Created Table in database 'pdr_db' - 'drug_interactions'")
        except:
            print("Something has gone wrong creating table 'drug_interactions'")
            pass
     
        
    #Requests and parses pdr.net 'Browse by Drug Name' landing page.
    page = requests.get('https://www.pdr.net/browse-by-drug-name?letter=')
    soup = BeautifulSoup(page.content, 'html.parser')
    
    navLinks = [] #Container for links to first alpha-numeric index pages  
    
    #Extracts links from parsed html.
    for link in soup.find_all('a', href=True):
            #Cleans non-navigational links. 
            if 'browse-by-drug-name?' in link.get('href') and link.get('href')[-1].isalpha():
                #Fills navLinks with links to first.  
                navLinks.append(link.get('href'))
                
    #iterates through alphabetized nav links
    for i in navLinks:
        print(i)
        increment = 1 #count of numerical sub-pages 
        
        #loops through numerical sub-pages
        pageCount = 1
        while True:
            drugLinks = [] #container for links to drug summary pages
            brandNames = [] #container for cleaned brand names
            chemNames = [] #container for cleaned chemical names
            page = requests.get(i + '&currentpage=' + str(increment))
            soup = BeautifulSoup(page.content, 'html.parser')
            increment+=1
            
            drugNameSoup = soup.find_all('div', class_='drugName') #Contains parsed HTML drug names. 
            drugLinkSoup = soup.find_all('a', href=True) #Contains parsed HTML links. 
            #Breaks numerical sub-page loop if no entries are found on the page.
            if len(drugNameSoup) == 0: #or len(drugLinkSoup) == 0:
                break
            
            #Finds and stores summary links in drugLinks by cleaning drugLinkSoup.
            for link in drugLinkSoup:
                if 'summary' in link.get('href'):
                    drugLinks.append(link.get('href').lower())
                    # print(link.get('href'))

            # print("drug link count: " +str(len(drugLinks)))
            
 
            for j in range(0,len(drugLinks)):

                for k in range (0,len(drugNameSoup)):
                    bn = drugNameSoup[k].text.replace('\n','').splitlines()[1].replace('\'', ' ').strip() #Acronym: Brand Name - Contains drug brand name cleaned from drugNameSoup
                    bnFirstWord = bn.split(' ', 1)[0].replace('/', '-').replace(',', '-').replace('.','-').replace('+','-').replace('•', 'bull').replace('%', '-').lower()
                    
                    if bnFirstWord in drugLinks[j]:
                        
                        cn = drugNameSoup[j].text.replace('\n','').splitlines()[2].replace('\'', ' ').strip()[1:-1] #Acronym: Chemical Name - Contains chemical name cleaned from drugNameSoup
                        brandNames.append(bn)
                        chemNames.append(cn)
                        break
                    else:
                        pass 
            # if len(brandNames) != len(drugLinks):
            #     print(str(len(brandNames))+ '   ' + str(len(drugLinks))+" | page: "+str(pageCount))
            #     print(brandNames)
            pageCount+=1      
            
            #Constructs database insert statement.
            for name, chem, link in zip(brandNames, chemNames, drugLinks):
                try:
                    db.tc("pdr_db",'INSERT INTO drug_index VALUES ("'+name+'","'+chem+'","'+link+'")') #Structures SQL insert statement, for some reason it didn't like it when I tried to use formatting
                    # print("INSERT INTO drug_index VALUES (brand_name, chemical_name, summary_link) ('"+name+"','"+chem+"','"+link+"')") #Test case for insert statement 
                    pass
                except:
                    pass
                
                hdr = {'User-Agent':'Mozilla/5.0'}
                page = requests.get(link, headers = hdr)
                soup = BeautifulSoup(page.content, 'html.parser')
                hdr = {'User-Agent':'Mozilla/5.0'}
                page = requests.get(link, headers = hdr)
                soup = BeautifulSoup(page.content, 'html.parser')
                tags = soup.find_all('div', 'clearfix drugSection')
                
                for x in tags:
                    if x.find('h3', 'drugSummary').text == 'DRUG INTERACTIONS':
                        iNames = x.find_all('strong')
                        iDescriptions = x.text.split(':')
                        del iDescriptions[0]
                        print(str(len(iNames)) + '   ' + str(len(iDescriptions)))
                        for y, z in zip(iNames, iDescriptions):
                            iName = y.text[:-1]
                            iDescription = z.rsplit('.', 1)[0][1:]
                            iStrength = iDescription.split(' ', 1)[0][1:-1]
                            iDescription = iDescription.split(' ', 1)[1]
                            # print("INSERT INTO drug_interactions VALUES ('"+name+"','"+iName+"','"+iDescription+"')")
                            db.tc("pdr_db",'INSERT INTO drug_interactions VALUES ("'+name+'","'+iName+'","'+iStrength+'","'+iDescription+'")')

                '''
                To Do:
                -Alter try/except statements to catch errors
                -Check for appropriate pairing of names, links, etc DONE
                -Build command line UI
                
                '''

        increment = 1 #Resets sub-page count.
        break # this break statement stops the program from running through more than the first letter of results                 
main()
