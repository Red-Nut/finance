from django.shortcuts import render, redirect
from django.conf import settings

from finance.models import *
from finance.models import Account
from finance.models import Transaction

from bs4 import BeautifulSoup
import time
import datetime
from dateutil.relativedelta import relativedelta

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import Select
from finance.models import Transaction

import undetected_chromedriver.v2 as uc

# Create your views here.

# Index.
def NABTransactions(request):
    url = "https://ib.nab.com.au/nabib/index.jsp?browser=correct"

    # Firefox
    #driver = webdriver.Firefox()
    # Chrome
    #driver = webdriver.Chrome()
    
    # Undetected Chrome Driver
    driver = webdriver.Chrome()
    driver.implicitly_wait(1)
    driver.quit()
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-site-isolation-trials')
    #options.headless = True 
    driver = uc.Chrome(options=options)

    #Set full screen
    driver.set_window_position(0, 0)
    driver.set_window_size(1920, 1080)

    # Open URL
    #driver.implicitly_wait(1)
    time.sleep(2)
    driver.get(url)

    # Login
    driver.find_element_by_id("userid").send_keys(settings.NAB_USERNAME)
    driver.find_element_by_id("password").send_keys(settings.NAB_PASSWORD)
    driver.find_element_by_id("loginBtn").click()

    # Go to Transactions Page
    time.sleep(2)
    javaScript = "sendMenuRequest('/nabib/transactionHistorySelectAccount.ctl');"
    driver.execute_script(javaScript)

    # James Transaction Account
    account = Account.objects.get(id=1)
    processTransactions(driver, 0, account)

    # Long Term Savings
    account = Account.objects.get(id=2)
    processTransactions(driver, 2, account)

    # Joint Transaction Account
    account = Account.objects.get(id=3)
    processTransactions(driver, 3, account)

    # Short Term Savings
    account = Account.objects.get(id=4)
    processTransactions(driver, 4, account)
    
    

    

    # Home Page
    javaScript = "javascript:sendMenuRequest('/nabib/acctInfo_acctBal.ctl');"
    driver.execute_script(javaScript)

    driver.quit()

    return redirect("unallocated")

def processTransactions(driver, id, account):
    time.sleep(5)
    # Select Account
    try:
        driver.execute_script('''return document.querySelector('miniapp-transactions').shadowRoot.querySelector('#dropdown-toggle-button-accountsListDropdown').click()''')
    except:
        time.sleep(5)
        driver.execute_script('''return document.querySelector('miniapp-transactions').shadowRoot.querySelector('#dropdown-toggle-button-accountsListDropdown').click()''')
    
    time.sleep(0.5)
    driver.execute_script('''return document.querySelector('miniapp-transactions').shadowRoot.querySelector('#dropdown-listbox-accountsListDropdown-''' + str(id) + '''').click()''')
    
    # Select Last 7 days
    time.sleep(0.5)
    driver.execute_script('''return document.querySelector('miniapp-transactions').shadowRoot.querySelector('#dropdown-toggle-button-DateDropdown').click()''')
    time.sleep(0.5)
    driver.execute_script('''return document.querySelector('miniapp-transactions').shadowRoot.querySelector('#dropdown-listbox-DateDropdown-0').click()''')

    # Select Custom Date Range
    #driver.execute_script('''return document.querySelector('miniapp-transactions').shadowRoot.querySelector('#dropdown-toggle-button-DateDropdown').click()''')
    #time.sleep(1)
    #driver.execute_script('''return document.querySelector('miniapp-transactions').shadowRoot.querySelector('#dropdown-listbox-DateDropdown-2').click()''')
    #time.sleep(1)
    # Doesn't work because date values reset almost instantly.
    #driver.execute_script('''return document.querySelector('miniapp-transactions').shadowRoot.querySelector('#fromDate').value="01/05/2022"''')
    #driver.execute_script('''return document.querySelector('miniapp-transactions').shadowRoot.querySelector('#toDate').value="01/06/2022"''')
    #time.sleep(1)
    
    # Update Transactions Button
    time.sleep(0.5)
    driver.execute_script('''return document.querySelector('miniapp-transactions').shadowRoot.querySelector('button[class*="StyledSubmitButton"]').click()''')
 
    time.sleep(5)
    ScrollDown(driver)

    try:
        trs = driver.execute_script('''return document.querySelector('miniapp-transactions').shadowRoot'''
            '''.querySelector("tbody[class^='StyledTableBody']")'''
            '''.querySelectorAll("tr[class^='StyledTableRow']")'''
            )
    except:
        time.sleep(3)
        try:
            trs = driver.execute_script('''return document.querySelector('miniapp-transactions').shadowRoot'''
                '''.querySelector("tbody[class^='StyledTableBody']")'''
                '''.querySelectorAll("tr[class^='StyledTableRow']")'''
                )
        except:
            print("FAILED TO GET TABLE ROWS: " + account.name)
            return



    for t in range(len(trs)-1):
        time.sleep(5)
        ScrollDown(driver)
        try:
            trs = driver.execute_script('''return document.querySelector('miniapp-transactions').shadowRoot'''
                '''.querySelector("tbody[class^='StyledTableBody']")'''
                '''.querySelectorAll("tr[class^='StyledTableRow']")'''
                )
        except:
            time.sleep(3)
            try:
                trs = driver.execute_script('''return document.querySelector('miniapp-transactions').shadowRoot'''
                    '''.querySelector("tbody[class^='StyledTableBody']")'''
                    '''.querySelectorAll("tr[class^='StyledTableRow']")'''
                    )
            except:
                print("FAILED TO GET TABLE ROWS: " + account.name + ", for row " + str(t))
        
        time.sleep(0.5)
        try:
            tr=trs[t]
        except:
            print("**************** FAILED ****************")
            print("could not find row: " + str(t) + " in account " + account.name)
            break

        tr.click()
        time.sleep(3)

        shadowContent = driver.execute_script('''return document.querySelector('miniapp-transactions').shadowRoot.innerHTML''')
        soup=BeautifulSoup(shadowContent, 'lxml')

        merchant = None
        transactionType = None
        description = None
        value = None
        myDate = None

        # Value
        try:
            valueText = soup.find('b').text
            if(valueText[0] == '$'):
                value = valueText[1:]
        except:
            time.sleep(5)
            shadowContent = driver.execute_script('''return document.querySelector('miniapp-transactions').shadowRoot.innerHTML''')
            soup=BeautifulSoup(shadowContent, 'lxml')

            try:
                valueText = soup.find('b').text
                if(valueText[0] == '$'):
                    value = valueText[1:]
            except:
                print("**************** FAILED ****************")
                print("failed to get value: row " + str(t) + " in account " + account.name)
                print(" ")
                print("**************** SOUP PRINT ****************")
                print(soup)
                print(" ")

        for data in soup.find_all('dd'):
            
            #if hasattr(data, 'data-test-id'):
            # Description
            dataKey = data.get('data-test-id', None)
            if dataKey == 'narrative':
                description = data.text
            # Transaction Type
            if dataKey == 'description':
                transactionType = data.text
            # Mechant
            if dataKey == 'merchant-name':
                merchant = data.text

        # Date
        try:
            dateDiv = soup.find("div", {"id": "transaction-info-heading-date-time"})
            dateTexts = dateDiv.find_all('span')
            if(len(dateTexts) == 6):
                dateText = dateTexts[1].text.strip()
                firstSpace = dateText.find(" ")
                secondSpace = dateText.find(" ", 3)
                yearEnd1 = dateText.find("A E")
                yearEnd2 = dateText.find(" ", secondSpace+1)
                yearEnd = yearEnd1
                if yearEnd2 < yearEnd1 and yearEnd2 != -1:
                    yearEnd = yearEnd2
                myDate = None
                try:
                    if firstSpace is not None and secondSpace is not None and yearEnd is not None:
                        day = dateText[0:firstSpace]
                        month = dateText[firstSpace+1: secondSpace -3]
                        year = dateText[secondSpace+1: yearEnd]
                        myDate = datetime.datetime.strptime(day + " " + month + " " + year, '%d %B %Y').date()
                    else:
                        print("DATE CONVERSION FAILED")
                        print(dateText)
                except:
                    print("DATE CONVERSION FAILED")
                    print(dateText)
        except:
            print("DATE CONVERSION FAILED")
            print("failed to get date text: row " + str(t) + " in account " + account.name)

        if myDate is not None and description is not None and transactionType is not None and value is not None:
            dateFormatted = myDate.strftime('%Y-%m-%d')
            value = value.replace(',', '')
            transaction = None
                
            # Internal Transfer
            if transactionType == "Transfer Credit" and description.find("Linked Acc Trns") > -1:
                # Fix Description
                descriptionFormatted = description
                dStart = description.find("ONLINE")
                dEnd = description.find("Linked Acc Trns")

                if dStart > -1 and dEnd > -1:
                    descriptionFormatted = "Internal Transfer: " + description[dStart + 7 : dEnd]

                # Create Transaction Object
                transaction = Transaction(
                    date = dateFormatted,
                    name = descriptionFormatted,
                    type = Transaction.TRANSFER,
                    value = value,
                    paid_to = account
                )

            # Credits
            elif transactionType == "Transfer Credit" or transactionType == "Inter Bank Credit" or transactionType == "Interest Paid":
                # Fix Description
                descriptionFormatted = "Credit: " + description

                # Create Transaction Object
                transaction = Transaction(
                    date = dateFormatted,
                    name = descriptionFormatted,
                    type = Transaction.CREDIT,
                    value = value,
                    paid_to = account
                )

            # Debits
            elif transactionType=="Eftpos Debit" or transactionType=="Miscellaneous Debit" or transactionType=="Automatic Drawing" or transactionType=="Transfer Debit":
                # Fix Description
                descriptionFormatted = description
                if transactionType=="Eftpos Debit" or transactionType=="Miscellaneous Debit":
                    dStart = description.find(" ", 8)

                    if dStart > -1:
                        descriptionFormatted = "Debit: " + description[dStart + 1 : ]

                if transactionType=="Transfer Debit":
                    dStart = description.find("ONLINE")
                    dEnd = description.find("Linked Acc Trns")

                    if dStart > -1 and dEnd > -1:
                        descriptionFormatted = "Online Transfer: " + description[dStart + 7 : dEnd]

                # Create Transaction Object
                transaction = Transaction(
                    date = dateFormatted,
                    name = descriptionFormatted,
                    type = Transaction.DEBIT,
                    value = value,
                    paid_from = account,
                    merchant = merchant
                )

            else: 
                print("**************** FAILED ****************")
                print("failed to identify transaction type: " + transactionType + " (row "+ str(t) +")" + " in account " + account.name)

            if transaction is not None and not (myDate.month == 5 and myDate.year == 2022):
                # Income adjustment
                if transaction.name.find("CENTRAL ENERGY") > -1:
                    tDate = datetime.datetime.strptime(transaction.date, '%Y-%m-%d').date()
                    if tDate.day > 26:
                        tDate = tDate + relativedelta(months=1)
                        myDate = datetime.datetime.strptime("1 " + str(tDate.month) + " " + str(tDate.year), '%d %m %Y').date()
                        dateFormatted = myDate.strftime('%Y-%m-%d')
                        transaction.date = dateFormatted



                # Date adjustment (because the bank keeps changing the dates on the transactions causeing duplication)
                start = datetime.datetime.strptime(transaction.date, '%Y-%m-%d').date() - datetime.timedelta(days=5)
                end = datetime.datetime.strptime(transaction.date, '%Y-%m-%d').date()

                # Check if transaction already exists
                if transaction.type == Transaction.DEBIT:
                    check1 = Transaction.objects.filter(date__range=[start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")], value=transaction.value, type=transaction.type, paid_from=transaction.paid_from).first()
                else:
                    check1 = Transaction.objects.filter(date__range=[start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")], value=transaction.value, type=transaction.type, paid_to=transaction.paid_to).first()

                check2 = check1
                if transaction.type == Transaction.DEBIT:
                    check2 = Transaction.objects.filter(date__range=[start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")], value=transaction.value, type=Transaction.TRANSFER_DUPLICATE, paid_from=transaction.paid_from).first()
                
                check3 = check1
                if transaction.type == Transaction.CREDIT or transaction.type == Transaction.TRANSFER:
                    check3 = Transaction.objects.filter(date__range=[start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")], value=transaction.value, type=Transaction.TRANSFER, paid_to=transaction.paid_to).first()
                
                check4 = check1
                
                if check1 is None and check2 is None and check3 is None and check4 is None:
                    try:
                        transaction = AutomaticAllocation(transaction)
                        transaction.save(force_insert=True)
                        
                    except Exception as e:
                        print(e)
                        print("Failed to save transaction: " + str(transaction))
                else:
                    pass
                    #print("duplicate transaction: " + str(transaction))



        # Return to Transaction List
        driver.execute_script('''return document.querySelector('miniapp-transactions').shadowRoot.querySelector('button[data-test-id="backButton"]').click()''')
        
    return

def AutomaticAllocation(transaction):
    # Automatically assigns transaction allocations based on set parameters

    if transaction.type == Transaction.DEBIT:
        # Coles
        if transaction.name.find("Coles") > -1:
            allocation = Allocation.objects.filter(code="F1").first()
            transaction.allocation = allocation
            return transaction

        # Woolworths
        if transaction.name.find("Woolworths") > -1:
            allocation = Allocation.objects.filter(code="F1").first()
            transaction.allocation = allocation
            return transaction

        # Dinnerly
        if transaction.name.find("PAYPAL") > -1:
            if transaction.value == 74.99 or transaction.value == 80.39:
                allocation = Allocation.objects.filter(code="F1").first()
                transaction.allocation = allocation

                return transaction

        # Fruit and Veg
        if transaction.name.find("WYNNUM FRUIT BASKET") > -1 or transaction.name.find("PERRYS FRESH") > -1:
            allocation = Allocation.objects.filter(code="T1").first()
            transaction.allocation = allocation

            return transaction

        # Alcohol
        if transaction.name.find("Dan Murphy") > -1 or transaction.name.find("BWS") > -1:
            allocation = Allocation.objects.filter(code="F7").first()
            transaction.allocation = allocation

            return transaction

        # Fitness 4173 Coffee
        if transaction.name.find("Fitness 4173") > -1:
            allocation = Allocation.objects.filter(code="F6").first()
            transaction.allocation = allocation

            return transaction



        # Petrol
        if transaction.name.find("CNR GORDON AND ERNES") > -1 or transaction.name.find("BP (Manly)") > -1 or transaction.name.find("BP (Coopers Plains)") > -1:
            try:
                if float(transaction.value) > 30:
                    allocation = Allocation.objects.filter(code="T1").first()
                    transaction.allocation = allocation

                    return transaction
            except:
                pass

        # Tolls
        if transaction.name.find("LINKT ") > -1:
            allocation = Allocation.objects.filter(code="P2").first()
            transaction.allocation = allocation

            return transaction



        # Internet
        if transaction.name.find("TPG") > -1:
            allocation = Allocation.objects.filter(code="T6").first()
            transaction.allocation = allocation

            return transaction

        # Phone
        if transaction.name.find("PAYPAL") > -1:
            if transaction.value == 10 or transaction.value == 25:
                allocation = Allocation.objects.filter(code="P1").first()
                transaction.allocation = allocation

                return transaction

        # Netflix
        if transaction.name.find("PAYPAL") > -1:
            if transaction.value == 10.99:
                allocation = Allocation.objects.filter(code="P3").first()
                transaction.allocation = allocation

                return transaction

        # Spotify
        if transaction.name.find("PAYPAL") > -1:
            if transaction.value == 5.99:
                allocation = Allocation.objects.filter(code="P3").first()
                transaction.allocation = allocation

                return transaction

        # True Crime Obsessed
        if transaction.name.find("PAYPAL") > -1:
            try:
                if float(transaction.value) > 7 and float(transaction.value) < 8:
                    allocation = Allocation.objects.filter(code="P3").first()
                    transaction.allocation = allocation

                    return transaction
            except:
                pass

        
        # Gym
        if transaction.name.find("STUDIO PULSE") > -1:
            allocation = Allocation.objects.filter(code="R1").first()
            transaction.allocation = allocation

            return transaction

    return transaction
    
def ScrollDown(driver):
    driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
    time.sleep(0.1)
    driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
    time.sleep(0.1)
    driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
    time.sleep(0.1)
    driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
    time.sleep(0.1)
    driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
    time.sleep(0.1)
    driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
    time.sleep(0.1)
    driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
    time.sleep(0.1)
    driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
    time.sleep(0.1)
    driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
    time.sleep(0.1)
    driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
    time.sleep(0.1)
    driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
    time.sleep(0.1)
    driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
    time.sleep(0.1)
    driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
    time.sleep(0.1)
    driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
    time.sleep(0.1)
    driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
    time.sleep(0.1)
    driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
    time.sleep(0.1)
    driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
    time.sleep(0.1)
    driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
    time.sleep(0.1)
    driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
    time.sleep(0.1)

    return