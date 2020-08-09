from app import db

class Words(db.Model):
    __tablename__ = 'words'

    id = db.Column(db.Integer, primary_key=True)
    mark = db.Column(db.Integer)
    category = db.Column(db.String())
    romanian = db.Column(db.String())
    english = db.Column(db.String())

    def __init__(self,mark,category,romanian,english):
        self.mark = mark
        self.category = category
        self.romanian = romanian
        self.english = english

    def __repr__(self):
        return '<romanian {}>'.format(self.romanian)
