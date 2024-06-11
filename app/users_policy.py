from flask_login import current_user


class UsersPolicy:
    def __init__(self, user):
        self.user = user

    def create(self):
        return current_user.is_admin()

    def read(self):
        return current_user.is_admin()

    def update(self):
        return current_user.is_admin()

    def delete(self):
        return current_user.is_admin()
