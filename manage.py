from flask import Flask
from apis import init_api
import settings
from dao import init_db

app = Flask(__name__)
app.config.from_object(settings.Config)
init_api(app)

init_db(app)

if __name__ == '__main__':
    app.run()
