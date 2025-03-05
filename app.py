import os
import ast
from dotenv import load_dotenv
from apiflask import APIFlask, Schema, HTTPTokenAuth, abort
from apiflask.fields import Integer, String, DateTime, List, Nested
from supabase import create_client, Client
from flask import jsonify
import html

# Set how this API should be titled and the current version
API_TITLE='Call Logs API for Watson Assistant'
API_VERSION='1.0.1'

# create the app
app = APIFlask(__name__, title=API_TITLE, version=API_VERSION)

# load .env if present
load_dotenv()

SUPABASE_URL=https://azaciowvtzpbudilmvqz.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF6YWNpb3d2dHpwYnVkaWxtdnF6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzMxMzM4MDIsImV4cCI6MjA0ODcwOTgwMn0.v4AVDi4Zk_obPeMygY-ODbvOI8tW7VV-o8V1T2WiNOI
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# the secret API key
API_TOKEN="{{'{0}':'appuser'}}".format(os.getenv('API_TOKEN'))
#convert to dict:
tokens=ast.literal_eval(API_TOKEN)

# set how we want the authentication API key to be passed
auth=HTTPTokenAuth(scheme='ApiKey', header='API_TOKEN')

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
    response = supabase.table('call_logs').select('*').execute()
    
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

# Create a new call log
@app.post('/call-logs')
@app.input(CallLogInSchema)
@app.output(CallLogOutSchema)
@app.auth_required(auth)
def create_call_log(data):
    """
    Create a new call log entry
    """
    # Insert into Supabase
    response = supabase.table('call_logs').insert(data).execute()
    
    # Return the created log
    return response.data[0]

# Get a specific call log by ID
@app.get('/call-logs/<int:log_id>')
@app.output(CallLogOutSchema)
@app.auth_required(auth)
def get_call_log(log_id):
    """
    Retrieve a specific call log by its ID
    """
    # Fetch from Supabase
    response = supabase.table('call_logs').select('*').eq('id', log_id).execute()
    
    if not response.data:
        abort(404, message="Call log not found")
    
    return response.data[0]

# Update a call log
@app.put('/call-logs/<int:log_id>')
@app.input(CallLogInSchema)
@app.output(CallLogOutSchema)
@app.auth_required(auth)
def update_call_log(log_id, data):
    """
    Update an existing call log
    """
    # Update in Supabase
    response = supabase.table('call_logs').update(data).eq('id', log_id).execute()
    
    if not response.data:
        abort(404, message="Call log not found")
    
    return response.data[0]

# Delete a call log
@app.delete('/call-logs/<int:log_id>')
@app.auth_required(auth)
def delete_call_log(log_id):
    """
    Delete a call log by its ID
    """
    # Delete from Supabase
    response = supabase.table('call_logs').delete().eq('id', log_id).execute()
    
    if not response.data:
        abort(404, message="Call log not found")
    
    return jsonify({"message": "Call log deleted successfully"})

# Main entry point
if __name__ == '__main__':
    app.run(debug=True)
