from tkinter import *
from tkinter import messagebox
from tkinter import ttk
from flask import Flask
from flask_bcrypt import Bcrypt, bcrypt
import sqlite3
import os
import datetime
import requests
import json
app = Flask(__name__)
bcrypt = Bcrypt(app)
class Personal:
    def __init__(self, name, accountNumber,  amount, loanAmount, password):
        self.name = name
        self.accountNumber = accountNumber
        self.password = password
        self.amount = amount
        self.loanAmount = loanAmount
    def hash_password(self):
        return (bcrypt.generate_password_hash(self.password).decode('utf-8'))
    def createAccount(self, tableName, database):
        conn = sqlite3.connect(f'{database}')
        c = conn.cursor()
        c.execute(f"SELECT * FROM {tableName}")
        d = len(c.fetchall())+1
        c.execute(f"INSERT INTO {tableName} VALUES(:rowid, :name, :accountNo, :amount, :loanAmount, :password_hash)",
            {
                'rowid': int(d),
                'name': str(self.name),
                'accountNo': str(self.accountNumber),
                'amount': int(self.amount),
                'loanAmount': int(self.loanAmount),
                'password_hash': str(self.hash_password()),
            })
        conn.commit()
        conn.close()
    def deposit(self, depositamount):
        if not(depositamount.isdigit()) or int(depositamount) <=0:
            return f"Error! Invalid deposit amount. The deposit amount should be more than 1"
        else:
            self.amount = int(self.amount)
            self.amount+=int(depositamount)
            conn = sqlite3.connect("/home/naikram/Desktop/VS/bank/Bank.db")
            c = conn.cursor()
            c.execute(f'UPDATE user SET amount=\'{str(self.amount)}\' WHERE accountNo=\'{str(self.accountNumber)}\'')

            conn.commit()
            conn.close()
            return f'You have successfully deposited {depositamount} Your account balance is {self.amount}'
    def withdraw(self, withdrawalAmount):
        self.amount = int(self.amount)
        if not(withdrawalAmount.isdigit()) or int(withdrawalAmount) <=0:
            return f"Error! Invalid withdrawal amount. The withdrawal amount should be more than 1"
        if self.amount<int(withdrawalAmount):
            return f'Withdrawal Unsuccessful. Your account balance is insufficient'
        else:
            self.amount-= int(withdrawalAmount)
            conn = sqlite3.connect("/home/naikram/Desktop/VS/bank/Bank.db")
            c = conn.cursor()
            c.execute(f'UPDATE user SET amount=\'{str(self.amount)}\' WHERE accountNo=\'{str(self.accountNumber)}\'')

            conn.commit()
            conn.close()
            return f'Withdrawal of {withdrawalAmount} Ksh was Successful'
    def checkBalance(self):
        conn = sqlite3.connect("/home/naikram/Desktop/VS/bank/Bank.db")
        c = conn.cursor()
        c.execute(f'SELECT * FROM user WHERE accountNo=\'{str(self.accountNumber)}\'')
        data = c.fetchall()
        conn.commit()
        conn.close()
        return data[0][3]
    def transferFunds(self, receiverID, transferAmount):
        if receiverID == self.accountNumber:
            return f'Please note that you cannot transfer funds to your own account'
        if not(transferAmount.isdigit()) or int(transferAmount) <=0:
            return f"Error! Invalid transfer amount. The transfer amount should be more than 1"
        if int(self.amount) < int(transferAmount):
            return f'Your Account balance is insufficient'   
        if int(self.amount) >= int(transferAmount):
            #getting the receiverID info
            conn = sqlite3.connect("/home/naikram/Desktop/VS/bank/Bank.db")
            c = conn.cursor()
            c.execute(f'SELECT * FROM user WHERE accountNo=\'{receiverID}\'')
            d = c.fetchall()
            if len(d)==0:
                return "The Receipient's ID is invalid, please provide a valid ID"
            else:
                d = d[0]
                receiver = Personal(d[1], d[2], d[3], d[4], d[5]) #creating an instance of the receiver
                self.amount = int(self.amount) #converting the amount to int

                self.amount-=int(transferAmount)
                c.execute(f'UPDATE user SET amount=\'{str(self.amount)}\' WHERE accountNo=\'{str(self.accountNumber)}\'')
                c.execute(f'UPDATE user SET amount=\'{str(int(receiver.amount)+int(transferAmount))}\' WHERE accountNo=\'{str(receiver.accountNumber)}\'')
                conn.commit()
                conn.close()
            return f"Transaction is Successful. You have transferred {transferAmount} Ksh to {receiver.name}  {receiver.accountNumber}"
        else:
            return f'An error occurred'

class Loans(Personal):
    def checkLimit(self):
        self.amount = int(self.amount)
        if self.amount < 2000:
            self.loanLimit = 0
        elif self.amount > 2000 and self.amount < 5000:
            self.loanLimit = 3000
        elif self.amount > 5000 and self.amount < 10000:
            self.loanLimit = 7500
        elif self.amount > 10000 and self.amount < 20000:
            self.loanLimit = 17000
        elif self.amount > 20000 and self.amount < 50000:
            self.loanLimit = 35000
        else:
            self.loanLimit = 60000
        self.amount = str(self.amount)
        return str(self.loanLimit)
    def takeLoan(self, requestLoan):
        if not(requestLoan.isdigit()) or int(requestLoan)<=0:
            return " invalid Request Amount"
        if int(self.loanAmount) > 0:
            return "Sorry! You have an outstanding Loan"
        if int(requestLoan)>int(self.loanLimit):
            return "Please request a loan within your loan limit"
        else:
            self.loanAmount = requestLoan
            self.amount = int(self.amount)+int(self.loanAmount)
            conn = sqlite3.connect("Bank.db")
            c = conn.cursor()
            c.execute(f'UPDATE user SET amount=\'{str(int(self.amount))}\' WHERE accountNo=\'{str(self.accountNumber)}\'')
            c.execute(f'UPDATE user SET loanAmount=\'{str(self.loanAmount)}\' WHERE accountNo=\'{str(self.accountNumber)}\'')

            conn.commit()
            conn.close()
            return f"Loan request is successful. Your outstanding loan is {self.loanAmount}"
    def repayLoan(self, returnAmount):
        if not(returnAmount.isdigit()) or int(returnAmount)<=0:
            return " Invalid Return Amount"
        if int(self.loanAmount) < 1:
            return "You have no outstanding loan amount"
        if int(self.amount)<int(returnAmount):
            return "You have insufficient balance in your account to repay the loan"
        else:
            if int(returnAmount) > int(self.loanAmount):
                self.amount = int(self.amount)-int(self.loanAmount)
                self.loanAmount = 0 
            else:
                self.amount = int(self.amount)-int(returnAmount) 
                self.loanAmount = int(self.loanAmount)-int(returnAmount)
            conn = sqlite3.connect("/home/naikram/Desktop/VS/bank/Bank.db") #creating a connectio to the database
            c = conn.cursor()
            c.execute(f'UPDATE user SET amount=\'{str(int(self.amount))}\' WHERE accountNo=\'{str(self.accountNumber)}\'')
            c.execute(f'UPDATE user SET loanAmount=\'{str(self.loanAmount)}\' WHERE accountNo=\'{str(self.accountNumber)}\'')
            conn.commit() #updating the database
            conn.close() 
            return f"Repay was successful. Your loan balance is {self.loanAmount}"# feedback

    def checkLoanBalance(self):
        return self.loanAmount

class Atm(Personal):
    pass

def formatMoney(p):
    x = list(str(p))
    x.reverse()
    t=0
    while t < len(x):
        if (t+1)%4==0:
            x.insert(t, ',')
        t=t+1
    x.reverse()
    p=''
    for c in range(len(x)):
        p+=x[c]
    return p

# creating the window object
root = Tk()
root.geometry('600x400')
root.title('G7 BANK')
root.resizable(False, False)
title_label = Label(root, text='G7 BANK MANAGEMENT SYSTEM', bg='#212121', fg='#40ff00', font=('Helvetica', 22, "bold"), anchor='center')
title_label.grid(column=0, row=0, columnspan=2, pady=50)

# creating the bank database
conn = sqlite3.connect("/home/naikram/Desktop/VS/bank/Bank.db")
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS user(name TEXT, accountNo TEXT, amount TEXT, loanAmount TEXT, password_hash TEXT)')

conn.commit()
conn.close()

# creating the functions

def creatAccountWindow():
    window=Tk()
    window.title('CREATE ACCOUNT')
    window.geometry('670x400')
    window.resizable(False, False)

    entry_width = 35

    fnameLabel = Label(window, text='First Name: ', font=('Helvetica', 17), bg='#212121', fg='white')
    fnameLabel.grid(column=0, row=0, padx=10, pady=10)
    fnameEntry = Entry(window, font=('Helvetica', 17), width=entry_width)
    fnameEntry.grid(column=1, row=0, padx=10, pady=10)

    lnameLabel = Label(window, text='Last Name: ', font=('Helvetica', 17), bg='#212121', fg='white')
    lnameLabel.grid(column=0, row=1, padx=10, pady=10)
    lnameEntry = Entry(window, font=('Helvetica', 17), width=entry_width)
    lnameEntry.grid(column=1, row=1, padx=10, pady=10)

    passLabel = Label(window, text='Password: ', font=('Helvetica', 17), bg='#212121', fg='white')
    passLabel.grid(column=0, row=2, padx=10, pady=10)
    passEntry = Entry(window, font=('Helvetica', 17), width=entry_width, show='*')
    passEntry.grid(column=1, row=2, padx=10, pady=10)

    def submit():
        accountNumber = os.urandom(6).hex()
        newPersonalUser = Personal(f'{fnameEntry.get()} {lnameEntry.get()}', accountNumber, 0, 0, passEntry.get())
        newPersonalUser.createAccount('user', '/home/naikram/Desktop/VS/bank/Bank.db')
        successLabel = Label(window, text='Account Created Successfully:)\n', bg='#212121', fg='white')
        successLabel.grid(column=1, row=4)
        detailsLabel = Label(window, text=f'Acccount Number:\t{accountNumber}\n Name:\t{newPersonalUser.name}', bg='#212121', fg='white')
        detailsLabel.grid(row=5, column=1)
    btnCancel = Button(window, text='Cancel', width=18, bg='orange', font=('Helvetica', 12))
    btnCancel.grid(column=0, row=3)

    btnSubmit = Button(window, text='Create Account', bg='#483D8B', width=47, font=('Helvetica', 12), command=submit)
    btnSubmit.grid(column=1, row=3, padx=2, pady=10)

    window.config(bg='#212121')
    window.mainloop()

def forex():
    try:
        currency_list = ["AED United Arab Emirates Dirham","AFN Afghan Afghani","ALL Albanian Lek", "AMD Armenian Dram", "ANG Netherlands Antillean Guilder", "AOA Angolan Kwanza", "ARS Argentine Peso", "AUD Australian Dollar", 
                "AWG Aruban Florin", "AZN Azerbaijani Manat", "BAM Bosnia-Herzegovina Convertible Mark", "BBD Barbadian Dollar", "BDT Bangladeshi Taka", "BGN Bulgarian Lev", "BHD Bahraini Dinar", 
                "BIF Burundian Franc","BMD Bermudan DollBank.dbar","BND Brunei Dollar", "BOB Bolivian Boliviano", "BRL Brazilian Real",
                "BSD Bahamian Dollar","BTN Bhutanese Ngultrum","BWP Botswanan Pula","BZD Belize Dollar","CAD Canadian Dollar","CDF Congolese Franc",
                "CHF Swiss Franc""CLF Chilean Unit of Account UF","CLP Chilean Peso","CNH Chinese Yuan Offshore","CNY Chinese Yuan","CLP Colombian Peso","CUP Cuban Peso","CVE Cape Verdean Escudo",
                "CZK Czech Republic Koruna","DJF Djiboutian Franc","DKK Danish Krone","DOP Dominican Peso","DZD Algerian Dinar","EGP Egyptian Pound",
                "ERN Eritrean Nakfa","ETB Ethiopian Birr","EUR Euro","FJD Fijian Dollar","FKP Falkland Islands Pound","GBP British Pound Sterling""GEL Georgian Lari","GHS Ghanaian Cedi","GIP Gibraltar Pound","GMD Gambian Dalasi","GNF Guinean Franc","GTQ Guatemalan Quetzal",
                "GYD Guyanaese Dollar","HKD Hong Kong Dollar","HNL Honduran Lempira","HRK Croatian Kuna","HTG Haitian Gourde","HUF Hungarian Forint","IDR Indonesian Rupiah""ILS Israeli New Sheqel","INR Indian Rupee","IQD Iraqi Dinar",
                "IRR Iranian Rial","ISK Icelandic Krona","JEP Jersey Pound","JMD Jamaican Dollar","JOD Jordanian Dinar","JPY Japanese Yen","KES Kenyan Shilling","KGS Kyrgystani Som","KHR Cambodian Riel","KMF Comorian Franc",
                "KPW North Korean Won","KRW South Korean Won","KWD Kuwaiti Dinar","KYD Cayman Islands Dollar","KZT Kazakhstani Tenge","LAK Laotian Kip","LBP Lebanese Pound","LKR Sri Lankan Rupee",
                "LRD Liberian Dollar","LSL Lesotho Loti","LYD Libyan Dinar","MAD Moroccan Dirham","MDL Moldovan Leu","MGA Malagasy Ariary","MKD Macedonian Denar","MMK Myanma Kyat","MNT Mongolian Tugrik",
                "MOP Macanese Pataca","MRO Mauritanian Ouguiya (pre-2018)","MRU Mauritanian Ouguiya","MUR Mauritian Rupee","MVR Maldivian Rufiyaa","MWK Malawian Kwacha","MXN Mexican Peso","MYR Malaysian Ringgit","MZN Mozambican Metical","NAD Namibian Dollar"
                "NGN Nigerian Naira","NOK Norwegian Krone","NPR Nepalese Rupee","NZD New Zealand Dollar","OMR Omani Rial","PAB Panamanian Balboa",
                "PEN Peruvian Nuevo Sol","PGK Papua New Guinean Kina","PHP Philippine Peso","PKR Pakistani Rupee","PLN Polish Zloty","PYG Paraguayan Guarani",
                "QAR Qatari Rial","RON Romanian Leu","RSD Serbian Dinar","RUB Russian Ruble","RUR Old Russian Ruble","RWF Rwandan Franc",
                "SAR Saudi Riyal","SBD Solomon Islands Dollar","SCR Seychellois Rupee","SDG Sudanese Pound","SDR Special Drawing Rights","SEK Swedish Krona",
                "SGD Singapore Dollar","SHP Saint Helena Pound","SLL Sierra Leonean Leone","SOS Somali Shilling","SRD Surinamese Dollar","SYP Syrian Pound","SZL Swazi Lilangeni",
                "THB Thai Baht","TJS Tajikistani Somoni","TMT Turkmenistani Manat","TND Tunisian Dinar","TOP Tongan Pa'anga","TRY Turkish Lira",
                "TTD Trinidad and Tobago Dollar","TWD New Taiwan Dollar","TZS Tanzanian Shilling","UAH Ukrainian Hryvnia","UGX Ugandan Shilling","USD United States Dollar",
                "UYU Uruguayan Peso","UZS Uzbekistan Som","VND Vietnamese Dong","VUV Vanuatu Vatu","WST Samoan Tala","XAF CFA Franc BEAC","XCD East Caribbean Dollar","XDR Special Drawing Rights",
                "XOF CFA Franc BCEAO","XPF Franc","YER Yemeni Rial","ZAR South African Rand","ZMW Zambian Kwacha","ZWL Zimbabwean Dollar"]
        # print(currency_list)
        # print(currency_rate)
        window = Tk() 
        window.title('G7 FOREX')
        window.geometry('670x400')
        title_label = Label(window, text='G7 REAL TIME FOREX RATES', font=('Helvetica', 17), fg='#40ff00', bg='#212121')
        title_label.grid(row=0, column=0, columnspan=2, pady=20, padx=10)
        combo1 = ttk.Combobox(window, value=currency_list, width=21, font=('Helvetica', 17))
        combo1.grid(column=0, row=1, padx=20, pady=20)
        entry1 = Entry(window, width=15, font=('Helvetica', 17))
        entry1.grid(column=1, row=1, padx=20, pady=20)
        combo2 = ttk.Combobox(window, value=currency_list, width=21, font=('Helvetica', 17))
        combo2.grid(column=0, row=2, padx=20, pady=20)
        entry2 = Entry(window, width=15, font=('Helvetica', 17))
        entry2.grid(column=1, row=2, padx=20, pady=20)
        time_label = Label(window, text='', bg='#212121', fg='red', font=('Helvetica', 10))
        time_label.grid(row=3, column=0, columnspan=2, padx=20, pady=20)
        def convert():
            if not (entry1.get().isdigit()):
                messagebox.showerror(title='Error!', message='Invalid Entry. Please Enter a numerical value', parent=window)
            else:
                amount = entry1.get()
                amount = float(amount)
                from_c = combo1.get()[0:3]
                to_c = combo2.get()[0:3]
                API_KEY= "61N7X1H7ILJI7SDI"
                url = 'https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={}&to_currency={}&apikey={}'.format(
                    from_c, to_c, API_KEY)
                response = requests.get(url=url).json()
                rate = response['Realtime Currency Exchange Rate']['5. Exchange Rate']
                rate = float(rate)
                result = rate * amount
                time = response['Realtime Currency Exchange Rate']['6. Last Refreshed']
                time_label.config(text=f'Last Update: {time} UTC')
                entry2.delete(0, END)
                entry2.insert(END, result)

        convertButton = Button(window, text='CONVERT', font=('Helvetica', 15), width=25, bg='#483D8B', command=convert)
        convertButton.grid(column=0, row=4, columnspan=2)
        window.config(background='#212121')
        window.mainloop()
    except:
        messagebox.showerror(title='Error!', message='Check Your Internet connection')

def personal():
    window=Tk()
    window.title('LOGIN')
    window.geometry('670x400')
    window.resizable(False, False)

    entry_width = 35

    fnameLabel = Label(window, text='First Name: ', font=('Helvetica', 17), bg='#212121', fg='white')
    fnameLabel.grid(column=0, row=0, padx=10, pady=10)
    fnameEntry = Entry(window, font=('Helvetica', 17), width=entry_width)
    fnameEntry.grid(column=1, row=0, padx=10, pady=10)

    lnameLabel = Label(window, text='Last Name: ', font=('Helvetica', 17), bg='#212121', fg='white')
    lnameLabel.grid(column=0, row=1, padx=10, pady=10)
    lnameEntry = Entry(window, font=('Helvetica', 17), width=entry_width)
    lnameEntry.grid(column=1, row=1, padx=10, pady=10)

    accLabel = Label(window, text='Acount No', font=('Helvetica', 17), bg='#212121', fg='white')
    accLabel.grid(column=0, row=2, padx=10, pady=10)
    accEntry = Entry(window, font=('Helvetica', 17), width=entry_width)
    accEntry.grid(column=1, row=2, padx=10, pady=10)

    passLabel = Label(window, text='Password: ', font=('Helvetica', 17), bg='#212121', fg='white')
    passLabel.grid(column=0, row=3, padx=10, pady=10)
    passEntry = Entry(window, font=('Helvetica', 17), width=entry_width, show='*')
    passEntry.grid(column=1, row=3, padx=10, pady=10)

    def check_password_correction(hash, attempted_password): #unhashing the passwords to be used during login
        return bcrypt.check_password_hash(hash, attempted_password)  #returns true or false

    def validate():
        login = False
        conn = sqlite3.connect("/home/naikram/Desktop/VS/bank/Bank.db")
        c = conn.cursor()
        c.execute(f'SELECT * FROM user WHERE name=\'{fnameEntry.get()} {lnameEntry.get()}\' AND accountNo=\'{accEntry.get()}\'')
        data = c.fetchall()
        if len(data)==0:
            messagebox.showerror(title='Invalid Login', message='Invalid login details', parent=window)
        else:
            if check_password_correction(data[0][5], passEntry.get()):
                login = True
            else:
                messagebox.showerror(title='Invalid Login', message='Invalid Password', parent=window)
        
        if login:
            c.execute(f'SELECT * FROM user WHERE accountNo=\'{accEntry.get()}\'')
            d = c.fetchall()
            d = d[0]
            conn.commit()
            conn.close()
            window.destroy()
            
            top = Tk()
            top.title('THE G7 BANK')
            top.geometry('950x400')
            top.resizable(False, False)

            accountNameLabel = Label(top, text=f'Account Name:', font=('Helvetica', 14), bg='#212121', fg='#483D8B')
            accountNameLabel.grid(column=0, row=0, padx=2, pady=10)
            account = Label(top, text=f'{d[1]}', font=('Helvetica', 17), bg='#212121', fg='#40ff00')
            account.grid(column=1, row=0, padx=2, pady=20)

            accountNoLabel = Label(top, text=f'Account ID:', font=('Helvetica', 14), bg='#212121', fg='#483D8B')
            accountNoLabel.grid(column=2, row=0, padx=2, pady=10)
            accountNoLabel1 = Label(top, text=f'{d[2]}', font=('Helvetica', 14), bg='#212121', fg='#40ff00')
            accountNoLabel1.grid(column=3, row=0, padx=2, pady=10)

            balancelabel = Label(top, text=f'Account Balance:', font=('Helvetica', 14), bg='#212121', fg='#483D8B')
            balancelabel.grid(column=0, row=1, padx=2, pady=10)
            balancelabel1 = Label(top, text=f'{formatMoney(d[3])}', font=('Helvetica', 14), bg='#212121', fg='#40ff00')
            balancelabel1.grid(column=1, row=1, padx=2, pady=10)

            dateLabel = Label(top, text='Date:', font=('Helvetica', 14), bg='#212121', fg='#483D8B')
            dateLabel.grid(column=2, row=1, padx=2, pady=10)
            dateLabel1 = Label(top, text=f'{datetime.datetime.now().strftime("%A")} {datetime.datetime.now().date()}', font=('Helvetica', 14), bg='#212121', fg='#40ff00')
            dateLabel1.grid(column=3, row=1, padx=2, pady=10)


            w = 20

            currentUser = Personal(d[1], d[2], d[3], d[4], d[5])

            def deposit():
                info = currentUser.deposit(depositEntry.get())
                balancelabel1.config(text=formatMoney(str(currentUser.amount)))
                depositEntry.delete(0, END)
                messagebox.showinfo(title='Success', message=info, parent=top)
            
            def withdraw():
                info = currentUser.withdraw(withdrawEntry.get())
                balancelabel1.config(text=formatMoney(str(currentUser.amount)))
                withdrawEntry.delete(0, END)
                messagebox.showinfo(title='Feedback', message=info, parent=top)
            def transfer():
                info = currentUser.transferFunds(receipientEntry.get(), transferEntry.get())
                balancelabel1.config(text=formatMoney(str(currentUser.amount)))
                transferEntry.delete(0, END)
                messagebox.showinfo(title='Feedback', message=info, parent=top)
            
            def loans():
                currentUser = Loans(d[1], d[2], d[3], d[4], d[5])
                loansWindow = Tk()
                loansWindow.title('G7 BANK My loans')
                loansWindow.geometry('950x400')
                loansWindow.resizable(False, False)

                accntNameLabel = Label(loansWindow, text=f'Account Name:', font=('Helvetica', 14), bg='#212121', fg='#483D8B')
                accntNameLabel.grid(column=0, row=0, padx=2, pady=10)
                accnt = Label(loansWindow, text=f'{d[1]}', font=('Helvetica', 17), bg='#212121', fg='#40ff00')
                accnt.grid(column=1, row=0, padx=2, pady=20)

                accntNoLabel = Label(loansWindow, text=f'Account ID:', font=('Helvetica', 14), bg='#212121', fg='#483D8B')
                accntNoLabel.grid(column=2, row=0, padx=2, pady=10)
                accntNoLabel1 = Label(loansWindow, text=f'{d[2]}', font=('Helvetica', 14), bg='#212121', fg='#40ff00')
                accntNoLabel1.grid(column=3, row=0, padx=2, pady=10)

                loanlabel = Label(loansWindow, text=f'Account Balance:', font=('Helvetica', 14), bg='#212121', fg='#483D8B')
                loanlabel.grid(column=0, row=1, padx=2, pady=10)
                loanlabel1 = Label(loansWindow, text=formatMoney(d[4]), font=('Helvetica', 14), bg='#212121', fg='#40ff00')
                loanlabel1.grid(column=1, row=1, padx=2, pady=10)

                limitLabel = Label(loansWindow, text='Loan Limit:', font=('Helvetica', 14), bg='#212121', fg='#483D8B')
                limitLabel.grid(column=2, row=1, padx=2, pady=10)
                limitLabel1 = Label(loansWindow, text=f'{formatMoney(currentUser.checkLimit())}', font=('Helvetica', 14), bg='#212121', fg='#40ff00')
                limitLabel1.grid(column=3, row=1, padx=2, pady=10)

                def takeLoan():
                    info = currentUser.takeLoan(takeLoanEntry.get())
                    loanlabel1.config(text=formatMoney(currentUser.loanAmount))
                    balancelabel1.config(text=formatMoney(currentUser.amount))
                    messagebox.showinfo(title='Feedback', message=info, parent=loansWindow)
                
                def repayLoan():
                    info = currentUser.repayLoan(repayEntry.get())
                    loanlabel1.config(text=formatMoney(currentUser.loanAmount))
                    balancelabel1.config(text=formatMoney(currentUser.amount))
                    messagebox.showinfo(title='Feedback', message=info, parent=loansWindow)

                btntakeLoan = Button(loansWindow, text='Take Loan', font=('Helvetica', 17), bg='#483D8B', fg='#40ff00', width=w, command=takeLoan)
                btntakeLoan.grid(row=2, column=0, padx=10, pady=10)
                takeLoanEntry = Entry(loansWindow, font=('Helvetica', 17), width=w-5)
                takeLoanEntry.grid(column=1, row=2)
                takeLoanEntry.insert(0, "Request Amount")

                btnRepay = Button(loansWindow, text='Repay Loan', font=('Helvetica', 17), bg='#483D8B', fg='#40ff00', width=w, command=repayLoan)
                btnRepay.grid(row=3, column=0, padx=10, pady=10)
                repayEntry = Entry(loansWindow, font=('Helvetica', 17), width=w-5)
                repayEntry.grid(row=3, column=1)
                repayEntry.insert(0, 'Repay ')

                loansWindow.config(bg='#212121')
                loansWindow.mainloop()

            btnDeposit = Button(top, text='Deposit', font=('Helvetica', 17), bg='#483D8B', fg='#40ff00', width=w, command=deposit)
            btnDeposit.grid(row=2, column=0, padx=10, pady=10)
            depositEntry = Entry(top, font=('Helvetica', 17), width=w-5)
            depositEntry.grid(row=2, column=1, padx=10, pady=10)
            depositEntry.insert(0, 'Deposit Amount')

            btnWithdraw = Button(top, text='Withdraw', font=('Helvetica', 17), bg='#483D8B', fg='#40ff00', width=w, command=withdraw)
            btnWithdraw.grid(row=3, column=0, padx=10, pady=10)
            withdrawEntry = Entry(top, font=('Helvetica', 17), width=w-5)
            withdrawEntry.grid(row=3, column=1, padx=10, pady=10)
            withdrawEntry.insert(0, 'Withdrawal Amount')

            btnTransfer = Button(top, text='Transfer', font=('Helvetica', 17), bg='#483D8B', fg='#40ff00', width=w, command=transfer)
            btnTransfer.grid(row=4, column=0, padx=10, pady=10)
            transferEntry = Entry(top, font=('Helvetica', 17), width=w-5)
            transferEntry.grid(row=4, column=1, padx=10, pady=10)
            transferEntry.insert(0, 'Transfer Amount')
            receipientEntry = Entry(top, font=('Helvetica', 17), width=w-5)
            receipientEntry.grid(row=4, column=2, padx=10, pady=10)
            receipientEntry.insert(0, 'Account Number')

            btnLoan = Button(top, text='My Loans', font=('Helvetica', 17), bg='#483D8B', fg='#40ff00', width=w, command=loans)
            btnLoan.grid(row=5, column=0, padx=10, pady=10)

            top.config(bg='#212121')
            top.mainloop()

    btnCancel = Button(window, text='Cancel', width=18, bg='orange', font=('Helvetica', 12), command=window.destroy)
    btnCancel.grid(column=0, row=4)

    btnLogin = Button(window, text='Login', bg='#483D8B', width=47, font=('Helvetica', 12), command=validate)
    btnLogin.grid(column=1, row=4, padx=2, pady=10)

    window.config(bg='#212121')
    window.mainloop()

# creating the landing buttons
btnWidth=30
btnHeight=2
btnCreateAccount = Button(root, text='Create Account', bg='#483D8B', fg='white', width=btnWidth, height=btnHeight, command=creatAccountWindow)
btnCreateAccount.grid(column=0, row=1, padx=10)

btnForex = Button(root, text='FOREX', width=btnWidth, height=btnHeight, bg='#483D8B', fg='white', command=forex)
btnForex.grid(column=1, row=1, padx=10, pady=10)

btnPersonal = Button(root, text='Personal Account', width=btnWidth, height=btnHeight, bg='#483D8B', fg='white', command=personal)
btnPersonal.grid(column=0, row=2, padx=10, pady=50)

btnExit = Button(root, text='Exit', width=btnWidth, height=btnHeight, bg='#483D8B', fg='white', command=root.destroy)
btnExit.grid(column=1, row=2, padx=10, pady=50)

conn = sqlite3.connect("/home/naikram/Desktop/VS/bank/Bank.db")
c = conn.cursor()
c.execute('SELECT * FROM user')
data = c.fetchall()
conn.commit()
conn.close()

print(data)

root.config(bg='#212121')

root.mainloop()