from flask import Flask, session, render_template, request, redirect, url_for
import os
import pandas as pd
import random as rd
from wtforms import Form, SelectField, RadioField, validators
import json
import tablib

app = Flask(__name__)
assert "APP_SETTINGS" in os.environ, "APP_SETTINGS environment variable not set"
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']

def ReadWordsCSV(cat='all'):
    Words = pd.read_csv('words.csv')
    if not cat == 'all':
        if cat == '30 random words':
            Words = Words.sample(n=30)
        elif cat == '30 random verbs':
            Words = Words[Words['Category'].str.startswith('Verbs:')].sample(n=30)
        else:
            Words = Words[Words['Category'] == cat]
        Words.reset_index(inplace=True)
    return Words

Words = ReadWordsCSV()
categories = ['30 random words','30 random verbs','Random category']+sorted(Words['Category'].unique())
catChoices = []
for c in categories:
    catChoices.append((c,c))
EngRomChoices = [('Eng2Rom','English to Romanian'),('Rom2Eng','Romanian to English')]

Words_tablib = tablib.Dataset()
with open('words.csv') as f:
    Words_tablib.csv = f.read()

class CategoriesForm(Form):
    EngRom = RadioField(choices=EngRomChoices, default='Eng2Rom', validators = [validators.Required()])
    category = SelectField(label='Category', choices=catChoices)

@app.route("/", methods=['GET', 'POST'])
def home():
    form = CategoriesForm(request.form)
    if request.method == 'POST':
        session.clear()
        cat = form.category.data
        if cat == 'Random category':
            cat = categories[rd.randrange(1,len(categories))]
        subWords = ReadWordsCSV(cat=cat)
        session['subWords'] = subWords.to_json()
        idx = list(range(len(subWords)))
        rd.shuffle(idx)
        session['nWords'] = len(subWords)
        session['nWrong'] = 0
        session['idxList'] = idx
        session['i'] = 0
        session['EngRom'] = form.EngRom.data
    else:
        if not 'i' in session:
            cat = '30 random words'
            subWords = ReadWordsCSV(cat=cat)
            session['subWords'] = subWords.to_json()
            idx = list(range(len(subWords)))
            rd.shuffle(idx)
            session['nWords'] = len(subWords)
            session['nWrong'] = 0
            session['idxList'] = idx
            session['i'] = 0
            session['EngRom'] = form.EngRom.data
    if session['i'] == len(session['idxList']):
        bFinished = True
        return render_template('main.html', form=form, bFinished=bFinished)
    else:
        bFinished = False
        subWordsJSON = json.loads(session['subWords'])
        if session['EngRom'] == 'Eng2Rom':
            Qu = subWordsJSON['English'][str(session['idxList'][session['i']])]
            Ans = subWordsJSON['Romanian'][str(session['idxList'][session['i']])]
        else:
            Qu = subWordsJSON['Romanian'][str(session['idxList'][session['i']])]
            Ans = subWordsJSON['English'][str(session['idxList'][session['i']])]
        return render_template('main.html', Qu=Qu, Ans=Ans, form=form, bFinished=bFinished)

@app.route("/next")
def next():
    if 'i' in session:
        session['i'] += 1
    return redirect(url_for("home"))

@app.route("/prev")
def prev():
    if 'i' in session and session['i'] > 0:
        session['i'] -= 1
    return redirect(url_for("home"))

@app.route("/repeat")
def repeat():
    if 'i' in session:
        session['nWrong'] += 1
        session['idxList'].append(session['idxList'][session['i']])
        session.modified = True
    return redirect(url_for("next"))

@app.route('/clear')
def clear():
    session.clear()
    return 'session cleared'

@app.route('/words')
def words():
    return Words_tablib.html

if __name__ == "__main__":
    app.run()
