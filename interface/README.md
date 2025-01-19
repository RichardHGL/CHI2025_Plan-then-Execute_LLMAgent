# interface
This folder contains all code associated with our interfaces used in our experiments. If you create one github repo with all code in this folder, you should be able to deploy our interfaces with [Render](https://render.com/).

To achieve that, you can get an instance of database and instance for web server (flask).
Render provides a clear [instruction](https://render.com/docs/deploy-flask) to set it up.

Build Command:
`pip install -r requirements_new.txt`

start command:
gunicorn wsgi:app