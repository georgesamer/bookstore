import os
import json
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "bookstore_db")

# Connect to the MongoDB database
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
books_collection = db[os.getenv("BOOKS_COLLECTION", "books")]

print("1. AGGREGATION PIPELINE: Analysis of Publishers and Ratings Reports")

# Complex aggregation pipeline to group and analyze book data by publisher and genre
pipeline = [
    # Stage 1: Filter books with high ratings and available stock ($match)
    {
        "$match": {
            "avg_rating": {"$gte": 4.0},
            "stock": {"$gt": 0}
        }
    },
    # Stage 2: Unwind the attributes array to access the publisher ($unwind)
    {"$unwind": "$attributes"},
    # Stage 3: Filter the publisher attribute only ($match)
    {
        "$match": {
            "attributes.k": "publisher"
        }
    },
    # Stage 4: Group the data by publisher name and calculate metrics ($group)
    {
        "$group": {
            "_id": "$attributes.v",
            "total_books": {"$sum": 1},
            "avg_book_price": {"$avg": "$price"},
            "total_ratings": {"$sum": "$ratings_count"},
            "highest_rated_book_score": {"$max": "$avg_rating"}
        }
    },
    # Stage 5: Filter publishers who have more than 10 books ($match)
    {
        "$match": {
            "total_books": {"$gte": 10}
        }
    },
    # Stage 6: Reorganize the output and calculate the rounded average price ($project)
    {
        "$project": {
            "publisher": "$_id",
            "_id": 0,
            "total_books": 1,
            "avg_book_price": {"$round": ["$avg_book_price", 2]},
            "total_ratings": 1,
            "highest_rated_book_score": 1
        }
    },
    # Stage 7: Order the results by total ratings in descending order ($sort)
    {"$sort": {"total_ratings": -1}},
    # Stage 8: Display only the top 5 publishers ($limit)
    {"$limit": 5}
]

results = list(books_collection.aggregate(pipeline))
print(json.dumps(results, indent=2, ensure_ascii=False))

print("2. DIAGNOSTICS & TUNING: Analysis of Query Execution Plan (Explain)")

# Equality: genres | Sort: avg_rating | Range: price
explain_result = books_collection.find({
    "genres": "General Literature",
    "price": {"$gte": 10.0, "$lte": 30.0}
}).sort("avg_rating", -1).explain()

execution_stage = explain_result.get("executionStats", {}).get("executionStages", {})

# Print details of the execution plan to verify index utilization
winning_plan = explain_result.get("queryPlanner", {}).get("winningPlan", {})
print(f"Stage Name: {winning_plan.get('stage') or winning_plan.get('inputStage', {}).get('stage')}")
print(f"Index Used: {winning_plan.get('inputStage', {}).get('indexName', 'No Index / COLLSCAN')}")