import os
import ast
from dotenv import load_dotenv
from apiflask import APIFlask, Schema, HTTPTokenAuth, abort
from apiflask.fields import Integer, String, DateTime
from supabase import create_client, Client
from flask import jsonify
import logging

# Configure the logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set how this API should be titled and the current version
API_TITLE = 'Call Logs API for Watson Assistant'
API_VERSION = '1.0.1'

# Create the app
app = APIFlask(__name__, title=API_TITLE, version=API_VERSION)

# Load .env if present
load_dotenv()

# Load Supabase URL and API Key from environment variables
SUPABASE_URL = 'https://azaciowvtzpbudilmvqz.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF6YWNpb3d2dHpwYnVkaWxtdnF6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzMxMzM4MDIsImV4cCI6MjA0ODcwOTgwMn0.v4AVDi4Zk_obPeMygY-ODbvOI8tW7VV-o8V1T2WiNOI'

if not SUPABASE_URL or not SUPABASE_KEY:
    logging.error("Error: Missing Supabase URL or Key in .env")
else:
    try:
        # Create the Supabase client
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logging.info("Supabase client created successfully")
    except Exception as e:
        logging.error(f"Error creating Supabase client: {str(e)}")

# The secret API key
API_TOKEN = "{{'{0}':'appuser'}}".format(os.getenv('API_TOKEN'))
# Convert to dict
tokens = ast.literal_eval(API_TOKEN)

# Set how we want the authentication API key to be passed
auth = HTTPTokenAuth(scheme='ApiKey', header='API_TOKEN')

# register a callback to verify the token
@auth.verify_token  
def verify_token(token):
    if token in tokens:
        return tokens[token]
    else:
        return None

# Specify a generic SERVERS scheme for OpenAPI to allow both local testing
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
    
    def to_dict(self):
        """
        Convert CallLogModel to a dictionary for JSON serialization
        """
        return {
            'id': self.id,
            'account_no': self.account_no,
            'created_at': str(self.created_at),
            'call_type': self.call_type,
            'sentiment_analysis': self.sentiment_analysis,
            'audio_filename': self.audio_filename,
            'tone': self.tone,
            'transcriptions': self.transcriptions
        }

@app.get('/call-logs')
@app.auth_required(auth)
def get_call_logs():
    """
    Retrieve all call logs
    """
    try:
        # Fetch data from Supabase
        response = supabase.table('Truworthstable').select('*').execute()
        
        # Check if response is None or doesn't have data
        if response is None:
            logging.error("No response received from Supabase")
            return jsonify({
                "message": "No data retrieved from Supabase",
                "error": "Empty response"
            }), 404
        
        # In newer versions of supabase-py, data might be accessed differently
        try:
            # First try the current method
            data = response.data
        except AttributeError:
            # If that fails, try accessing data directly
            data = response

        # Check if data is empty
        if not data:
            logging.warning("No call logs found in the database")
            return jsonify({
                "message": "No call logs found",
                "call_logs": []
            }), 404

        # Convert Supabase results to CallLogModel and then to dictionaries
        call_logs = [CallLogModel(item).to_dict() for item in data]

        # Return response with call logs
        return jsonify({
            "call_logs": call_logs,
            "message": "Call logs retrieved successfully"
        })
    
    except Exception as e:
        logging.error(f"An error occurred while fetching call logs: {str(e)}")
        return jsonify({
            "message": "An unexpected error occurred",
            "error": str(e)
        }), 500

@app.get('/')
def print_default():
    """Greeting
    Health check
    """
    # Returning a dict equals to using jsonify()
    return {'message': 'This is the certifications API server'}

# Main entry point
if __name__ == '__main__':
    app.run(debug=True)
