import awslambda_wsgi
from app import app

def handler(event, context):
    return awslambda_wsgi.response(app, event, context)
