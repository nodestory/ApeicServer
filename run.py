import time
from flask import Flask, abort, request
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
		illumination FLOAT, \
		mobile_connection BOOLEAN, \
		wifi_connection BOOLEAN, \
		wifi_ap_num INT, \
		battery_power FLOAT, \
		application VARCHAR(96) NOT NULL, \
		PRIMARY KEY(id));' % uuid
	db.session.execute(create_table_cmd)
	file = request.files['log_file']
	if file:
		for line in file.stream.readlines():
			values = line.replace('\n', '')
			try:
				insert_log_cmd = 'INSERT INTO %s_app_usage_logs \
					(datetime, latitude, longitude, location_acc, speed, \
						activity, activity_conf, \
						illumination, mobile_connection, wifi_connection, wifi_ap_num, \
						battery_power, application) \
					VALUES (%s);' % (uuid, values)
				db.session.execute(insert_log_cmd)
			except:
				print insert_log_cmd
		db.session.commit()
	return 'Success!'

@app.route('/<uuid>/register_app', methods=['GET'])
def register_app(uuid):
	uuid = uuid.replace('-', '_')
	app = request.args['app']
	
	try:
		create_table_cmd = 'CREATE TABLE IF NOT EXISTS %s_installed_apps(\
			id INT NOT NULL AUTO_INCREMENT, \
			application VARCHAR(96) NOT NULL, \
			start_date DATETIME, \
			end_date DATETIME, \
			PRIMARY KEY(id), \
			UNIQUE KEY(application));' % uuid
		db.session.execute(create_table_cmd)
	except:
		abort(404)
		print create_table_cmd

	try:
		insert_app_cmd = 'INSERT INTO %s_installed_apps \
			(application, start_date) VALUES ("%s", "%s");' % \
			(uuid, app, time.strftime('%Y-%m-%d %H:%M:%S'))
		db.session.execute(insert_app_cmd)
		db.session.commit()
		return request.args['app'] + " is registered!"
	except:
		print insert_app_cmd
		abort(404)

@app.route('/<uuid>/unregister_app', methods=['GET'])
def unregister_app(uuid):
	uuid = uuid.replace('-', '_')
	app = request.args['app']

	try:
		update_cmd = 'UPDATE %s_installed_apps SET end_date = "%s" \
			WHERE application = "%s"' % \
			(uuid, time.strftime('%Y-%m-%d %H:%M:%S'), app)
		db.session.execute(update_cmd)
		db.session.commit()
		return request.args['app'] + " is unregistered!"
	except:
		print update_cmd
		return request.args['app'] + "unregistration failed."


@app.route('/test_post', methods=['POST'])
def test_post():
	for att in request.files:
		print att
	return 'Success!'

import os
from werkzeug.utils import secure_filename
def save_file(file):
	filename = secure_filename(file.filename)
	file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
	
if __name__ == '__main__':
	app.run()