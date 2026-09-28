import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

class TagClassifier:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=500, stop_words="english")
        self.model = MultinomialNB()
        self.is_trained = False

    def train(self, texts, tags):
        X = self.vectorizer.fit_transform(texts)
        self.model.fit(X, tags)
        self.is_trained = True

    def predict(self, text: str, top_k: int = 2):
        if not self.is_trained:
            raise RuntimeError("Classifier hasn't been trained yet.")
        X = self.vectorizer.transform([text])
        probs = self.model.predict_proba(X)[0]
        ranked = sorted(zip(self.model.classes_, probs), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]

    def save(self, path="data/tag_classifier.joblib"):
        joblib.dump({"vectorizer": self.vectorizer, "model": self.model}, path)

    def load(self, path="data/tag_classifier.joblib"):
        saved = joblib.load(path)
        self.vectorizer = saved["vectorizer"]
        self.model = saved["model"]
        self.is_trained = True