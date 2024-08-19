from functools import wraps
from flask import Flask, render_template, flash, redirect, url_for, session, request
import mysql.connector
import os
from datetime import datetime
import bcrypt

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your_secret_key')


def db_connection():
    db_config = {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'database': os.getenv('MYSQL_DB', 'feedback_db'),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', 'admin'),
        'port': os.getenv('MYSQL_PORT', 3307)
    }

    connection = mysql.connector.connect(**db_config)
    return connection


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('You need to log in to access this page.', 'danger')
            return redirect(url_for('user_login'))
        return f(*args, **kwargs)

    return decorated_function


@app.route('/display')
@login_required
def display_tweets():
    conn = db_connection()
    cursor = conn.cursor()

    query = """
        SELECT tweet_id, timestamp, likes, retweets, comments, tweet_link
        FROM tweets_fb
        WHERE timestamp >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
    """
    cursor.execute(query)
    records = cursor.fetchall()

    monthly_data = {}
    top_tweet_current_month = {'likes': 0, 'retweets': 0, 'comments': 0, 'link': ''}
    most_liked_tweet_all_time = {'likes': 0, 'retweets': 0, 'comments': 0, 'link': ''}

    current_month = datetime.now().month

    for record in records:
        tweet_id, timestamp, likes, retweets, comments, tweet_link = record
        date_obj = datetime.strptime(str(timestamp), '%Y-%m-%d %H:%M:%S')

        month_key = date_obj.strftime('%Y-%m')

        if month_key not in monthly_data:
            monthly_data[month_key] = {'likes': 0, 'retweets': 0, 'comments': 0}

        monthly_data[month_key]['likes'] += likes
        monthly_data[month_key]['retweets'] += retweets
        monthly_data[month_key]['comments'] += comments

        if date_obj.month == current_month and likes > top_tweet_current_month['likes']:
            top_tweet_current_month = {
                'likes': likes,
                'retweets': retweets,
                'comments': comments,
                'link': tweet_link
            }

        if likes > most_liked_tweet_all_time['likes']:
            most_liked_tweet_all_time = {
                'likes': likes,
                'retweets': retweets,
                'comments': comments,
                'link': tweet_link
            }

    cursor.close()
    conn.close()

    months = sorted(monthly_data.keys())
    likes_per_month = [monthly_data[month]['likes'] for month in months]
    retweets_per_month = [monthly_data[month]['retweets'] for month in months]
    comments_per_month = [monthly_data[month]['comments'] for month in months]

    return render_template(
        'index.html',
        months=months,
        likes_per_month=likes_per_month,
        retweets_per_month=retweets_per_month,
        comments_per_month=comments_per_month,
        top_tweet_current_month=top_tweet_current_month,
        most_liked_tweet_all_time=most_liked_tweet_all_time
    )


@app.route('/', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = db_connection()
        cursor = conn.cursor()

        query = """
        SELECT id, password, role 
        FROM register_user 
        WHERE email = %s;
        """
        cursor.execute(query, (email,))
        user = cursor.fetchone()

        if user:
            user_id, hashed_password, role = user
            try:
                if bcrypt.checkpw(password.encode(), hashed_password.encode()):
                    session['user_id'] = user_id
                    session['role'] = role
                    cursor.close()
                    conn.close()
                    return redirect(url_for('display_tweets'))
                else:
                    flash('Invalid email or password. Please try again.', 'danger')
            except ValueError as e:
                flash(f"Password check error: {str(e)}", 'danger')
        else:
            flash('Invalid email or password. Please try again.', 'danger')

        cursor.close()
        conn.close()

        return redirect(url_for('user_login'))

    return render_template('login.html')


@app.route('/filter-data')
@login_required
def filter_data():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    conn = db_connection()
    cursor = conn.cursor()

    query = """
        SELECT tweet_id, timestamp, likes, retweets, comments, tweet_link
        FROM tweets_fb
        WHERE timestamp BETWEEN %s AND %s
    """
    cursor.execute(query, (start_date, end_date))
    records = cursor.fetchall()

    # Process records to extract the monthly data, top tweet, and most liked tweet as before
    monthly_data = {}
    top_tweet_current_month = {'likes': 0, 'retweets': 0, 'comments': 0, 'link': ''}
    most_liked_tweet_all_time = {'likes': 0, 'retweets': 0, 'comments': 0, 'link': ''}

    current_month = datetime.now().month

    for record in records:
        tweet_id, timestamp, likes, retweets, comments, tweet_link = record
        date_obj = datetime.strptime(str(timestamp), '%Y-%m-%d %H:%M:%S')

        month_key = date_obj.strftime('%Y-%m')

        if month_key not in monthly_data:
            monthly_data[month_key] = {'likes': 0, 'retweets': 0, 'comments': 0}

        monthly_data[month_key]['likes'] += likes
        monthly_data[month_key]['retweets'] += retweets
        monthly_data[month_key]['comments'] += comments

        if date_obj.month == current_month and likes > top_tweet_current_month['likes']:
            top_tweet_current_month = {
                'likes': likes,
                'retweets': retweets,
                'comments': comments,
                'link': tweet_link
            }

        if likes > most_liked_tweet_all_time['likes']:
            most_liked_tweet_all_time = {
                'likes': likes,
                'retweets': retweets,
                'comments': comments,
                'link': tweet_link
            }

    cursor.close()
    conn.close()

    # Prepare data to return as JSON
    months = sorted(monthly_data.keys())
    likes_per_month = [monthly_data[month]['likes'] for month in months]
    retweets_per_month = [monthly_data[month]['retweets'] for month in months]
    comments_per_month = [monthly_data[month]['comments'] for month in months]

    return {
        'months': months,
        'likes': likes_per_month,
        'retweets': retweets_per_month,
        'comments': comments_per_month,
        'topTweetCurrentMonth': top_tweet_current_month,
        'mostLikedTweetAllTime': most_liked_tweet_all_time
    }


@app.route('/logout')
def user_logout():
    try:
        session.pop('user_id', None)
        flash('You have been logged out.', 'info')
    except Exception as e:
        flash(f"There was an error during logout: {str(e)}", "danger")
    return redirect(url_for('user_login'))


if __name__ == "__main__":
    app.run(debug=True)
