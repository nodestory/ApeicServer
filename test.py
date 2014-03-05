import requests

if __name__ == "__main__":
	url = 'http://140.112.170.196:8000/upload_log'
	files = {'file': open('temp.log', 'rb')}
	r = requests.post(url, files=files)
	print r.text
