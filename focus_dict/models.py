import mongoengine as db

class Pair(db.Document):
    meta = {"db_alias":"default", 'collection':'pair'}
    index = db.IntField(required=True)
    word1 = db.StringField(required=True)
    word2 = db.StringField(required=True)
    word1_merge = db.BooleanField(default=False)
    word1_delete = db.BooleanField(default=False)
    word2_merge = db.BooleanField(default=False)
    word2_delete = db.BooleanField(default=False)

    def to_dict(self):
        d = {}
        d["index"] = self.index
        d["word1"] = self.word1
        d["word2"] = self.word2
        d["word1_merge"] = self.word1_merge
        d["word1_delete"] = self.word1_delete
        d["word2_merge"] = self.word2_merge
        d["word2_delete"] = self.word2_delete
        return d