class Chapter:
    
    __slots__ = {'id', 'len', 'title', 'manga', 'publish_date', 'upload_date', 
                 'group', 'pages'}
    
    def __init__(self, attr):
        self.id = attr.get('id')                        # str
        self.title = attr.get('title')                  # str
        self.manga = attr.get('manga')                  # Manga object
        self.publish_date = attr.get('publish_date')    # str (time)
        self.upload_date = attr.get('upload_date')      # str (time)
        self.group = attr.get('group')                  # Group object
        self.pages = attr.get('pages')                  # dict {int : image... somehow}
        self.len = self.pages.len()