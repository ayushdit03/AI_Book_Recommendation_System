from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.stem.porter import PorterStemmer
from pymongo import MongoClient
import certifi
import os
import logging

app = Flask(__name__, static_url_path='/static')

# Configure logging
logging.basicConfig(level=logging.INFO)

# MongoDB configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://pj29102005:bTQfPPqugcyv9mv8@cluster0.9nt5ygc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
client = MongoClient(
    MONGO_URI,
    tls=True,
    tlsAllowInvalidCertificates=True,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=30000
)
db = client['library']
books_collection = db['books_data']
feedback_collection = db['feedback']

# Fetch data from MongoDB
try:
    books_data = list(books_collection.find())
    new_df = pd.DataFrame(books_data)
    logging.info(f"Books data fetched from MongoDB: {new_df.head()}")
except Exception as e:
    logging.error(f"Error fetching data from MongoDB: {e}")
    new_df = pd.DataFrame()  # Use an empty dataframe if data fetching fails

# Ensure 'books' column exists and handle NaN values
if 'books' in new_df.columns:
    new_df['books'] = new_df['books'].fillna('')
else:
    logging.error("Column 'books' not found in MongoDB data.")
    new_df['books'] = ''

# Initialize vectorizer and compute vectors
cv = CountVectorizer(max_features=5000, stop_words="english")
vectors = np.array([])
similar = np.array([])

if not new_df.empty:
    try:
        vectors = cv.fit_transform(new_df['books']).toarray()
        similar = cosine_similarity(vectors)
        logging.info("Vectorization and similarity computation successful.")
    except Exception as e:
        logging.error(f"Error initializing vectorizer or computing vectors: {e}")

ps = PorterStemmer()

def stem(text):
    return " ".join([ps.stem(word) for word in text.split()])

@app.route('/')
def home():
    try:
        data = list(books_collection.find({"rating": 5}).sort("rating", 1).limit(8))
        return render_template('home.html', total_data=data,
                               author_data=[row['books'] for row in data],
                               image_data=[row['img'] for row in data],
                               title_data=[row['mod_title'] for row in data],
                               rating_data=[row['rating'] for row in data],
                               genre_data=[row['mod_title'] for row in data])
    except Exception as e:
        logging.error(f"Error in home route: {e}")
        return "Internal Server Error", 500

@app.route('/recommend', methods=['GET', 'POST'])
def recommend():
    data = []
    error = False
    if request.method == 'POST':
        title_input = request.form.get('title_input', 'None').strip()
        logging.info(f"Title input: {title_input}")

        def recommend_fun(book):
            recommended_books = []
            try:
                book_index = new_df[new_df['mod_title'] == book].index[0]
                distances = similar[book_index]
                book_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

                for i in book_list:
                    recommended_books.append([
                        new_df.iloc[i[0]].mod_title,
                        new_df.iloc[i[0]].img,
                        new_df.iloc[i[0]].rating,
                        new_df.iloc[i[0]].books
                    ])
                return recommended_books

            except (IndexError, KeyError) as e:
                logging.error(f"Exception in recommend_fun: {e}")
                return None

        if not new_df.empty:
            data = recommend_fun(title_input)
            logging.info(f"Recommendation data: {data}")
        else:
            logging.error("Dataframe is empty, cannot perform recommendation.")

        if data is None:
            error = True

    return render_template('recommend.html', data=data, error=error)

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        try:
            feedback_collection.insert_one({
                'title': request.form['title'],
                'author': request.form['author'],
                'genre': request.form['genre'],
                'img_url': request.form['img-url'],
                'rating': request.form['rating']
            })
            logging.info("Feedback successfully submitted")
            return redirect(url_for('home'))
        except Exception as e:
            logging.error(f"Error submitting feedback: {e}")
            return "Internal Server Error", 500

    return render_template('feedback.html')

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))  # Use PORT environment variable if available
    app.run(debug=True, host='0.0.0.0', port=port)
