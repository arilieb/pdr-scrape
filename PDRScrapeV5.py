# -*- coding: utf-8 -*-
'''
Created on Sun Aug  2 05:05:24 2020

@author: Ari Argoud
'''
import requests
from bs4 import BeautifulSoup
import mysql.connector
import sys

hostName = 'localhost'
username = 'root'
password = 'Sin_shadow1'


"""Allows for SQL to be written 'easily' in python"""
class SQL_Framework():
    
    def __init__(self):
        global hostName, username, password
        self.host = hostName
        self.user = username
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

from tkinter import (Tk, BOTH, Text, E, W, S, N, END, NORMAL, DISABLED, StringVar)
from tkinter.ttk import Frame, Label, Button, Progressbar, Entry
from tkinter import scrolledtext
import multiprocessing
from multiprocessing import Process, Manager, Queue
from queue import Empty

DELAY1 = 80
DELAY2 = 20

q = Queue()

class Example(Frame):
  
    def __init__(self, parent):
        Frame.__init__(self, parent, name="frame")   
        self.parent = parent
        self.initUI()                
        
    def initUI(self):
      
        self.parent.title("PDR Scrape")
        self.pack(fill=BOTH, expand=True)
        
        self.grid_columnconfigure(4, weight=1)
        self.grid_rowconfigure(3, weight=1)
        self.txt = scrolledtext.ScrolledText(self)  
        self.txt.grid(row=3, column=0, rowspan=4, padx=10, pady=10,
            columnspan=5, sticky=E+W+S+N)
        self.txt.insert('end',
            "-Instructions-\n\nPlease input your host name, username, and password, then click submit to allow for database access\n\nStart - Constructs database pdr_db with tables drug_index and drug_interactions (if not already constructed), then begins scraping PDR.net for drug interactions. This process will likely take several hours to complete, and will continue until it has finished or the Stop button is pressed.\n\nStop - terminates scraping of PDR.net. Please note that pressing start, then stop, then start again, will restart scraping process.\n\nQuery - allows for database queries specific to pdr_db, ie SELECT * FROM drug_index"
            )
        self.scrapeBtn = Button(self, text="Start", command=self.onScrape, width=10)
        self.scrapeBtn.grid(row=0, column=0, padx=10, pady=5, sticky=W)
        
        self.stopBtn = Button(self, text="Stop", command=self.onStop, width=10)
        self.stopBtn.grid(row=0, column=1, padx=5, pady=5, sticky=W)
        
        self.queryBtn = Button(self, text="Query", command =self.onQuery, width=10)
        self.queryBtn.grid(row=1, column=0, padx=10, pady=5, sticky=W)
        
        self.enterQuery = Entry(self, width=45)
        self.enterQuery.grid(row=1, column=1, sticky=W, padx=5, pady=5, columnspan=5)
        
        
        self.enterHost = Entry(self, width=10)
        self.enterHost.grid(row=2, column=0, sticky=W, padx=10, pady=5)
        self.enterHost.insert('end','hostname')
        
        self.enterUser = Entry(self, width=10)
        self.enterUser.grid(row=2, column=1, sticky=W, padx=5, pady=5)
        self.enterUser.insert('end','username')
        
        self.enterPass = Entry(self, width=10)
        self.enterPass.grid(row=2, column=2, sticky=W, padx=10, pady=5)
        self.enterPass.insert('end','password')
        
        self.submitBtn = Button(self, text="Submit", command = self.onSubmit, width=10)
        self.submitBtn.grid(row=2, column=3, padx=10, pady=5, sticky=W)
        
    def onSubmit(self):
        global hostName, username, password
        hostName = self.enterHost.get()
        username = self.enterUser.get()
        password = self.enterPass.get()

    def onQuery(self):
        self.sql = SQL_Framework()
        returnList = self.sql.tc('pdr_db', self.enterQuery.get())
        returnString = ''
        for i in returnList:
            returnString+=str(i)
            returnString+='\n\n'
        self.txt.insert('end',returnString)
        
        
    def onScrape(self):
        
        self.scrapeBtn.config(state=DISABLED)
        self.txt.delete("1.0", END)
        self.p1 = Process(target=PDR_Scrape)
        self.p1.start()
    
    def onStop(self):
        self.p1.kill()
        self.scrapeBtn.config(state=NORMAL)
                
def PDR_Scrape():
    home = 'https://www.pdr.net/browse-by-drug-name?letter='
    cmd = PDR_DB_Commander()
    cmd.makeDB()
    cmd.makeDrugIndexTable()
    cmd.makeDrugInteractionsTable()
    page = requests.get(home)
    soup = BeautifulSoup(page.content, 'html.parser')
    navLinks = []
    #Requests and parses pdr.net 'Browse by Drug Name' landing page.
    for link in soup.find_all('a', href=True):
        #Cleans non-navigational links. 
        if 'browse-by-drug-name?' in link.get('href') and link.get('href')[-1].isalpha():
            #Fills navLinks with links to alphabetical landing pages.  
            navLinks.append(link.get('href'))
            
    for i in navLinks:
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
                    cmd.insertToDrugIndex(name, chem, link) 
                except:
                    if len(cmd.sql.tc('pdr_db', 'SELECT * FROM drug_index WHERE brand_name = "' + name +'"')) > 0:
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
                                iDescription = z.rsplit('.', 1)[0]
                                iStrength = iDescription.split(' ', 1)[0][:-1]
                                iDescription = iDescription.split(' ', 1)[1].replace("\"","'")
                                # print("INSERT INTO drug_interactions VALUES ('"+name+"','"+iName+"','"+iDescription+"')")
                            except Exception as e: 
                                print(e)
                                print("\n",name,"\n",y,"\n",z,"\n")
                            
                            try:
                                cmd.insertToDrugInteractions(name, iName, iStrength, iDescription)
                            except:
                                if len(cmd.sql.tc('pdr_db', 'SELECT * FROM drug_interactions WHERE brand_name = "' + name +'" AND interaction_name = "' + iName + '"')) > 0:
                                    pass
                                else:
                                    print("something has gone wrong inserting \n\"{}\", \n\"{}\", \n\"{}\", \n\"{}\" \nto drug_interactions table".format(name, iName, iStrength, iDescription))
                                    pass
        increment = 1 #Resets sub-page count.
        # break # this break statement stops the program from running through more than the first letter of results  



def main():
    multiprocessing.freeze_support()
    root = Tk()
    root.geometry("400x350+300+300")
    app = Example(root)
    root.mainloop()  



if __name__ == '__main__':
    main()  
    