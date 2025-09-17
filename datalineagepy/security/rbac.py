class Role:
    def __init__(self, name, permissions):
        self.name = name
        self.permissions = set(permissions)


class User:
    def __init__(self, username, roles):
        self.username = username
        self.roles = roles  # List of Role

    def has_permission(self, permission):
        return any(permission in role.permissions for role in self.roles)


class RBACManager:
    def __init__(self):
        self.roles = {}
        self.users = {}

    def add_role(self, name, permissions):
        self.roles[name] = Role(name, permissions)

    def add_user(self, username, role_names):
        roles = [self.roles[r] for r in role_names if r in self.roles]
        self.users[username] = User(username, roles)

    def check_access(self, username, permission):
        user = self.users.get(username)
        if not user:
            return False
        return user.has_permission(permission)
