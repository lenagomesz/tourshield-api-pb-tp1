"""Trusted local classifier artifact. Never deserialize user-supplied files."""
import hashlib
import io
import json
from functools import lru_cache
from pathlib import Path
import joblib
import sklearn

MODEL_DIR=Path(__file__).resolve().parents[1]/'models'


@lru_cache(maxsize=1)
def load_classifier():
    manifest=json.loads((MODEL_DIR/'manifest.json').read_text(encoding='utf-8'))
    raw=(MODEL_DIR/'intent_classifier.joblib').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=manifest['sha256']:
        raise ValueError('Model integrity check failed')
    if sklearn.__version__!=manifest['sklearn_version']:
        raise ValueError('Model dependency version mismatch')
    model=joblib.load(io.BytesIO(raw))
    if list(model.classes_)!=manifest['classes']:
        raise ValueError('Model labels mismatch')
    return model,manifest


def classify_text(text):
    model,manifest=load_classifier()
    proba=model.predict_proba([text])[0]
    index=int(proba.argmax())
    return {'intent':str(model.classes_[index]),'probability':float(proba[index]),
            'model_version':manifest['version']}
