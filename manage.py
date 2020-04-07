"""
This file is here to be able to do updates to the database without reverting to DROP TABLE, i.e. to use Flask-Migrate
"""
from chronos import create_app

app = create_app()
if __name__ == '__main__':
    from chronos import model
    model.manage()


def run():
    app.run()
