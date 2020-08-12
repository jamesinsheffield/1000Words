from flask import Flask, session, render_template, request, redirect, url_for, abort
import os
import pandas as pd
import random as rd
from wtforms import Form, SelectField, RadioField, StringField, BooleanField, validators
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

def ReadWordsDB(cat='all'):
    wordsDB = psql_to_pandas(Words.query.order_by(Words.category,Words.romanian))
    if not cat == 'all':
        if cat == '30 random words':
            wordsDB = wordsDB.sample(n=min(len(wordsDB),30))
        elif cat == '30 marked words':
            toSample = wordsDB[wordsDB['mark']==1]
            wordsDB = toSample.sample(n=min(len(toSample),30))
        elif cat == '30 random nouns':
            toSample = wordsDB[wordsDB['category'].str.startswith('Nouns:')]
            wordsDB = toSample.sample(n=min(len(toSample),30))
        elif cat == '30 random verbs':
            toSample = wordsDB[wordsDB['category'].str.startswith('Verbs:')]
            wordsDB = toSample.sample(n=min(len(toSample),30))
        elif cat == '30 random adjectives':
            toSample = wordsDB[wordsDB['category'].str.startswith('Adjectives:')]
            wordsDB = toSample.sample(n=min(len(toSample),30))
        else:
            wordsDB = wordsDB[wordsDB['category'] == cat]
        wordsDB.reset_index(inplace=True)
    return wordsDB

wordsDF = ReadWordsDB()
categories = ['30 random words','30 marked words','30 random nouns','30 random verbs','30 random adjectives','Random category']+sorted(wordsDF['category'].unique())
catChoices = []
for c in categories:
    catChoices.append((c,c))
EngRomChoices = [('Eng2Rom','English to Romanian'),('Rom2Eng','Romanian to English')]


def getWordsCSV():
    Words_tablib = tablib.Dataset()
    with open('words.csv') as f:
        Words_tablib.csv = f.read()
    return Words_tablib

class CategoriesForm(Form):
    EngRom = RadioField(choices=EngRomChoices, default='Eng2Rom', validators = [validators.Required()])
    category = SelectField(label='Category', choices=catChoices)

class addForm(Form):
    mark = BooleanField(label='Mark?')
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
        subWords = ReadWordsDB(cat=cat)
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
            subWords = ReadWordsDB(cat=cat)
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
        Ctgry = subWordsJSON['category'][str(session['idxList'][session['i']])]
        if session['EngRom'] == 'Eng2Rom':
            Qu = subWordsJSON['english'][str(session['idxList'][session['i']])]
            Ans = subWordsJSON['romanian'][str(session['idxList'][session['i']])]
        else:
            Qu = subWordsJSON['romanian'][str(session['idxList'][session['i']])]
            Ans = subWordsJSON['english'][str(session['idxList'][session['i']])]
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
        if form.mark.data:
            mark = 1
        else:
            mark = 0
        category = form.category.data
        romanian = form.romanian.data
        english = form.english.data
        word = Words(mark,category,romanian,english)
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
    Words_tablib = getWordsCSV()
    return Words_tablib.html

@app.route('/view')
def view():
    words = psql_to_pandas(Words.query.order_by(Words.category,Words.romanian))
    return render_template("view.html", words=words)

@app.route('/delete/<string:id>', methods=['POST'])
def delete(id):
    #Retrieve DB entry:
    db_row = Words.query.filter_by(id=id).first()
    if db_row is None:
        abort(404)
    #Delete from DB:
    db.session.delete(db_row)
    db.session.commit()
    return redirect(url_for('view'))

@app.route('/edit/<string:id>', methods=['GET','POST'])
def edit(id):
    #Retrieve DB entry:
    db_row = Words.query.filter_by(id=id).first()
    if db_row is None:
        abort(404)
    #Get form (and tweak where necessary):
    form = addForm(request.form)
    #If user submits edit entry form:
    if request.method == 'POST' and form.validate():
        if form.mark.data:
            db_row.mark = 1
        else:
            db_row.mark = 0
        db_row.category = form.category.data
        db_row.romanian = form.romanian.data
        db_row.english = form.english.data
        db.session.commit()
        #Return:
        return redirect(url_for('view'))
    #Pre-populate form fields with existing data:
    if not request.method == 'POST':
        if db_row.mark == 1:
            form.mark.data = True
        else:
            form.mark.data = 0
        form.category.data = db_row.category
        form.romanian.data = db_row.romanian
        form.english.data = db_row.english
    return render_template('edit.html',id=id,form=form)

if __name__ == "__main__":
    app.run()
