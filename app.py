# Import necessary modules and packages
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Initialize the Flask application
app = Flask(__name__)
app.secret_key = 'shravanichavan'  # Secret key for session management
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/expenses'  # Database URI
db = SQLAlchemy(app)  # Initialize the SQLAlchemy object

# User model for storing user details
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Unique identifier for each user
    username = db.Column(db.String(50), nullable=False)  # User's name
    email = db.Column(db.String(100), unique=True, nullable=False)  # User's email (must be unique)
    password = db.Column(db.String(200), nullable=False)  # Hashed password

# Expense model for storing expense details
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Unique identifier for each expense
    amount = db.Column(db.Float, nullable=False)  # Amount of the expense
    description = db.Column(db.String(200), nullable=False)  # Description of the expense
    date = db.Column(db.Date, nullable=False)  # Date of the expense
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Foreign key referencing the user

# Home route that redirects to login or dashboard based on session state
@app.route('/')
def home():
    if 'user_id' in session:  # Check if user is logged in
        return redirect(url_for('dashboard'))  # Redirect to dashboard if logged in
    return redirect(url_for('login'))  # Redirect to login if not logged in

# Registration route for new users
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':  # Handle form submission
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']  # Password to be hashed
        
        # Hash the password for security
        hashed_password = generate_password_hash(password)
        
        # Check if the email already exists in the database
        existing_user = db.session.query(User).filter_by(email=email).first()
        if existing_user:
            return "Email already registered."  # Notify user if email is taken

        # Create a new user object and add to the database
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()  # Commit the new user to the database
        return redirect(url_for('login'))  # Redirect to login after successful registration

    return render_template('register.html')  # Render registration page

# Login route for existing users
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':  # Handle form submission
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()  # Find user by email
        if user and check_password_hash(user.password, password):  # Validate password
            session['user_id'] = user.id  # Store user ID in session
            return redirect(url_for('dashboard'))  # Redirect to dashboard on successful login
        return 'Invalid Credentials'  # Notify user of invalid credentials
    return render_template('login.html')  # Render login page

# Logout route to end user session
@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Remove user ID from session
    return redirect(url_for('login'))  # Redirect to login page

# Route for updating existing expenses
@app.route('/update_expense/<int:id>', methods=['GET', 'POST'])
def update_expense(id):
    expense = Expense.query.get_or_404(id)  # Retrieve the expense or return a 404 error
    if request.method == 'POST':  # Handle form submission
        expense.amount = request.form['amount']  # Update amount
        expense.description = request.form['description']  # Update description
        expense.date = datetime.strptime(request.form['date'], '%Y-%m-%d')  # Update date
        db.session.commit()  # Save changes to the database
        return redirect(url_for('dashboard'))  # Redirect to dashboard after update
    
    return render_template('update_expense.html', expense=expense)  # Render update expense page

# Dashboard route to display user expenses
@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:  # Check if user is logged in
        user_expenses = Expense.query.filter_by(user_id=session['user_id']).all()  # Retrieve user's expenses
        
        # Prepare data for the chart
        labels = [expense.description for expense in user_expenses]  # Use expense descriptions as labels
        data = [expense.amount for expense in user_expenses]  # Use expense amounts as data

        return render_template('dashboard.html', expenses=user_expenses, labels=labels, data=data)
    
    return redirect(url_for('login'))  # Redirect to login if user is not logged in

# Route for adding new expenses
@app.route('/add_expense', methods=['GET', 'POST'])
def add_expense():
    if 'user_id' in session:  # Check if user is logged in
        if request.method == 'POST':  # Handle form submission
            amount = request.form['amount']
            description = request.form['description']
            date = datetime.strptime(request.form['date'], '%Y-%m-%d')  # Parse date
            new_expense = Expense(amount=amount, description=description, date=date, user_id=session['user_id'])
            db.session.add(new_expense)  # Add new expense to the session
            db.session.commit()  # Commit new expense to the database
            return redirect(url_for('dashboard'))  # Redirect to dashboard after adding expense
        return render_template('add_expense.html')  # Render add expense page
    return redirect(url_for('login'))  # Redirect to login if user is not logged in

# Route for deleting expenses
@app.route('/delete_expense/<int:id>')
def delete_expense(id):
    if 'user_id' in session:  # Check if user is logged in
        expense = Expense.query.get(id)  # Retrieve expense by ID
        if expense:  # If expense exists
            db.session.delete(expense)  # Delete expense from the session
            db.session.commit()  # Commit deletion to the database
        return redirect(url_for('dashboard'))  # Redirect to dashboard after deletion
    return redirect(url_for('login'))  # Redirect to login if user is not logged in

# Run the application
if __name__ == '__main__':
    app.run(debug=True)  # Start the Flask application in debug mode
