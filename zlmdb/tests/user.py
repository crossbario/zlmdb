class User(object):

    def __init__(self):
        self.oid = None
        self.name = None
        self.authid = None
        self.email = None
        self.birthday = None
        self.is_friendly = None
        self.tags = None
        self.ratings = {}
        self.friends = []
        self.referred_by = None
