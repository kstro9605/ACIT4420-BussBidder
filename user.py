from priorityHierarchy import Hierarchy

class User():
    hierarchy: Hierarchy

    def __init__(self, username, password, email, name, theme="green-light"):
        self.username = username
        self.password = password
        self.name = name
        self.email = email
        self.theme = theme

    def set_hierarchy(self, hierarchy):
        self.hierarchy = hierarchy


