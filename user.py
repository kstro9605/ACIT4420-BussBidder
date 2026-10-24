class User():
    def __init__(self, username, password, email, name):
        self.username = username
        self.password = password
        self.name = name
        self.email = email
        self.hierarchy = {}

    def set_hierarchy(self, hierarchy_dict):
        validate_hierarchy(hierarchy_dict)



