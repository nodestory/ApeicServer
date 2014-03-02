import sqlite3
from flask import Flask, g, request

app = Flask(__name__)
app.config.from_object('config.DevelopmentConfig')

@app.before_request
def before_request():
    g.db = sqlite3.connect(app.config['DATABASE'])

@app.after_request
def after_request(response):
    g.db.close()
    return response

@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/<uuid>/upload_log', methods=['POST'])
def upload_file(uuid):
	file = request.files['file']
	if file:
		for line in file.stream.readlines():
			values = line.replace('\n', '').split(';;')
			cmd = 'INSERT INTO app_usage_logs VALUES (null, "%s", "%s", "%s", "%s", "%s", "%s");' % \
				(uuid, values[0], values[1], values[2], values[4], values[6])
			g.db.execute(cmd)
		g.db.commit()
	return '200'

@app.route('/upload_log', methods=['POST'])
def test_uploading_file():
	for att in request.files:
		print att
	# file = request.files['file']
	# if file:
	# 	save_file(file)
	return '200'


import os
from werkzeug.utils import secure_filename
def save_file(file):
	filename = secure_filename(file.filename)
	file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))


if __name__ == '__main__':
	# 0.0.0.0
	# 140.112.42.22
	app.run(host='192.168.17.230', port=8080)