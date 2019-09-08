from flask import Flask, session, render_template, request, redirect, url_for
import os
import pandas as pd
import random as rd
from wtforms import Form, SelectField, RadioField, validators

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
catChoices = []
for c in categories:
    catChoices.append((c,c))
EngRomChoices = [('Eng2Rom','English to Romanian'),('Rom2Eng','Romanian to English')]

class CategoriesForm(Form):
    EngRom = RadioField(choices=EngRomChoices, default='Eng2Rom', validators = [validators.Required()])
    category = SelectField(label='Category', choices=catChoices)

@app.route("/", methods=['GET', 'POST'])
def home():
    form = CategoriesForm(request.form)
    if request.method == 'POST':
        subWords = ReadWordsCSV(cat=form.category.data)
        session.clear()
        session['cat'] = form.category.data
        idx = list(range(len(subWords)))
        rd.shuffle(idx)
        session['idxList'] = idx
        session['i'] = 0
        session['EngRom'] = form.EngRom.data
    else:
        if not 'i' in session:
            subWords = ReadWordsCSV(cat=categories[0])
            session['cat'] = categories[0]
            idx = list(range(len(subWords)))
            rd.shuffle(idx)
            session['idxList'] = idx
            session['i'] = 0
            session['EngRom'] = form.EngRom.data
        else:
            subWords = ReadWordsCSV(cat=session['cat'])
    if session['EngRom'] == 'Eng2Rom':
        Qu = subWords.loc[session['idxList'][session['i']],'English']
        Ans = subWords.loc[session['idxList'][session['i']],'Romanian']
    else:
        Qu = subWords.loc[session['idxList'][session['i']],'Romanian']
        Ans = subWords.loc[session['idxList'][session['i']],'English']
    return render_template('main.html', Qu=Qu, Ans=Ans, form=form)

@app.route("/next")
def next():
    if 'i' in session and session['i'] < len(session['idxList'])-1:
        session['i'] += 1
    return redirect(url_for("home"))

@app.route("/prev")
def prev():
    if 'i' in session and session['i'] > 0:
        session['i'] -= 1
    return redirect(url_for("home"))

@app.route("/repeat")
def repeat():
    if 'idxList' in session:
        session['idxList'].append(session['idxList'][session['i']])
        session.modified = True
    return redirect(url_for("home"))

@app.route('/clear')
def clear():
    session.clear()
    return 'session cleared'

if __name__ == "__main__":
    app.run()
