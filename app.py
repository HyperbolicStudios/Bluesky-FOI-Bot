import os
import pymongo
import dns.resolver
import random
from dotenv import load_dotenv
from atproto import Client, models

from scraper import scrape  # Assuming you have a scrape() function in scraper.py

# Load environment variables
load_dotenv()

# Configure DNS resolver for MongoDB
dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers = ['8.8.8.8']

# MongoDB setup
client = pymongo.MongoClient(os.getenv('MONGO_DB_ACCESS'))
mydb = client.Cluster0  # Update with your actual database name
mycol = mydb["FOI_results"]

#BlueSky setup
client = Client("https://bsky.social")
client.login(os.getenv('BLUESKY_USERNAME'), os.getenv('BLUESKY_PASSWORD'))

def post_to_bluesky(result, curated=False):
    max_len = 300

    if len(result["Description"]) +  40 > max_len:
        desc = result["Description"][:(max_len - 43)] + "..."
    else:
        desc = result["Description"]
    
    # Create the base message without the hyperlink
    if curated == False:
        message = "New FOI release: " + desc + "\n\nView on Open Gov"
    if curated == True:
        message = "Curated FOI release: " + desc + "\n\nView on Open Gov"

    open_gov_url = "https://www2.gov.bc.ca/enSearch/detail?id={}&recorduid={}".format(result["search_ID"], result["Record_UID"])
    
    # Find the starting and ending index of "View on Open Gov" in the message
    start_idx = message.find("View on Open Gov")
    end_idx = start_idx + len("View on Open Gov")
    
    facets = []

    facets.append(
        models.AppBskyRichtextFacet.Main(
            features=[models.AppBskyRichtextFacet.Link(uri=open_gov_url)],
            index=models.AppBskyRichtextFacet.ByteSlice(byte_start=start_idx, byte_end=end_idx)
        )
    )

    client.send_post(message, facets=facets)

    return

def post_FOI_results():
    search_results = scrape()  # Expected keys: Name, URL, and Description
    new_results = []

    for result in search_results:
        # Check if there's a result with the same Name already in the database
        query = {"Name": result["Name"]}
        if not mycol.find_one(query):  # If no matching document is found
            new_results.append(result)
            mycol.insert_one(result)  # Add new result to the database

            post_to_bluesky(result)

    if not new_results:
        #select a random result to post - query for 'starred' == True
        query = {"starred": True}
        starred_results = list(mycol.find(query))

        #if the query returns no results, pass
        if len(starred_results) != 0:
            #select a random result from the starred results
            result = random.choice(starred_results)
            post_to_bluesky(result, curated=True)

    return new_results  # Return the list of new results

post_FOI_results()