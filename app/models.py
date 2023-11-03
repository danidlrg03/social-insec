from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, id, username, first_name, last_name, password, education='Unknown', employment='Unknown', music='Unknown', movie='Unknown', nationality='Unknown', birthday='Unknown'):
        self.id = id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.password = password
        self.education = education
        self.employment = employment
        self.music = music
        self.movie = movie
        self.nationality = nationality
        self.birthday = birthday



