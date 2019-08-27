from flask import Flask
import os
import pandas as pd
import random as rd

app = Flask(__name__)
assert "APP_SETTINGS" in os.environ, "APP_SETTINGS environment variable not set"
app.config.from_object(os.environ['APP_SETTINGS'])

def ReadWordsCSV():
    Words = pd.read_csv('words.csv')
    return Words


@app.route("/")
def hello():
    Words = ReadWordsCSV()
    idx = list(range(len(Words)))
    rd.shuffle(idx)
    Eng = Words.loc[idx[0],'English']
    Rom = Words.loc[idx[0],'Romanian']
    str = "<h1>"+Eng+"</h1><h1>"+Rom+"</h1>"
    return str

if __name__ == "__main__":
    app.run()
