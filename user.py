from priorityHierarchy import Hierarchy

class User():
    hierarchy: Hierarchy

    def __init__(self, username, password, email, name):
        self.username = username
        self.password = password
        self.name = name
        self.email = email

    def set_hierarchy(self, hierarchy):
        self.hierarchy = hierarchy



