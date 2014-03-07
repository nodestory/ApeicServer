import sqlite3
from flask import Flask, request
from flask.ext.sqlalchemy import SQLAlchemy
from werkzeug.contrib.fixers import ProxyFix

app = Flask(__name__)
app.config.from_object('config.DevelopmentConfig')
app.wsgi_app = ProxyFix(app.wsgi_app)    

db = SQLAlchemy(app)
    
@app.before_request
def before_request():
	pass

@app.after_request
def after_request(response):
	return response

@app.route('/')
def hello_world():
    return 'Hello World!'



@app.route('/<uuid>/upload_log', methods=['POST'])
def upload_file(uuid):
	uuid = uuid.replace('-', '_')
	create_table_cmd = 'CREATE TABLE IF NOT EXISTS %s_app_usage_logs(\
		id INT NOT NULL AUTO_INCREMENT, \
		datetime DATETIME NOT NULL, \
		latitude DOUBLE, \
		longitude DOUBLE, \
		location_acc FLOAT, \
		speed FLOAT, \
		activity VARCHAR(12), \
		activity_conf INT, \
		application VARCHAR(96) NOT NULL, \
		PRIMARY KEY(id));' % uuid
	db.session.execute(create_table_cmd)
	file = request.files['log_file']
	if file:
		for line in file.stream.readlines()[82:]:
			values = line.replace('\n', '')
			try:
				insert_log_cmd = 'INSERT INTO %s_app_usage_logs \
					(datetime, latitude, longitude, location_acc, speed, activity, activity_conf, application) \
					VALUES (%s);' % (uuid, values)
				db.session.execute(insert_log_cmd)
			except:
				print insert_log_cmd
		db.session.commit()
	return 'Success!'

@app.route('/upload_log', methods=['POST'])
def test_uploading_file():
	for att in request.files:
		print att
	return 'Success!'

@app.route('/read_logs', methods=['GET'])
def test_reading_logs():
	logs = db.session.execute('select distinct application from app_usage_logs')
	return ' '.join(log[0] for log in logs)

import os
from werkzeug.utils import secure_filename
def save_file(file):
	filename = secure_filename(file.filename)
	file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
	
if __name__ == '__main__':
	app.run()