from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

texts = [
    "big pothole on road",
    "road damaged near bridge",
    "huge pit on street",

    "garbage dump near school",
    "trash not collected",
    "waste overflowing",

    "water leakage on road",
    "pipe broken water flowing",
    "no water supply",

    "street light not working",
    "electricity cut in area",
    "power outage at night"
]

labels = [
    "Pothole", "Pothole", "Pothole",
    "Garbage", "Garbage", "Garbage",
    "Water", "Water", "Water",
    "Electricity", "Electricity", "Electricity"
]

# Vectorizer converts text → numbers
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(texts)

# Classifier
model = LogisticRegression()
model.fit(X, labels)

def predict_category(description: str) -> str:
    X_test = vectorizer.transform([description])
    prediction = model.predict(X_test)[0]
    return prediction