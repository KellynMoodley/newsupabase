import os
import ast
from dotenv import load_dotenv
from apiflask import APIFlask, Schema, HTTPTokenAuth, abort
from apiflask.fields import Integer, String, DateTime
from supabase import create_client, Client
from flask import jsonify
import html

# Set how this API should be titled and the current version
API_TITLE = 'Call Logs API for Watson Assistant'
API_VERSION = '1.0.1'

# create the app
app = APIFlask(__name__, title=API_TITLE, version=API_VERSION)

# load .env if present
load_dotenv()

# Load Supabase URL and API Key from environment variables
#SUPABASE_URL = os.getenv("SUPABASE_URL")
#SUPABASE_KEY = os.getenv("SUPABASE_KEY")

SUPABASE_URL='https://azaciowvtzpbudilmvqz.supabase.co'
SUPABASE_KEY='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF6YWNpb3d2dHpwYnVkaWxtdnF6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzMxMzM4MDIsImV4cCI6MjA0ODcwOTgwMn0.v4AVDi4Zk_obPeMygY-ODbvOI8tW7VV-o8V1T2WiNOI'


if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Missing Supabase URL or Key in .env")
else:
    # Create the Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# the secret API key
API_TOKEN = "{{'{0}':'appuser'}}".format(os.getenv('API_TOKEN'))
# Convert to dict
tokens = ast.literal_eval(API_TOKEN)

# optional table arguments, e.g., to set another table schema
ENV_TABLE_ARGS = os.getenv('TABLE_ARGS')
TABLE_ARGS = None
if ENV_TABLE_ARGS:
    TABLE_ARGS = ast.literal_eval(ENV_TABLE_ARGS)

# specify a generic SERVERS scheme for OpenAPI to allow both local testing
# and deployment on Code Engine with configuration within Watson Assistant
app.config['SERVERS'] = [
    {
        'description': 'Code Engine deployment',
        'url': 'https://{appname}.{projectid}.{region}.codeengine.appdomain.cloud',
        'variables': {
            "appname": {
                "default": "myapp",
                "description": "application name"
            },
            "projectid": {
                "default": "projectid",
                "description": "the Code Engine project ID"
            },
            "region": {
                "default": "us-south",
                "description": "the deployment region, e.g., us-south"
            }
        }
    },
    {
        'description': 'local test',
        'url': 'http://127.0.0.1:{port}',
        'variables': {
            'port': {
                'default': "5000",
                'description': 'local port to use'
            }
        }
    }
]

# set how we want the authentication API key to be passed
auth = HTTPTokenAuth(scheme='ApiKey', header='API_TOKEN')


# Schema for Call Logs
class CallLogModel:
    def __init__(self, data):
        self.id = data.get('id')
        self.account_no = data.get('Account_no')
        self.created_at = data.get('created_at')
        self.call_type = data.get('CALLTYPE')
        self.sentiment_analysis = data.get('Sentiment analysis')
        self.audio_filename = data.get('AUDIOFILENAME2')
        self.tone = data.get('tone')
        self.transcriptions = data.get('transcriptions')

# the Python output for Call Logs
class CallLogOutSchema(Schema):
    id = Integer()
    account_no = String()
    created_at = DateTime()
    call_type = String()
    sentiment_analysis = String()
    audio_filename = String()
    tone = String()
    transcriptions = String()

# the Python input for Call Logs
class CallLogInSchema(Schema):
    account_no = String(required=True)
    call_type = String(required=True)
    sentiment_analysis = String(required=False, allow_none=True)
    audio_filename = String(required=False, allow_none=True)
    tone = String(required=False, allow_none=True)
    transcriptions = String(required=False, allow_none=True)

# register a callback to verify the token
@auth.verify_token  
def verify_token(token):
    if token in tokens:
        return tokens[token]
    else:
        return None

# Get all call logs
@app.get('/call-logs')
@app.auth_required(auth)
def get_call_logs():
    """
    Retrieve all call logs
    """
    # Fetch data from Supabase
    response = supabase.table('Truworthstable').select('*').execute()
    
    if response.status_code == 200:
        # Convert Supabase results to CallLogModel
        call_logs = [CallLogModel(item) for item in response.data]

        # Create HTML table
        table_html = "<table border='4'><tr><th>ID</th><th>Account No</th><th>Created At</th><th>Call Type</th>" \
                     "<th>Sentiment</th><th>Audio Filename</th><th>Tone</th><th>Transcriptions</th></tr>"

        for log in call_logs:
            table_html += f"<tr>" \
                          f"<td>{html.escape(str(log.id))}</td>" \
                          f"<td>{html.escape(str(log.account_no))}</td>" \
                          f"<td>{html.escape(str(log.created_at))}</td>" \
                          f"<td>{html.escape(str(log.call_type))}</td>" \
                          f"<td>{html.escape(str(log.sentiment_analysis))}</td>" \
                          f"<td>{html.escape(str(log.audio_filename))}</td>" \
                          f"<td>{html.escape(str(log.tone))}</td>" \
                          f"<td>{html.escape(str(log.transcriptions))}</td>" \
                          f"</tr>"

        table_html += "</table>"

        # Return response with table
        return jsonify({
            "table": table_html,
            "call_logs": call_logs,
            "message": "Call logs retrieved successfully"
        })
    else:
        return jsonify({
            "message": "Error retrieving data from Supabase",
            "error": response.status_code
        })

# default "homepage", also needed for health check by Code Engine
@app.get('/')
def print_default():
    """ Greeting
    health check
    """
    # returning a dict equals to use jsonify()
    return {'message': 'This is the certifications API server'}

# Main entry point
if __name__ == '__main__':
    app.run(debug=True)
