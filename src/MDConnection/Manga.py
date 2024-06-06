class Manga:
    # holds info for specific manga
    
    __slots__ = {'id', 'mean', 'bayesian', 'follows', 'chapters'}
    
    def __init__(self, attr):
        self.id = attr.get('id')                # str
        self.mean = attr.get('mean')            # double
        self.bayesian = attr.get('bayesian')    # double
        self.follows = attr.get('follows')      # int
        self.chapters = attr.get('chapters')    # dict {int : Chapter object}