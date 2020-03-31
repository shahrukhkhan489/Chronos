import os
from flask import Flask
from flask_migrate import Migrate, MigrateCommand
from flask_script import Command, Manager
from flask_sqlalchemy import SQLAlchemy
from chronos.libs import tools

config = tools.get_config()
log = tools.create_log()
log.setLevel(20)
log.setLevel(config.getint('logging', 'level'))

app = Flask(__name__, template_folder="chronos/templates", static_folder="chronos/static")
if config.has_option('postgresql', 'host') and config.has_option('postgresql', 'database') and config.has_option('postgresql', 'user') and config.has_option('postgresql', 'password'):
    uri = 'postgresql://{}:{}@{}/{}'.format(config.get('postgresql', 'user'), config.get('postgresql', 'password'), config.get('postgresql', 'host'), config.get('postgresql', 'database'))
    app.config['SQLALCHEMY_DATABASE_URI'] = uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)
log.info("test")

# Setup jinja2
# print(os.path.join(os.path.dirname(__file__), "static"))
# loader = jinja2.FileSystemLoader(
#         [os.path.join(os.path.dirname(__file__), "static"),
#          os.path.join(os.path.dirname(__file__), "templates")])
# environment = jinja2.Environment(loader=loader)


class Update(Command):
    def run(self):
        os.system('python model.py db migrate')
        os.system('python model.py db upgrade')


if __name__ == '__main__':
    manager.add_command('update', Update())
    manager.run()