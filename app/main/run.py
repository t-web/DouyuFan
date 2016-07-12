from flask import Flask
from flask import render_template
from getmsg import HotRoom

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/chatmsg')
def chatmsg():
    rooms = HotRoom()
    return render_template('gift.html', hotroom=rooms, flag=0)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=4000)
