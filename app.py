from flask import Flask, session, render_template, request
import os
import pandas as pd
import random as rd
from wtforms import Form, SelectField

app = Flask(__name__)
assert "APP_SETTINGS" in os.environ, "APP_SETTINGS environment variable not set"
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']

def ReadWordsCSV(cat='all'):
    Words = pd.read_csv('words.csv')
    if not cat == 'all':
        Words = Words[Words['Category'] == cat]
        Words.reset_index(inplace=True)
    return Words

Words = ReadWordsCSV()
categories = Words['Category'].unique()
choices = []
for c in categories:
    choices.append((c,c))

class CategoriesForm(Form):
    category = SelectField(label='Topic', choices=choices)

@app.route("/", methods=['GET', 'POST'])
def hello():
    form = CategoriesForm(request.form)
    if request.method == 'POST':
        subWords = ReadWordsCSV(cat=form.category.data)
        session.clear()
        session['cat']=form.category.data
        idx = list(range(len(subWords)))
        rd.shuffle(idx)
        session['idxList']=idx
        session['i']=0
    else:
        if not 'idxList' in session:
            subWords = ReadWordsCSV(cat=categories[0])
            session['cat']=categories[0]
            idx = list(range(len(subWords)))
            rd.shuffle(idx)
            session['idxList']=idx
            session['i']=0
        else:
            subWords = ReadWordsCSV(cat=session['cat'])
            session['i']+=1
    if session['i']==len(subWords):
        session['i']=0
    print(subWords)
    print(session['cat'])
    print(session['idxList'])
    print(session['i'])
    Eng = subWords.loc[session['idxList'][session['i']],'English']
    Rom = subWords.loc[session['idxList'][session['i']],'Romanian']
    string = Eng+Rom
    return render_template('main.html', Eng=Eng, Rom=Rom, form=form)

#Logout
@app.route('/clear')
def clear():
    session.clear()
    return 'session cleared'

if __name__ == "__main__":
    app.run()
