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
    #site_id = db.Column(db.Integer, db.ForeignKey('paste.db_id'))

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

#
# class FacebookPost(db.model):
#     """
#     A class for the Facebook db model
#     """
#     db_id = db.Column(db.Integer, primary_key=True)
#     url = db.Column(db.Text, unique=True)
#     author = db.Column(db.Text)
#     post_date = db.Column(db.text)
#     content = db.Column(db.text)
#
#     def __repr__(self):
#         return 'Facebook Post: %r' % self.url
#
#     def jsonify(self):
#         """
#         Return a dictionary for a JSON object for the FacebookPost model
#         :return:
#         """
#         rtn = {'db_id': self.db_id, 'url': self.url, 'author': self.author, 'post_date': self.post_date,
#                'content': self.content}
#         return rtn
#
#
# class FacebookComment(db.model):
#     """
#     A class for the Facebook db model
#     """
#     db_id = db.Column(db.Integer, primary_key=True)
#     url = db.Column(db.Text, unique=True)
#     author = db.Column(db.Text)
#     post_date = db.Column(db.Text)
#     content = db.Column(db.Text)
#     parent_post = db.Column(db.Text)
#
#     def __repr__(self):
#         return 'Facebook Post: %r' % self.url
#
#     def jsonify(self):
#         """
#         Return a dictionary for a JSON object for the FacebookPost model
#         :return:
#         """
#         rtn = {'db_id': self.db_id, 'url': self.url, 'author': self.author, 'post_date': self.post_date,
#                'content': self.content}
#         return rtn
