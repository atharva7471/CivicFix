# CivicFix 🏙️

A civic issue reporting web application built with Flask, MongoDB, and Machine Learning.

## Features
- User registration & login
- Report civic issues with description and image
- Community voting (one vote per user forever)
- MongoDB Atlas integration
- ML-based auto category detection (text)

## Tech Stack
- Frontend: HTML, CSS, JavaScript
- Backend: Flask (Python)
- Database: MongoDB Atlas
- ML: Scikit-learn (TF-IDF + Logistic Regression)

## Setup Instructions

1. Clone the repo
```bash
git clone https://github.com/yourusername/civicfix.git
cd civicfix
```

2. Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Create .env file
```bash
MONGO_URI=your_mongo_uri
FLASK_SECRET_KEY=your_secret_key
```

5. Run app
```bash
python app.py
```