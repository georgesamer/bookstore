import os
from dotenv import load_dotenv
from pymongo import MongoClient, TEXT, ASCENDING, DESCENDING
from datetime import datetime

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "bookstore_db")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

raw_collection = db[os.getenv("RAW_COLLECTION", "raw_books")]
books_collection = db[os.getenv("BOOKS_COLLECTION", "books")]
reviews_collection = db[os.getenv("REVIEWS_COLLECTION", "reviews")]

# Reset the target collections
books_collection.drop()
reviews_collection.drop()

print("Starting raw data processing and transformation")

raw_docs = list(raw_collection.find())
books_to_insert = []
reviews_to_insert = []

for doc in raw_docs:
    # cleaning and normalizing the document
    cleaned_doc = {k.strip(): v for k, v in doc.items()}
    
    title = str(cleaned_doc.get("title", "Untitled")).strip()
    isbn = str(cleaned_doc.get("isbn") or cleaned_doc.get("isbn13") or cleaned_doc.get("_id")).strip()
    
    # 1. parsing average rating and handling potential errors
    try:
        avg_rating = float(cleaned_doc.get("average_rating", 0.0))
    except (ValueError, TypeError):
        avg_rating = 0.0

    # 2. parsing page count and calculating price
    try:
        pages_val = int(cleaned_doc.get("num_pages", 200))
        price = round(max(9.99, pages_val * 0.05), 2)
    except (ValueError, TypeError):
        pages_val = 0
        price = 19.99

    # 3. parsing authors (splitting the comma-separated string into an array)
    raw_authors = str(cleaned_doc.get("authors", "Unknown"))
    authors = [a.strip() for a in raw_authors.split("/") if a.strip()]

    # 4. Attribute Pattern
    attributes = []
    if pages_val > 0:
        attributes.append({"k": "pages", "v": pages_val})
    
    publisher = str(cleaned_doc.get("publisher", "")).strip()
    if publisher:
        attributes.append({"k": "publisher", "v": publisher})

    lang = str(cleaned_doc.get("language_code", "")).strip()
    if lang:
        attributes.append({"k": "language", "v": lang})

    # 5. parsing publication date and converting it to ISODate
    pub_date_str = str(cleaned_doc.get("publication_date", "")).strip()
    pub_date = None
    if pub_date_str:
        try:
            pub_date = datetime.strptime(pub_date_str, "%m/%d/%Y")
            attributes.append({"k": "publication_date", "v": pub_date})
        except ValueError:
            pass

    # 6. Subset Pattern
    text_reviews_cnt = 0
    try:
        text_reviews_cnt = int(cleaned_doc.get("text_reviews_count", 0))
    except (ValueError, TypeError):
        pass

    recent_reviews = []
    if text_reviews_cnt > 0:
        review_doc = {
            "book_isbn": isbn,
            "user": "Reader_Community",
            "rating": avg_rating,
            "comment": f"Official community discussion thread with {text_reviews_cnt} total reviews.",
            "created_at": datetime.now()
        }
        reviews_to_insert.append(review_doc)

        recent_reviews.append({
            "user": review_doc["user"],
            "rating": review_doc["rating"],
            "comment": review_doc["comment"]
        })

    # 7. Computed Pattern
    ratings_count = 0
    try:
        ratings_count = int(cleaned_doc.get("ratings_count", 0))
    except (ValueError, TypeError):
        pass

    book_doc = {
        "title": title,
        "isbn": isbn,
        "authors": authors,
        "genres": ["General Literature"],
        "price": price,
        "stock": 100,
        "attributes": attributes,
        "recent_reviews": recent_reviews,
        "total_reviews_count": text_reviews_cnt,
        "ratings_count": ratings_count,
        "avg_rating": avg_rating
    }

    books_to_insert.append(book_doc)

# store the transformed documents into the target collections
if books_to_insert:
    books_collection.insert_many(books_to_insert)
if reviews_to_insert:
    reviews_collection.insert_many(reviews_to_insert)

print(f"Data transformation completed. Data inserted into {len(books_to_insert)} 'books'.")
print(f"Data transformation completed. Data inserted into {len(reviews_to_insert)} 'reviews'.")

# ==========================================
# 6. Indexing Strategy & ESR Rule
# ==========================================
print("creating indexes for the 'books' collection...")

books_collection.create_index([("isbn", ASCENDING)], unique=True)
books_collection.create_index([("title", TEXT), ("attributes.v", TEXT)])

# ESR Compound Index (Equality: genres, Sort: avg_rating, Range: price)
books_collection.create_index([
    ("genres", ASCENDING),
    ("avg_rating", DESCENDING),
    ("price", ASCENDING)
])

print("Indexes created successfully!")