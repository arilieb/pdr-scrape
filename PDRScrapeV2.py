# -*- coding: utf-8 -*-
'''
Created on Sun Aug  2 05:05:24 2020

@author: Ari Argoud
'''
import requests
from bs4 import BeautifulSoup
import mysql.connector

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
    
class PDR_DB_Commander():
    def __init__(self, dbName = 'pdr_db'):
        self.dbName = dbName
        self.sql = SQL_Framework()
        
    def makeDB(self):
        
        #Checks if database 'pdr_db' has already been created, if not, creates appropriate database.
        if len(self.sql.dbc("SHOW DATABASES LIKE '" + self.dbName + "'")) > 0:
            print("Database 'pdr_db' Already Created")
        else:
            try:
                self.sql.dbc("CREATE DATABASE " + self.dbName)
                print("Database Created - " + self.dbName)
            except:
                print("Something has gone wrong creating database - " + self.dbName)
                pass
            
    def makeDrugIndexTable(self):
        if len(self.sql.tc(self.dbName,"SHOW TABLES LIKE 'drug_index'")) > 0:
            print("Table - drug_index - already created in database " + self.dbName)
        else:
            try:
                #Creates table drug_index containing columns brand_name(primary key), chemical_name, and summary_link .
                self.sql.tc("pdr_db", "CREATE TABLE drug_index \
                (brand_name VARCHAR(255) PRIMARY KEY, \
                chemical_name VARCHAR(1000), \
                summary_link VARCHAR(1000) \
                )")
                print("Created Table in database " + self.dbName + " - drug_index")
            except:
                print("Something has gone wrong creating table - drug_index")
                pass
            
    def makeDrugInteractionsTable(self):
        if len(self.sql.tc(self.dbName,"SHOW TABLES LIKE 'drug_interactions'")) > 0:
            print("Table - drug_interactions - already created in database " + self.dbName)
        else:
            try:
                #Creates table drug_index containing columns brand_name(primary key), chemical_name, and summary_link .
                self.sql.tc("pdr_db", "CREATE TABLE drug_interactions \
                (brand_name VARCHAR(255), \
                interaction_name VARCHAR(1000), \
                interaction_strength VARCHAR(20), \
                interaction_description TEXT, \
                FOREIGN KEY(brand_name) REFERENCES drug_index(brand_name) \
                ON DELETE CASCADE \
                ON UPDATE CASCADE \
                )")
                print("Created Table in database " + self.dbName + " - drug_interactions")
            except:
                print("Something has gone wrong creating table - drug_interactions")
                pass
            
    def insertToDrugIndex(self, brandName, chemName, drugLink):
        self.sql.tc(self.dbName,'INSERT INTO drug_index VALUES ("'+brandName+'","'+chemName+'","'+drugLink+'")')
    
    def insertToDrugInteractions(self, brandName, interactionName, interactionStrength, interactionDescription):
        self.sql.tc(self.dbName,'INSERT INTO drug_interactions VALUES ("'+brandName+'","'+interactionName+'","'+interactionStrength+'","'+interactionDescription+'")')
    

"""
pdr.net is structured such that each index page (sorted alphabetically by brand name)
is split into seperate web adderesses consisting of 20 or less alphabetized results.

Example: https://www.pdr.net/browse-by-drug-name?letter=G&currentpage=3 displays 
41-60 of 91 results starting with G.

"""             
class PDR_Scraper():
    def __init__(self, home = 'https://www.pdr.net/browse-by-drug-name?letter='):
        
        self.cmd = PDR_DB_Commander()
        self.cmd.makeDB()
        self.cmd.makeDrugIndexTable()
        self.cmd.makeDrugInteractionsTable()
        
        self.home = home
        self.page = requests.get(home)
        self.soup = BeautifulSoup(self.page.content, 'html.parser')
        self.navLinks = []
        
        #Requests and parses pdr.net 'Browse by Drug Name' landing page.
        for link in self.soup.find_all('a', href=True):
            #Cleans non-navigational links. 
            if 'browse-by-drug-name?' in link.get('href') and link.get('href')[-1].isalpha():
                #Fills navLinks with links to alphabetical landing pages.  
                self.navLinks.append(link.get('href'))
        
    def populateTables(self):
        for i in self.navLinks:
            print("scraping " + i)
            increment = 1 #count of numerical sub-pages 

            #loops through numerical sub-pages
            while True:
                drugLinks = [] #container for links to drug summary pages
                brandNames = [] #container for cleaned brand names
                chemNames = [] #container for cleaned chemical names
                page = requests.get(i + '&currentpage=' + str(increment))
                increment+=1 #sub-page count increasing
                soup = BeautifulSoup(page.content, 'html.parser')

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
    
                for j in range(0,len(drugLinks)):
                    for k in range (0,len(drugNameSoup)):
                        bn = drugNameSoup[k].text.replace('\n','').splitlines()[1].replace('\'', ' ').strip() #Acronym: Brand Name - Contains drug brand name cleaned from drugNameSoup
                        bnFirstWord = bn.split(' ', 1)[0].replace('/', '-').replace(',', '-').replace('.','-').replace('+','-').replace('•', 'bull').replace('%', '-').lower()
                        
                        if bnFirstWord in drugLinks[j]:
                            
                            cn = drugNameSoup[j].text.replace('\n','').splitlines()[2].replace('\'', ' ').strip()[1:-1] #.replace("[", "(").replace("]", ")").replace(";",".") #Acronym: Chemical Name - Contains chemical name cleaned from drugNameSoup
                            brandNames.append(bn)
                            chemNames.append(cn)
                            break
                        else:
                            pass 

                #Constructs database insert statement.
                for name, chem, link in zip(brandNames, chemNames, drugLinks):
                    try:
                        self.cmd.insertToDrugIndex(name, chem, link) 
                    except:
                        if len(self.cmd.sql.tc('pdr_db', 'SELECT * FROM drug_index WHERE brand_name = "' + name +'"')) > 0:
                            pass
                        else:
                            print("Something has gone wrong inserting \n\"{}\", \n\"{}\", \n\"{}\" \nto drug_index table".format(name,chem,link))
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
                            iDescriptions = x.text.split(': (')
                            del iDescriptions[0]
                            # print(str(len(iNames)) + '   ' + str(len(iDescriptions)))
                            for y, z in zip(iNames, iDescriptions):
                                iName = ''
                                iDescription = ''
                                iStrength = ''
                                
                                try:
                                    iName = y.text[:-1]
                                    iDescription = z.rsplit('.', 1)[0][1:]
                                    iStrength = iDescription.split(' ', 1)[0][1:-1]
                                    iDescription = iDescription.split(' ', 1)[1].replace("\"","'")
                                    # print("INSERT INTO drug_interactions VALUES ('"+name+"','"+iName+"','"+iDescription+"')")
                                except Exception as e: 
                                    print(e)
                                    print("\n",name,"\n",y,"\n",z,"\n")
                                    
                                if len(self.cmd.sql.tc('pdr_db', 'SELECT * FROM drug_interactions WHERE brand_name = "' + name + '" AND interaction_name = "' + iName + '"')) > 0:
                                    pass
                                else:
                                    try:
                                        self.cmd.insertToDrugInteractions(name, iName, iStrength, iDescription)
                                    except:
                                        print("something has gone wrong inserting \n\"{}\", \n\"{}\", \n\"{}\", \n\"{}\" \nto drug_interactions table".format(name, iName, iStrength, iDescription))
                                        pass
            increment = 1 #Resets sub-page count.
            # break # this break statement stops the program from running through more than the first letter of results 
            
def main():
    pdr = PDR_Scraper()
    pdr.populateTables()
main()  
   

    