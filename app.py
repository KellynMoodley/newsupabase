import os
import ast
from dotenv import load_dotenv
from apiflask import APIFlask, Schema, HTTPTokenAuth, abort
from apiflask.fields import Integer, String, DateTime
from supabase import create_client, Client
from flask import escape
import logging
from apiflask.validators import Length, Range
from flask import abort, request, jsonify, url_for
import html


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

class AccountDetailModel:
    def __init__(self, data):
        self.account_no = data.get('Account_no')
        self.call_inum = data.get('Call_INUM')  # Added CALL_INUM field
        self.collections_segment_detail = data.get('Collections_Segment_Detail')
        self.ptp_ind = data.get('PTP_Ind')
        self.date_last_payment = data.get('Date_Last_Payment')
        self.payment_due_date = data.get('Payment_Due_Date')
        self.last_payment_amount = data.get('Last_Payment_Amount')
        self.current_balance = data.get('Current_Balance')
        self.total_amount_due = data.get('Total_amount_due')
        self.number_broken_ptp = data.get('Number_Broken_PTP')
        self.instalment = data.get('instalment')
        self.salary_day_of_month = data.get('Salary_DayofMonth')
        self.customer_bank_name = data.get('Customer_Bank_Name')
        self.store_pref_name = data.get('Store_Pref_Name')
        self.fpd_indicator = data.get('FPD_Indicator')
        self.pref_payment_method_desc = data.get('Pref_Payment_Method_Desc')
    
    def to_dict(self):
        """
        Convert AccountDetailModel to a dictionary for JSON serialization
        """
        return {
            'account_no': self.account_no,
            'call_inum': self.call_inum,  # Added to response
            'collections_segment_detail': self.collections_segment_detail,
            'ptp_ind': self.ptp_ind,
            'date_last_payment': str(self.date_last_payment) if self.date_last_payment else None,
            'payment_due_date': str(self.payment_due_date) if self.payment_due_date else None,
            'last_payment_amount': self.last_payment_amount,
            'current_balance': self.current_balance,
            'total_amount_due': self.total_amount_due,
            'number_broken_ptp': self.number_broken_ptp,
            'instalment': self.instalment,
            'salary_day_of_month': self.salary_day_of_month,
            'customer_bank_name': self.customer_bank_name,
            'store_pref_name': self.store_pref_name,
            'fpd_indicator': self.fpd_indicator,
            'pref_payment_method_desc': self.pref_payment_method_desc
        }

class CallBIModel:
    def __init__(self, data):
        self.customfield03 = data.get('CUSTOMFIELD03')  # Foreign key to CALL_INUM
        self.calltype_value = data.get('CALLTYPE_VALUE')
        self.ai_recommendations = data.get('AI_recommendations')
        self.negligence = data.get('negligence')
        self.pastcallsummary = data.get('pastcallsummary')
        self.call_strategy = data.get('call_strategy')
        self.sentiment_analysis = data.get('sentiment_analysis')
        self.tone = data.get('tone')
    
    def to_dict(self):
        """
        Convert CallBIModel to a dictionary for JSON serialization
        """
        
        return {
            'customfield03': self.customfield03,
            'calltype_value': self.calltype_value,
            'ai_recommendations': self.ai_recommendations,
            'negligence': self.negligence,
            'pastcallsummary': self.pastcallsummary,
            'call_strategy': self.call_strategy,
            'sentiment_analysis': self.sentiment_analysis,
            'tone': self.tone
        }

# New endpoint to get account details by account number
@app.get('/account-details/<account_number>')
@app.auth_required(auth)
def get_account_details(account_number):
    """
    Retrieve account details for a specific account number
    
    :param account_number: The account number to fetch details for
    :return: JSON response with account details
    """
    try:
        # Fetch account details from Supabase
        response = supabase.table('Truworthsaccountdetails') \
            .select('*') \
            .eq('Account_no', account_number) \
            .execute()
        
        try:
            data = response.data
        except AttributeError:
            data = response
        
        # Check if data is empty
        if not data:
            logging.warning(f"No account details found for account {account_number}")
            return jsonify({
                "message": f"No account details found for account {account_number}",
                "account_details": None
            }), 404
        
        # Convert to model and then to dict
        account_details = AccountDetailModel(data[0]).to_dict()
        
        return jsonify({
            "account_number": account_number,
            "account_details": account_details,
            "message": f"Account details retrieved successfully for account {account_number}"
        })
    
    except Exception as e:
        logging.error(f"An error occurred while fetching account details for account {account_number}: {str(e)}")
        return jsonify({
            "message": "An unexpected error occurred",
            "error": str(e)
        }), 500

# New endpoint to get call BI data by customfield03 (call_inum)
@app.get('/call-bi/<customfield03>')
@app.auth_required(auth)
def get_call_bi(customfield03):
    """
    Retrieve call BI data for a specific customfield03 (CALL_INUM)
    
    :param customfield03: The customfield03 value to match with CALL_INUM
    :return: JSON response with call BI data
    """
    try:
        # Fetch call BI data from Supabase
        response = supabase.table('TruworthscallBI') \
            .select('*') \
            .eq('CUSTOMFIELD03', customfield03) \
            .execute()
        
        try:
            data = response.data
        except AttributeError:
            data = response
        
        # Check if data is empty
        if not data:
            logging.warning(f"No call BI data found for customfield03 {customfield03}")
            return jsonify({
                "message": f"No call BI data found for customfield03 {customfield03}",
                "call_bi": []
            }), 404
        
        # Convert to model and then to dict
        call_bi_data = [CallBIModel(item).to_dict() for item in data]
        
        return jsonify({
            "customfield03": customfield03,
            "call_bi_data": call_bi_data,
            "message": f"Call BI data retrieved successfully for customfield03 {customfield03}"
        })
    
    except Exception as e:
        logging.error(f"An error occurred while fetching call BI data for customfield03 {customfield03}: {str(e)}")
        return jsonify({
            "message": "An unexpected error occurred",
            "error": str(e)
        }), 500


@app.get('/account-consolidated/<account_number>')
@app.auth_required(auth)
def get_account_consolidated(account_number):
    """
    Retrieve all data (account details and related call BI) for a specific account number
    using the relationship between CALL_INUM and CUSTOMFIELD03
    
    :param account_number: The account number to fetch all data for
    :return: JSON response with consolidated account data
    """
    try:
        # First get account details to find the CALL_INUM value
        account_details_response = supabase.table('Truworthsaccountdetails') \
            .select('*') \
            .eq('Account_no', account_number) \
            .execute()
            
        try:
            account_details_data = account_details_response.data
        except AttributeError:
            account_details_data = account_details_response
        
        # Check if account details exist
        if not account_details_data:
            logging.warning(f"No account details found for account {account_number}")
            return jsonify({
                "message": f"No account details found for account {account_number}",
                "account_details": None,
                "call_bi_data": []
            }), 404
            
        # Get the CALL_INUM from account details
        account_detail = AccountDetailModel(account_details_data[0])
        call_inum = account_detail.call_inum
        
        # If CALL_INUM exists, fetch related call BI data
        call_bi_data = []
        if call_inum:
            call_bi_response = supabase.table('TruworthscallBI') \
                .select('*') \
                .eq('CUSTOMFIELD03', call_inum) \
                .execute()
                
            try:
                bi_data = call_bi_response.data
            except AttributeError:
                bi_data = call_bi_response
                
            if bi_data:
                call_bi_data = [CallBIModel(item).to_dict() for item in bi_data]

        # Generate HTML table
        table_html = f"<h4 style='font-size: 16px; font-weight: bold; margin-bottom: 5px;'>AI analysis</h4>"
        table_html += "<table style='border-collapse: collapse; margin-bottom: 50px; width: 100%;'>"
        table_html += "<tr><th style='border: 1px solid pink; padding: 8px;'>Analysis type</th><th style='border: 1px solid pink; padding: 8px;'>AI outcome</th></tr>"

        # Define the fields to display
        fields = [
            ("Past Call Outcome", "calltype_value"),
            ("Past Call Summary", "pastcallsummary"),
            ("Sentiment Analysis of the last call", "sentiment_analysis"),
            ("Tone", "tone"),
            ("Current Call Strategy", "call_strategy"),
            ("AI Recommendations", "ai_recommendations"),
            ("Customer default history", "negligence")
        ]

        # Loop through each call in call_bi_data
        for call in call_bi_data:
            for field_name, field_key in fields:
                table_html += f"<tr><td style='border: 1px solid pink; padding: 8px; width: 30%;'>{field_name}</td>" \
                              f"<td style='border: 1px solid pink; padding: 8px;'>{html.escape(call[field_key])}</td></tr>"

        # Close the table
        table_html += "</table>"
        
        # Return consolidated response
        return jsonify({
            "account_number": account_number,
            "account_details": account_detail.to_dict(),
            "call_bi_data": call_bi_data,
            "call_inum": call_inum,
            "table": table_html,
            "message": f"Consolidated data retrieved successfully for account {account_number}"
        })
    
    except Exception as e:
        logging.error(f"An error occurred while fetching consolidated data for account {account_number}: {str(e)}")
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
    return {'message': 'This is the Truworths API server for call center data'}

# Main entry point
if __name__ == '__main__':
    app.run(debug=True)
