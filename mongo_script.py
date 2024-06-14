from pymongo import MongoClient
from bson import ObjectId  # For handling ObjectId

# Replace <your_connection_string> with your MongoDB Atlas connection string
client = MongoClient("mongodb+srv://pj29102005:bTQfPPqugcyv9mv8@cluster0.9nt5ygc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client['library']  # Replace with your actual database name
feedback_collection = db['feedback']  # Replace with your actual collection name

def submit_feedback(title, author, genre, rating, img_url):
    try:
        # Insert feedback into 'feedback' collection
        result = feedback_collection.insert_one({
            'title': title,
            'author': author,
            'genre': genre,
            'rating': rating,
            'img_url': img_url
        })

        # Check if insertion was successful
        if result.inserted_id:
            print("Feedback submitted successfully.")
            return True
        else:
            print("Failed to submit feedback.")
            return False

    except Exception as e:
        print(f"Error submitting feedback: {e}")
        return False

# Example usage:
if __name__ == "__main__":
    title = "Book Title"
    author = "Author Name"
    genre = "Fiction"
    rating = 4.5
    img_url = "https://example.com/book_image.png"

    # Submit feedback
    submit_feedback(title, author, genre, rating, img_url)
