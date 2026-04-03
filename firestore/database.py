from firebase_admin import firestore

db = firestore.client()
try:
    db.collection("devices").limit(1).get()
    print("✅ Connected to Firestore")
except Exception as e:
    print(f"Firestore connection failed: {e}")