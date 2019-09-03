from flask import Flask, session, render_template
import os
import pandas as pd
import random as rd

app = Flask(__name__)
assert "APP_SETTINGS" in os.environ, "APP_SETTINGS environment variable not set"
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']

def ReadWordsCSV():
    Words = pd.read_csv('words.csv')
    return Words


@app.route("/")
def hello():
    Words = ReadWordsCSV()
    if not 'idxList' in session:
        idx = list(range(len(Words)))
        rd.shuffle(idx)
        session['idxList']=idx
        session['i']=0
    else:
        session['i']+=1
    if session['i']==len(Words):
        session['i']=0
    Eng = Words.loc[session['idxList'][session['i']],'English']
    Rom = Words.loc[session['idxList'][session['i']],'Romanian']
    string = Eng+Rom
    return render_template('main.html', Eng=Eng, Rom=Rom)

#Logout
@app.route('/clear')
def clear():
    session.clear()
    return 'session cleared'

if __name__ == "__main__":
    app.run()
