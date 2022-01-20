import datetime
from flask import Flask, render_template, redirect, url_for, flash, request
import flask_login
from flask_wtf import FlaskForm
from flask_sqlalchemy import SQLAlchemy
from wtforms.fields.numeric import IntegerField
from wtforms.fields.simple import PasswordField, StringField, SubmitField
from wtforms.validators import Length, EqualTo, Email, DataRequired, ValidationError
from flask_bcrypt import Bcrypt, bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required
from flask_login import UserMixin #for login
import requests
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///Bank.db'
db = SQLAlchemy(app)
app.config['SECRET_KEY']='405ccfeb07e3f35cdc0e3f1a'
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login_page"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):#Creating the user database
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(length=30), nullable=False)
    accountNo = db.Column(db.String(length=10), nullable=False, unique=True)
    amount = db.Column(db.Integer(), nullable=False, default=0)
    loanAmount = db.Column(db.Integer(), nullable=False, default=0)
    password_hash = db.Column(db.String(length=60), nullable=False)

    # @property
    # def password(self):
    #     return self.password
    
    # @password.setter
    # def password(self, plain_text_password): #hashing passwords to be stored after registration and setting it as the password
    #     self.password_hash = bcrypt.generate_password_hash(plain_text_password).decode('utf-8')

    def check_password_correction(self, attempted_password): #unhashing the passwords to be used during login
        return bcrypt.check_password_hash(self.password_hash, attempted_password)  #returns true or false

    @property
    def checkLoanLimit(self):#checking the loan limits
        limit = 0
        if self.amount < 2000:
            limit = 0
        elif self.amount > 2000 and self.amount < 5000:
            limit = 3000
        elif self.amount > 5000 and self.amount < 10000:
            limit = 7500
        elif self.amount > 10000 and self.amount < 20000:
            limit = 17000
        elif self.amount > 20000 and self.amount < 50000:
            limit = 35000
        else:
            limit = 60000
        return limit
    
    @property
    def change_money(self): # this function is used to put the budget in money format
        x = list(str(self.amount))
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

    def __repr__(self):
        return f'User {self.name}'
    
class LoginForm(FlaskForm):#login form
    name = StringField(label='User Name', validators=[DataRequired()])
    accountNo = StringField(label='Account Number', validators=[DataRequired()])
    password = PasswordField(label='Password', validators=[DataRequired()])
    submit = SubmitField(label='Login')

class WithdrawForm(FlaskForm): #form used to withdraw
    amount = IntegerField(label='Amount', validators=[DataRequired()])
    submit1 = SubmitField(label='Withdraw')

class DepositForm(FlaskForm):
    amount = IntegerField(label='Amount', validators=[DataRequired()])
    submit2 = SubmitField(label='Deposit')

class TransferForm(FlaskForm):
    amount = IntegerField(label='Amount', validators=[DataRequired()])
    receiver = StringField(label='Receiver', validators=[DataRequired()])
    submit3=SubmitField(label='Send')

class BorrowLoan(FlaskForm):
    amount = IntegerField(label='Amount', validators=[DataRequired()])
    submit4 = SubmitField(label='Borrow')

class RepayLoan(FlaskForm):
    amount = IntegerField(label='Amount', validators=[DataRequired()])
    submit5 = SubmitField(label='Repay')

@app.route('/')
def home_page():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    form = LoginForm()
    if form.validate_on_submit():
        attempted_user = User.query.filter_by(accountNo=form.accountNo.data).first()
        if attempted_user and attempted_user.check_password_correction(attempted_password=form.password.data):
            login_user(attempted_user)
            flash('Successful Log in')
            return redirect(url_for('personal_page'))
        else:
            flash('Invalid Login details')
    return render_template('login.html', form=form)

@app.route('/personal', methods=['GET', 'POST'])
@login_required
def personal_page():
    time = str(datetime.datetime.now().strftime("%A")) + ' ' + str(datetime.datetime.now().date())
    withdrawForm = WithdrawForm()
    depositForm = DepositForm()
    transferForm = TransferForm()
    current_user = flask_login.current_user #getting the current user instance that is logged in
    if request.method == 'POST':
        if withdrawForm.submit1.data and withdrawForm.validate():
            if withdrawForm.amount.data>=1:
                if current_user.amount < withdrawForm.amount.data:
                    flash('Sorry, You have insufficient balance in your account')
                else:
                    current_user.amount-=withdrawForm.amount.data
                    flash(f'You have successfully withdrawn {withdrawForm.amount.data}')
            else:
                flash(f'The least amount you can withdraw is Ksh 1')

        if depositForm.submit2.data and depositForm.validate():
            if depositForm.amount.data >= 1:
                current_user.amount+=withdrawForm.amount.data
                flash(f'You have successfully deposited Ksh {depositForm.amount.data}')
            else:
                flash(f' ! Sorry The least amount you can deposit is Ksh 1!')

        if transferForm.submit3.data and transferForm.validate():
            if transferForm.amount.data >=1:
                if current_user.amount >= transferForm.amount.data:
                    receiver = User.query.filter_by(accountNo=transferForm.receiver.data).first()
                    if receiver:                    
                        receiver.amount+=transferForm.amount.data
                        current_user.amount-=transferForm.amount.data
                        flash(f'You have transferred {transferForm.amount.data} shillings to {receiver.name}')
                    else:
                        flash(' ! The Receiver ID does not exist.Please enter a valid ID')
                else:
                    flash(' ! You have insufficient money to make this transaction')
            else:
                flash(f' ! The least amount you can transfer is 1 shilling')
        db.session.commit()

        return redirect(url_for("personal_page"))

    return render_template('personal.html', withdrawForm=withdrawForm, depositForm=depositForm, transferForm=transferForm, time=time)

@app.route('/personal/loans', methods=['GET', 'POST'])
@login_required
def loans_page():
    borrowForm = BorrowLoan()
    repayForm = RepayLoan()
    time = str(datetime.datetime.now().strftime("%A")) + ' ' + str(datetime.datetime.now().date())
    current_user = flask_login.current_user
    limit = current_user.checkLoanLimit

    if request.method == 'POST':
        if borrowForm.submit4.data and borrowForm.validate():
            if current_user.loanAmount==0:
                if borrowForm.amount.data>100:
                    if borrowForm.amount.data<=limit:
                        current_user.loanAmount+=borrowForm.amount.data
                        current_user.amount+=borrowForm.amount.data
                        flash(f'You have successfully borrowed Ksh {borrowForm.amount.data}. Your outstanding loan balance is Ksh {borrowForm.amount.data}')
                    else:
                        flash(f'Please borrow an amount within your loan Limit')
                else:
                    flash(f'Please Enter a valid amount graeter than Ksh 100. You cannot borrow any amount less than Ksh 100')
            else:
                flash(f'Please make sure you have repayed all your outstanding Loan amount')

        if repayForm.submit5.data and repayForm.validate():
            if current_user.loanAmount!=0:
                if current_user.amount >= repayForm.amount.data:
                    if repayForm.amount.data>1:
                        if repayForm.amount.data>current_user.loanAmount:
                            current_user.amount = current_user.amount-current_user.loanAmount
                            current_user.loanAmount = 0
                        else:
                            current_user.amount-=repayForm.amount.data
                            current_user.loanAmount-=repayForm.amount.data
                        flash(f'You have successfully repaid Ksh {repayForm.amount.data}. Your outstanding loan amount is Ksh {current_user.loanAmount}')
                    else:
                        flash('You can only return an amount not less than Ksh 1')
                else:
                    flash('You do not have a sufficient amount in your account to repay this loan')
            else:
                flash(f'You do not have any outstanding Loan amount')

        db.session.commit()

        return redirect(url_for("loans_page"))

    return render_template('loans.html', borrowForm=borrowForm, repayForm=repayForm, time=time, limit=limit)

@app.route('/forex', methods=['GET', 'POST'])
def forex_page():
    y = ''
    if request.method == 'POST':
        try:
            #Getting data from the API
            amount = request.form['amount']
            amount = float(amount)
            from_c = request.form['from_c']
            to_c = request.form['to_c']
            API_KEY= "61N7X1H7ILJI7SDI"
            url = 'https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={}&to_currency={}&apikey={}'.format(
                from_c, to_c, API_KEY)
            response = requests.get(url=url).json()
            rate = response['Realtime Currency Exchange Rate']['5. Exchange Rate']
            rate = float(rate)
            result = rate * amount
            from_c_code = response['Realtime Currency Exchange Rate']['1. From_Currency Code']
            from_c_name = response['Realtime Currency Exchange Rate']['2. From_Currency Name']
            to_c_code = response['Realtime Currency Exchange Rate']['3. To_Currency Code']
            to_c_name = response['Realtime Currency Exchange Rate']['4. To_Currency Name']
            time = response['Realtime Currency Exchange Rate']['6. Last Refreshed']
            return render_template('forex.html', result=round(result, 2), amount=amount,
                                   from_c_code=from_c_code, from_c_name=from_c_name,
                                   to_c_code=to_c_code, to_c_name=to_c_name, time=time)

        except Exception as e:
            return '<h1>Bad request {}</h1>'.format(e)
    return render_template('forex.html')


@app.route('/logout')
def logout_page():
    logout_user()
    flash("Successful log out!", category='info')
    return redirect(url_for("home_page"))
