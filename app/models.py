from app import db


class Paste(db.Model):
    """
    A class for the Paste db model
    """
    db_id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(240), unique=True)
    name = db.Column(db.Text, unique=False)
    content = db.Column(db.Text)
    datetime = db.Column(db.DateTime)

    def __repr__(self):
        return 'Paste: %r' % self.url

    def jsonify(self):
        """
        Return the JSON object for the Paste model. Used with Elasticsearch.

        :return: JSON
        """
        rtn = {'db_id': self.db_id, 'url': self.url, 'name': self.name, 'content': self.content,
               'datetime': self.datetime}
        return rtn
