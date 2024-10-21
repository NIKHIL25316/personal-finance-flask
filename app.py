from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_mysqldb import MySQL
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from werkzeug.utils import secure_filename
import csv


app = Flask(__name__)
app.secret_key = '<secret_key>'  # Replace with your secret key
app.config['UPLOAD_FOLDER'] = 'uploads' 
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit file size (optional)

# MySQL Configuration
app.config['MYSQL_HOST'] = '<host>'
app.config['MYSQL_USER'] = '<user>'  # Replace with your MySQL username
app.config['MYSQL_PASSWORD'] = '<>password'  # Replace with your MySQL password
app.config['MYSQL_DB'] = '<database>'
mysql = MySQL(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Set the login view to the login function

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    conn = mysql.connection
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    if user:
        return User(user[0], user[1])  # Assuming user[0] is ID and user[1] is username
    return None

# Sign-up page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = mysql.connection
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()
        if user:
            cursor.close()
            return redirect(url_for('signup'))  # Redirect if username exists
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, generate_password_hash(password)))
        conn.commit()
        cursor.close()
        return redirect(url_for('login'))  # Redirect to login after signup
    return render_template('signup.html')

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = mysql.connection
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()
        cursor.close()
        if user and check_password_hash(user[2], password):  # Assuming password is in the third column
            login_user(User(user[0], user[1]))  # Create a User object
            return redirect(url_for('index'))  # Redirect to index after logging in
        else:
            return redirect(url_for('login'))  # Redirect if login fails
    return render_template('login.html')

# Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required  # Ensure the user is logged in to view the index
def index():
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    # Fetch user transactions
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT t.transaction_date, t.description, t.debit, t.credit, a.institution_name FROM transactions t left JOIN accounts a ON t.account_id = a.id  WHERE t.user_id = %s", (current_user.id,))
    transactions = cursor.fetchall()
    # Fetch user accounts
    cursor.execute("SELECT type, institution_name FROM accounts WHERE user_id = %s", (current_user.id,))
    accounts = cursor.fetchall()
    cursor.close()

    # Calculate total credit and debit
    total_credit = sum(txn[3] for txn in transactions if txn[3] is not None)
    total_debit = sum(txn[2] for txn in transactions if txn[2] is not None)

    # Pass accounts and transactions to the template
    return render_template('dashboard.html', transactions=transactions, accounts=accounts, total_credit=total_credit, total_debit=total_debit)


def get_user_accounts():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT institution_name, type, id FROM accounts WHERE user_id = %s", (current_user.id,))
    accounts = cursor.fetchall()
    cursor.close()
    return accounts

@app.route('/accounts', methods=['GET', 'POST'])
@login_required
def accounts():
    if request.method == 'POST':
        institution_name = request.form['institution_name']
        account_type = request.form['type']  # bank/investment/deposit
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO accounts (user_id, institution_name, type) VALUES (%s, %s, %s)",
                       (current_user.id, institution_name, account_type))
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('accounts'))
    
    accounts = get_user_accounts()
    return render_template('accounts.html', accounts=accounts)

@app.route('/delete_account/<int:account_id>', methods=['POST'])
@login_required
def delete_account(account_id):
    # Delete the account from the database
    cursor = mysql.connection.cursor()
    
    # Make sure to only delete accounts owned by the logged-in user
    cursor.execute("DELETE FROM accounts WHERE id = %s AND user_id = %s", (account_id, current_user.id))
    
    mysql.connection.commit()
    cursor.close()
    
    return redirect(url_for('accounts'))


@app.route('/add_transaction', methods=['GET', 'POST'])
@login_required
def add_transaction():
    # Get list of accounts for the dropdown
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, institution_name, type FROM accounts WHERE user_id = %s", (current_user.id,))
    accounts = cursor.fetchall()
    cursor.close()

    if request.method == 'POST':
        account_id = request.form.get('account_id')

        # Get the type of the selected institution
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT type FROM accounts WHERE id = %s", (account_id,))
        institution_type = cursor.fetchone()[0]
        cursor.close()

        if institution_type == 'bank':
            # Handle bank transaction
            debit = request.form.get('debit')
            credit = request.form.get('credit')
            transaction_date = request.form.get('transaction_date')
            description = request.form.get('description')

            cursor = mysql.connection.cursor()
            cursor.execute(
                "INSERT INTO transactions (user_id, account_id, debit, credit, transaction_date, description) VALUES (%s, %s, %s, %s, %s, %s)", 
                (current_user.id, account_id, debit, credit, transaction_date, description)
            )
            mysql.connection.commit()
            cursor.close()

            return redirect(url_for('add_transaction'))

        else:
            # For investment and deposit, just show "Coming soon"
            return "Coming soon"

    return render_template('add_transaction.html', accounts=accounts)


@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    if request.method == 'POST':
        account_id = request.form.get('account_id_upload')

        # Get the type of the selected institution
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT type FROM accounts WHERE id = %s", (account_id,))
        institution_type = cursor.fetchone()[0]
        cursor.close()

        if institution_type == 'bank':
            csv_file = request.files.get(f'csv_file_{account_id}')
            if not csv_file or csv_file.filename == '':
                flash('No file selected or file is empty.', 'error')
                return redirect(url_for('add_transaction'))
        else:
            flash('Coming soon! Transactions for investment and deposit accounts are not yet available.', 'info')
            return redirect(url_for('add_transaction'))

        # Secure and save the file
        filename = secure_filename(csv_file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        try:
            csv_file.save(file_path)
        except Exception as e:
            flash(f'File saving error: {str(e)}', 'error')
            return redirect(url_for('add_transaction'))

        try:
            with open(file_path, newline='') as csvfile:
                csv_reader = csv.DictReader(csvfile)

                # Check if required columns exist in the CSV
                expected_columns = {'transaction_date', 'description', 'debit', 'credit'}
                if not expected_columns.issubset(set(csv_reader.fieldnames)):
                    flash('CSV file is missing required columns.', 'error')
                    return redirect(url_for('add_transaction'))

                cursor = mysql.connection.cursor()

                # Process each row in the CSV file
                for row in csv_reader:
                    transaction_date = row.get('transaction_date')
                    description = row.get('description')
                    debit = float(row.get('debit', 0)) if row.get('debit') else 0
                    credit = float(row.get('credit', 0)) if row.get('credit') else 0

                    # Insert transaction into the `transactions` table
                    cursor.execute('''
                        INSERT INTO transactions (user_id, account_id, transaction_date, description, debit, credit)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    ''', (current_user.id, account_id, transaction_date, description, debit, credit))

                # Insert file upload metadata into the `uploads` table
                cursor.execute('''
                    INSERT INTO uploads (user_id, account_id, file_name)
                    VALUES (%s, %s, %s)
                ''', (current_user.id, account_id, filename))

                mysql.connection.commit()  # Commit all inserts to the database
                flash('CSV uploaded and transactions added successfully!', 'success')

        except Exception as e:
            mysql.connection.rollback()  # Rollback if an error occurs
            flash(f'Error during CSV processing: {str(e)}', 'error')
        finally:
            cursor.close()

    return redirect(url_for('add_transaction'))

if __name__ == '__main__':
    app.run(debug=True)
