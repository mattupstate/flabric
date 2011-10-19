from flask import Flask, render_template
from application import middleware, logging

app = Flask(__name__)
app.config.from_object('application.config')

try: app.config.from_object('instance.config')
except: pass

middleware.init(app)
logging.init(app)

@app.route('/')
def index():
    return render_template('index.html')
