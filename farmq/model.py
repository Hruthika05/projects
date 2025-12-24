import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from preprocess import clean_text

# 1. Load dataset
df = pd.read_csv("Agri dataset.csv")

# Clean queries
df['Questions'] = df['Questions'].astype(str).apply(clean_text)

X = df['Questions']
y = df['Label']

# 2. Vectorize
vectorizer = TfidfVectorizer(ngram_range=(1,2))
X_vec = vectorizer.fit_transform(X)

# 3. Train-test split
X_train, X_test, y_train, y_test = train_test_split(X_vec, y, test_size=0.2, random_state=42)

# 4. Train model
model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)

# 5. Evaluate
y_pred = model.predict(X_test)
print(classification_report(y_test, y_pred))

# 6. Save model and vectorizer
joblib.dump(model, "domain_model.pkl")
joblib.dump(vectorizer, "vectorizer.pkl")

print("✅ Model training complete. Files saved: domain_model.pkl, vectorizer.pkl")
