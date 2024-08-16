# main__.py

import os
import sys
import argparse
import getpass
import logging
from dotenv import load_dotenv
from twitter_scraper import Twitter_Scraper

# Configure logging
logging.basicConfig(level=logging.INFO)


def main():
    try:
        logging.info("Loading .env file")
        load_dotenv()
        logging.info("Loaded .env file\n")
    except Exception as e:
        logging.error(f"Error loading .env file: {e}")
        sys.exit(1)

    parser = argparse.ArgumentParser(
        usage="python scraper [option] ... [arg] ...",
        description="Twitter Scraper is a tool that allows you to scrape tweets from Twitter without using Twitter's "
                    "API."
    )

    parser.add_argument("--mail", type=str, default=os.getenv("TWITTER_MAIL"), help="Your Twitter mail.")
    parser.add_argument("--user", type=str, default=os.getenv("TWITTER_USERNAME"), help="Your Twitter username.")
    parser.add_argument("--password", type=str, default=os.getenv("TWITTER_PASSWORD"), help="Your Twitter password.")
    parser.add_argument("-t", "--tweets", type=int, default=250, help="Number of tweets to scrape (default: 50)")
    parser.add_argument("-u", "--username", type=str, help="Twitter username. Scrape tweets from a user's profile.")
    parser.add_argument("-ht", "--hashtag", type=str, help="Twitter hashtag. Scrape tweets from a hashtag.")
    parser.add_argument("-ntl", "--no_tweets_limit", action='store_true',
                        help="Set no limit to the number of tweets to scrape.")
    parser.add_argument("-q", "--query", type=str,
                        help="Twitter query or search. Scrape tweets from a query or search.")
    parser.add_argument("-a", "--add", type=str, default="",
                        help="Additional data to scrape and save in the .csv file.")
    parser.add_argument("--latest", action="store_true", help="Scrape latest tweets")
    parser.add_argument("--top", action="store_true", help="Scrape top tweets")

    args = parser.parse_args()

    USER_MAIL = args.mail
    USER_UNAME = args.user or input("Twitter Username: ")
    USER_PASSWORD = args.password or getpass.getpass("Enter Password: ")

    tweet_type_args = [arg for arg in [args.username, args.hashtag, args.query] if arg]

    if len(tweet_type_args) > 1:
        logging.error("Please specify only one of --username, --hashtag, or --query.")
        sys.exit(1)

    if args.latest and args.top:
        logging.error("Please specify either --latest or --top. Not both.")
        sys.exit(1)

    if USER_UNAME and USER_PASSWORD:
        scraper = Twitter_Scraper(
            mail=USER_MAIL,
            username=USER_UNAME,
            password=USER_PASSWORD
        )

        scraper.login()
        scraper.scrape_tweets(
            max_tweets=args.tweets,
            no_tweets_limit=args.no_tweets_limit,
            scrape_username=args.username,
            scrape_hashtag=args.hashtag,
            scrape_query=args.query,
            scrape_latest=args.latest,
            scrape_top=args.top,
            scrape_poster_details="pd" in args.add.split(",")
        )
        # scraper.save_to_csv()
        scraper.save_to_mysql()

        if not scraper.interrupted:
            scraper.driver.close()
    else:
        logging.error("Missing Twitter username or password. Please check your .env file.")
        sys.exit(1)


if __name__ == "__main__":
    main()
