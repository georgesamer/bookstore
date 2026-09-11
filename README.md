# 📚 Enterprise NoSQL Bookstore Engine (MongoDB & Python)

An end-to-end, production-grade NoSQL database architecture project built on a dataset of **11,000+ real-world book records and ratings**.

This repository demonstrates practical expertise in NoSQL data operations, advanced schema design patterns, complex multi-stage aggregation pipelines, ESR-aligned compound indexing strategies, and query performance tuning.

---

## 🎯 Executive Summary & Certification Context

The architecture and operations in this project directly align with hands-on technical concepts certified across official MongoDB Skill Badges and advanced courses:

* **CRUD Operations & Query Mechanics**
* **Relational (SQL) to MongoDB Document Model Migration**
* **MongoDB Aggregation Framework**
* **Indexing Strategy & Query Optimization (ESR Rule)**
* **Advanced Schema Design Patterns & Anti-Pattern Mitigation**
* **Diagnostics & System Performance Tuning (`explain` & Profiling)**

---

## 🏗️ Architecture & Applied Schema Design Patterns

Rather than storing data in flat tables, this engine transforms CSV data into an optimized BSON/JSON document model leveraging industry-standard design patterns:

### 1. Attribute Pattern
* Dynamic metadata fields (`pages`, `publisher`, `language`, `publication_date`) are modeled as key-value pairs inside an `attributes` array. This stabilizes the document schema against variable fields across publishers.

### 2. Subset Pattern
* To optimize memory footprint and read latency, the primary `books` collection embeds only the 3 most recent/relevant user reviews in a `recent_reviews` array. Full review histories are persisted in a dedicated `reviews` collection.

### 3. Computed Pattern
* Metrics such as `total_reviews_count` and `avg_rating` are pre-calculated and stored at document level to allow low-cost, zero-computation sorting and filtering.

### 4. Extended Reference Pattern
* Historical transaction models snapshot item details (`title`, `price_at_purchase`) inside order records to preserve historical integrity against catalog price updates.

---

## ⚡ Indexing Strategy & Performance Optimization

To eliminate costly full collection scans (`COLLSCAN`) and ensure efficient index scans (`IXSCAN`), indexing adheres strictly to the **ESR Rule (Equality, Sort, Range)**:

* **Compound Index (`genres_1_avg_rating_-1_price_1`)**:
  * **E**quality: `genres`
  * **S**ort: `avg_rating` (Descending)
  * **R**ange: `price` (Ascending)
* **Text Index**: Full-text search across `title` and string values in `attributes.v`.
* **Unique Index**: Enforced uniqueness on `isbn`.

---

## 📁 Repository Structure

```
bookstore
├─ analytics_and_tuning.py     # Aggregation pipeline analytics & query diagnostics
├─ data
│  └─ books.csv                # Raw source dataset (11,000+ records)
├─ README.md                   # Project documentation
├─ requirements.txt            # Python dependencies
└─ transform_and_clean.py      # ETL script applying schema patterns & indexing
```

---

## 📊 Analytics Pipeline & Query Diagnostics

The included `analytics_and_tuning.py` script runs real-time analytical workloads, such as calculating publisher performance metrics:

```javascript
[
  {
    "$match": { "avg_rating": { "$gte": 4.0 }, "stock": { "$gt": 0 } }
  },
  { "$unwind": "$attributes" },
  { "$match": { "attributes.k": "publisher" } },
  {
    "$group": {
      "_id": "$attributes.v",
      "total_books": { "$sum": 1 },
      "avg_book_price": { "$avg": "$price" },
      "total_ratings": { "$sum": "$ratings_count" }
    }
  },
  { "$sort": { "total_ratings": -1 } },
  { "$limit": 5 }
]
```

Execution plan diagnostics (`explain("executionStats")`) verify that queries execute efficiently using index scans (`IXSCAN`).

---

## 🚀 Getting Started

### 1. Prerequisites

* Python 3.9+
* Local MongoDB instance running on `mongodb://localhost:27017`

### 2. Environment Setup

```bash
# Clone repository
git clone https://github.com/your-username/bookstore.git
cd bookstore

# Install dependencies
pip install -r requirements.txt
```

### 3. Execution Pipeline

```bash
# Step 1: Run ETL pipeline to clean, patternize, and index the dataset
# (reads the source file from data/books.csv)
python transform_and_clean.py

# Step 2: Execute aggregation analytics and performance diagnostics
python analytics_and_tuning.py
```