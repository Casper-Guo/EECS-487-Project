"""Maestro Flask Server."""
from logging.config import dictConfig
import flask
from ml import frontend
from ml import db


# For debug puropses
dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})



"""Flask initialization."""
app = flask.Flask(__name__)

app.secret_key = b'\x84\xa1+\xd5\x16\xcf\xf6\xe2lz!\xb0\xd1W' \
    b'\xc9\xd3\xba\x1c(\xdd|\xbf<\xea'



"""Temporary helper functions."""
def add_user(username, client):
    return username



def save_answers(sentence_id, answers):
    app.logger.debug(f'Sentence ID: {sentence_id}')
    app.logger.debug(f'Answers: {answers}')



"""Begin routes."""
@app.route('/api/')
@app.route('/api/v1/')
def endpoints():
    """Return list of REST API endpoints."""
    context = {
        'endpoints': '/api/v1/',
        'login': 'api/v1/login/',
        'cards': '/api/v1/cards/'
    }

    return flask.jsonify(**context)


@app.route('/api/v1/login/', methods=['POST'])
def login():
    username = flask.request.json['username']

    flask.session['username'] = username
    flask.session['pending'] = False
    flask.session['done'] = False

    # for testing
    # flask.session['cards'] = [
    #     None,
    #     (1, '¡Recicla las botellas!', 'Recycle the bottles!', 'https://cdn-empjn.nitrocdn.com/XwyHQmqXQgQUrbJbUwDmDtDbdvcYyuWY/assets/static/optimized/rev-68c4a69/wp-content/uploads/2021/09/recycle-distillata-bottle-1024x1024.jpeg'),
    #     (0, 'Desayuné una manzana.', 'I ate an apple for breakfast', 'https://static4.depositphotos.com/1011434/507/i/950/depositphotos_5072980-stock-photo-eating-an-apple.jpg')
    # ]

    user_id = frontend.add_user(username, db.client)

    if user_id == -1:
        return flask.Response('Error occurred while logging in or creating user', 500)
    app.logger.debug(user_id)


    flask.session['user_id'] = user_id
    flask.session['pending'] = False
    return flask.Response('', 200)


@app.route('/api/v1/cards/', methods=['GET'])
def send_card():
    """Sends new card information to the client."""
    if flask.session['done'] or flask.session['pending']:
        return flask.jsonify(flask.session['current_card'])
    flask.session['pending'] = True

    card = frontend.get_next_card(flask.session['user_id'])
    app.logger.debug(card)

    # no more cards remain
    if not card:
        flask.session['done'] = True
        return flask.jsonify(**{'done': True})

    context = {
        'sentence_id': card[0],
        'sentence': card[1].split(),
        'translated_sentence': card[2].split(),
        'img_url': card[3]
    }
    flask.session['current_card'] = context

    return flask.jsonify(**context)


@app.route('/api/v1/cards/', methods=['POST'])
def save_result():
    if flask.session['done'] or not flask.session['pending']:
        return flask.Response('', 200)

    flask.session['pending'] = False

    # ???: confirm answers format
    sentence_id = flask.session['current_card']['sentence_id']
    scores = flask.request.json['scores']
    answers = [(score, True) for score in scores]

    frontend.save_answers(sentence_id, answers)

    return flask.Response('', 200)


"""Flask run."""
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
