import pandas as pd
from .collector import deduplicate

def import_csv(file):
    df = pd.read_csv(file)
    return deduplicate(df.fillna("").to_dict("records"))

def import_excel(file):
    df = pd.read_excel(file)
    return deduplicate(df.fillna("").to_dict("records"))
