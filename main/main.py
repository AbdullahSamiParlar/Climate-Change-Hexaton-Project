from flask import Flask, request, redirect, render_template, session, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_session import Session  # For session management
from werkzeug.security import generate_password_hash, check_password_hash
from deep_translator import GoogleTranslator  # Importing deep-translator for translation
from transformers import pipeline  # Importing transformers for AI functionality
from functools import lru_cache
import time

# Initialize the Flask application
app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///climate_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Session configuration
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)  # Initialize session

# Initialize the database and migration tools
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Initialize GPT-2 model for text generation
gpt2 = pipeline("text-generation", model="gpt2")

# Models: User and ClimateData
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class ClimateData(db.Model):
    __tablename__ = 'climate_data'
    id = db.Column(db.Integer, primary_key=True)
    ulke = db.Column(db.String(100), nullable=False)  # Country
    sehir = db.Column(db.String(100), nullable=False)  # City
    saat = db.Column(db.String(50), nullable=False)  # Time
    nem = db.Column(db.Float, nullable=False)  # Humidity (as a fraction)
    sicaklik_degeri = db.Column(db.Float, nullable=False)  # Temperature
    oran = db.Column(db.Float, nullable=False)  # CO2 Ratio (as a fraction)
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)

# Function: Translate Text using Deep Translator with caching and performance measurement
@lru_cache(maxsize=1000)  # Cache up to 1000 translations
def translate_text(text, dest_language):
    if text:
        try:
            # Start the timer for performance measurement
            start_time = time.time()
            translated = GoogleTranslator(source='auto', target=dest_language).translate(text)
            elapsed_time = time.time() - start_time  # Measure elapsed time
            print(f"Translation time for '{text}': {elapsed_time:.2f} seconds")
            return translated
        except Exception as e:
            print(f"Translation error: {e}")
            return text  # Fallback to original text if translation fails
    return text

# Route: Home Page
@app.route('/')
def index():
    climate_data = ClimateData.query.all()
    language = session.get('language', 'tr')
    return render_template('tables.html', climate_data=climate_data, translate_text=translate_text, language=language)

@app.route('/delete_all_entries', methods=['GET', "POST"])
def delete_all_entries():
    try:
        # Delete all entries from ClimateData table
        db.session.query(ClimateData).delete()
        db.session.commit()
        return "All entries deleted successfully!", 200
    except Exception as e:
        db.session.rollback()  # Rollback the session in case of error
        return f"An error occurred: {str(e)}", 500

# Route: Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    language = session.get('language', 'tr')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the username already exists
        if User.query.filter_by(username=username).first():
            flash(translate_text("Username already exists.", language), "error")
            return redirect(url_for('register'))

        # Hash the password and create a new user
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash(translate_text("Registration successful! Please log in.", language), "success")
        return redirect(url_for('login'))  # Redirect to login after successful registration

    return render_template('register.html', translate_text=translate_text, language=language)

# Route: Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    language = session.get('language', 'tr')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Verify username and password
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['username'] = username  # Store username in session
            flash(translate_text("Logged in successfully!", language), "success")
            return redirect(url_for('index'))  # Redirect to the home page after successful login
        flash(translate_text("Invalid credentials.", language), "error")

    return render_template('login.html', translate_text=translate_text, language=language)

# Route: Logout
@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove username from session
    flash("You have been logged out.", "success")
    return redirect(url_for('index'))

# Route: Add Climate Data
@app.route('/add', methods=['POST'])
def add_climate_data():
    # Check if the user is logged in
    if 'username' not in session:
        flash("You need to log in to add data.", "error")
        return redirect('/login')

    try:
        # Retrieve form data
        country = request.form['country']
        city = request.form['city']
        time = request.form['time']
        humidity = float(request.form['humidity']) / 100  # Convert to fraction
        temperature = float(request.form['temperature'])
        oran = float(request.form['oran']) / 100  # Convert to fraction

        # Validate humidity and CO2 ratio
        if not (0 <= humidity <= 1) or not (0 <= oran <= 1):
            flash("Humidity and CO2 ratio must be between 0 and 100.", "error")
            return redirect('/')

        # Create a new ClimateData entry
        new_data = ClimateData(
            ulke=country,
            sehir=city,
            saat=time,
            nem=humidity,
            sicaklik_degeri=temperature,
            oran=oran
        )

        # Add the entry to the database
        db.session.add(new_data)
        db.session.commit()
        flash("Climate data added successfully!", "success")

    except ValueError:
        flash("Invalid input values. Please check your data.", "error")
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "error")

    return redirect('/app')

# Route: App Page
# Route: App Page
@app.route('/app', methods=['GET'])
def app_page():
    query = request.args.get('query', '').strip()  # Get the query and remove whitespace

    # Check if the query is not empty to filter climate data
    if query:  
        # Filter the data based on the query, only including records that start with the query
        climate_data = ClimateData.query.filter(
            (ClimateData.ulke.ilike(f'{query}%')) |  # Change to starts with
            (ClimateData.sehir.ilike(f'{query}%'))   # Change to starts with
        ).order_by(ClimateData.upvotes.desc(), ClimateData.sehir).all()
    else:
        # If there is no query, fetch all records
        climate_data = ClimateData.query.order_by(ClimateData.upvotes.desc(), ClimateData.sehir).all()

    language = session.get('language', 'tr')
    has_data = len(climate_data) > 0  # Check if there is any data

    return render_template('app.html', 
                           climate_data=climate_data, 
                           translate_text=translate_text, 
                           language=language,
                           has_data=has_data)  # Pass the flag to the template

@app.route('/upvote/<int:id>', methods=['POST'])
def upvote(id):
    if 'username' not in session:
        flash("You need to log in to vote.", "error")
        return redirect(request.referrer or '/app')

    data = ClimateData.query.get_or_404(id)
    data.upvotes += 1  # Increment the upvote count
    db.session.commit()
    session[f'voted_{id}'] = True  # Track the user's vote
    flash("Upvoted successfully!", "success")
    return redirect(request.referrer or '/app')

# Route: Downvote
@app.route('/downvote/<int:id>', methods=['POST'])
def downvote(id):
    if 'username' not in session:
        flash("You need to log in to vote.", "error")
        return redirect(request.referrer or '/app')

    data = ClimateData.query.get_or_404(id)
    data.downvotes += 1  # Increment the downvote count
    db.session.commit()
    session[f'voted_{id}'] = True  # Track the user's vote
    flash("Downvoted successfully!", "success")
    return redirect(request.referrer or '/app')

# Route: Change Language
@app.route('/lang', methods=['GET'])
def change_language():
    language = request.args.get('language', 'tr')
    session['language'] = language  # Store the selected language in the session
    return redirect(request.referrer or url_for('index'))

# Route: Help Page
@app.route('/help')
def help_page():
    language = session.get('language', 'tr')
    return render_template('help.html', translate_text=translate_text, language=language)

# Route: Climate Change Page
@app.route('/c')
def climate_change_page():
    language = session.get('language', 'tr')
    return render_template('c.html', translate_text=translate_text, language=language)

# Route: AI Climate Change Q&A
@app.route('/ai', methods=['GET', 'POST'])
def ai():
    question = ""
    response = ""  # Initialize response variable
    if request.method == 'POST':
        question = request.form.get('question', '')
        if question:
            # Generate response from AI
            response_data = gpt2(question, max_length=50, num_return_sequences=1, truncation=True)
            response = response_data[0]['generated_text'].strip()  # Clean up the response
        else:
            flash("Please ask a question about climate change.", "error")
            return redirect(url_for('ai'))

    # Get the current language from the session
    language = session.get('language', 'tr')

    # Using Deep Translator for UI text
    ai_title = translate_text("Climate Change Q&A", language)
    home_text = translate_text("Home", language)
    logout_text = translate_text("Logout", language)
    enter_question_text = translate_text("Enter your question:", language)
    ask_text = translate_text("Ask", language)
    ai_response_text = translate_text("AI Response", language)
    no_response_text = translate_text("No response received yet.", language)

    return render_template('ai.html', 
                           question=question, 
                           response=response, 
                           ai_title=ai_title, 
                           home_text=home_text, 
                           logout_text=logout_text, 
                           enter_question_text=enter_question_text, 
                           ask_text=ask_text, 
                           ai_response_text=ai_response_text, 
                           no_response_text=no_response_text,
                           translate_text=translate_text,  # Ensure this line is included
                           language=language)

# Initialize the database
with app.app_context():
    db.create_all()

# Run the application
if __name__ == '__main__':
    app.run(debug=True)
