from flask import Flask, session, render_template, request, redirect, url_for
import os
import pandas as pd
import random as rd
from wtforms import Form, SelectField, RadioField, StringField, validators
import json
import tablib
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
assert "APP_SETTINGS" in os.environ, "APP_SETTINGS environment variable not set"
assert "SECRET_KEY" in os.environ, "SECRET_KEY environment variable not set"
assert "DATABASE_URL" in os.environ, "DATABASE_URL environment variable not set"
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

from models import Words

########## PSQL FUNCTIONS ##########
def psql_to_pandas(query):
    df = pd.read_sql(query.statement,db.session.bind)
    return df
####################################

def ReadWordsCSV(cat='all'):
    WordsCSV = pd.read_csv('words.csv')
    if not cat == 'all':
        if cat == '30 random words':
            WordsCSV = WordsCSV.sample(n=min(len(WordsCSV),30))
        elif cat == '30 marked words':
            toSample = WordsCSV[WordsCSV['Mark']==1]
            WordsCSV = toSample.sample(n=min(len(toSample),30))
        elif cat == '30 random nouns':
            toSample = WordsCSV[WordsCSV['Category'].str.startswith('Nouns:')]
            WordsCSV = toSample.sample(n=min(len(toSample),30))
        elif cat == '30 random verbs':
            toSample = WordsCSV[WordsCSV['Category'].str.startswith('Verbs:')]
            WordsCSV = toSample.sample(n=min(len(toSample),30))
        elif cat == '30 random adjectives':
            toSample = WordsCSV[WordsCSV['Category'].str.startswith('Adjectives:')]
            WordsCSV = toSample.sample(n=min(len(toSample),30))
        else:
            WordsCSV = WordsCSV[WordsCSV['Category'] == cat]
        WordsCSV.reset_index(inplace=True)
    return WordsCSV

WordsCSV = ReadWordsCSV()
categories = ['30 random words','30 marked words','30 random nouns','30 random verbs','30 random adjectives','Random category']+sorted(WordsCSV['Category'].unique())
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

class addForm(Form):
    category = StringField(label='Category', validators = [validators.Required()], render_kw={"placeholder": "Category"})
    romanian = StringField(label='Romanian', validators = [validators.Required()], render_kw={"placeholder": "Romanian"})
    english = StringField(label='English', validators = [validators.Required()], render_kw={"placeholder": "English"})

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
        Ctgry = subWordsJSON['Category'][str(session['idxList'][session['i']])]
        if session['EngRom'] == 'Eng2Rom':
            Qu = subWordsJSON['English'][str(session['idxList'][session['i']])]
            Ans = subWordsJSON['Romanian'][str(session['idxList'][session['i']])]
        else:
            Qu = subWordsJSON['Romanian'][str(session['idxList'][session['i']])]
            Ans = subWordsJSON['English'][str(session['idxList'][session['i']])]
        return render_template('main.html', Qu=Qu, Ans=Ans, form=form, Ctgry=Ctgry, bFinished=bFinished, iWord=session['i']+1,nWords=len(session['idxList']))

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

@app.route("/add",methods=['GET', 'POST'])
def add():
    form = addForm(request.form)
    if request.method == 'POST' and form.validate():
        category = request.form['category']
        romanian = request.form['romanian']
        english = request.form['english']
        word = Words(1,category,romanian,english)
        db.session.add(word)
        db.session.commit()
        return redirect(url_for('add'))
    return render_template('add.html',form=form)

@app.route('/clear')
def clear():
    session.clear()
    return 'session cleared'

@app.route('/words')
def words():
    return Words_tablib.html

@app.route('/view')
def view():
    words = psql_to_pandas(Words.query.order_by(Words.category,Words.romanian))
    return render_template("view.html", words=words)

if __name__ == "__main__":
    app.run()
