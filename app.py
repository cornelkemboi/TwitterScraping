from flask import Flask, render_template
import mysql.connector
import os
from datetime import datetime

app = Flask(__name__)


@app.route('/')
def display_tweets():
    # Database configuration
    db_config = {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'database': os.getenv('MYSQL_DB', 'feedback_db'),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', 'admin'),
        'port': os.getenv('MYSQL_PORT', 3307)
    }

    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    # Query to get the tweet data
    query = """
        SELECT tweet_id, timestamp, likes, retweets, comments, tweet_link
        FROM tweets_fb
        WHERE timestamp >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
    """
    cursor.execute(query)
    records = cursor.fetchall()

    # Process data for the charts
    monthly_data = {}
    top_tweet_current_month = {'likes': 0, 'retweets': 0, 'comments': 0, 'link': ''}
    most_liked_tweet_all_time = {'likes': 0, 'retweets': 0, 'comments': 0, 'link': ''}

    current_month = datetime.now().month

    for record in records:
        tweet_id, timestamp, likes, retweets, comments, tweet_link = record
        date_obj = datetime.strptime(str(timestamp), '%Y-%m-%d %H:%M:%S')

        # Group data by month (e.g., "2023-08")
        month_key = date_obj.strftime('%Y-%m')

        if month_key not in monthly_data:
            monthly_data[month_key] = {'likes': 0, 'retweets': 0, 'comments': 0}

        # Add the tweet's metrics to the respective month
        monthly_data[month_key]['likes'] += likes
        monthly_data[month_key]['retweets'] += retweets
        monthly_data[month_key]['comments'] += comments

        # Check if this is the top tweet of the current month
        if date_obj.month == current_month and likes > top_tweet_current_month['likes']:
            top_tweet_current_month = {
                'likes': likes,
                'retweets': retweets,
                'comments': comments,
                'link': tweet_link
            }

        # Check if this is the most liked tweet of all time
        if likes > most_liked_tweet_all_time['likes']:
            most_liked_tweet_all_time = {
                'likes': likes,
                'retweets': retweets,
                'comments': comments,
                'link': tweet_link
            }

    connection.close()

    # Prepare data to send to the frontend
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


if __name__ == "__main__":
    app.run(debug=True)
