from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from bson import ObjectId
from datetime import datetime
import os
from werkzeug.exceptions import BadRequest
import json
from dotenv import load_dotenv
import pymongo.errors

# Load environment variables
load_dotenv(dotenv_path=".env")

app = Flask(__name__)

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    print("❌ Error: MONGO_URI not found in environment variables")
    print("Please check your .env file and make sure MONGO_URI is set")
    exit(1)

app.config["MONGO_URI"] = MONGO_URI
print(f"🔗 Connecting to MongoDB Atlas with URI: {MONGO_URI}")

try:
    # Initialize PyMongo with connectTimeoutMS and serverSelectionTimeoutMS
    mongo = PyMongo(app, connectTimeoutMS=5000, serverSelectionTimeoutMS=5000)
    
    # Explicitly get the client and database to test connection
    client = mongo.cx
    db = client.get_database()
    
    # Test the connection
    db.command('ping')
    print("✅ MongoDB Atlas connected successfully!")
    
    # Create index for better performance (optional)
    try:
        db.expenses.create_index([("created_at", -1)])
        db.expenses.create_index([("paid_by", 1)])
        print("✅ Database indexes created")
    except Exception as e:
        print(f"⚠️  Index creation warning: {e}")
        
except pymongo.errors.ConfigurationError as e:
    print(f"❌ MongoDB configuration error: {e}")
    print("Please check your MONGO_URI format")
    exit(1)
except pymongo.errors.ConnectionFailure as e:
    print(f"❌ MongoDB connection failed: {e}")
    print("Please check:")
    print("1. Your internet connection")
    print("2. MongoDB Atlas cluster is running")
    print("3. IP address is whitelisted in Atlas")
    print("4. Username and password are correct")
    exit(1)
except Exception as e:
    print(f"❌ Unexpected error connecting to MongoDB: {e}")
    exit(1)

# Helper function to serialize MongoDB documents
def serialize_doc(doc):
    if doc is None:
        return None
    if '_id' in doc:
        doc['_id'] = str(doc['_id'])
    if 'created_at' in doc:
        doc['created_at'] = doc['created_at'].isoformat()
    if 'updated_at' in doc:
        doc['updated_at'] = doc['updated_at'].isoformat()
    return doc

# Helper function to validate expense data
def validate_expense_data(data, is_update=False):
    errors = []
    
    if not is_update or 'amount' in data:
        if 'amount' not in data:
            errors.append("Amount is required")
        elif not isinstance(data.get('amount'), (int, float)) or data['amount'] <= 0:
            errors.append("Amount must be a positive number")
    
    if not is_update or 'description' in data:
        if 'description' not in data:
            errors.append("Description is required")
        elif not data.get('description', '').strip():
            errors.append("Description cannot be empty")
    
    if not is_update or 'paid_by' in data:
        if 'paid_by' not in data:
            errors.append("paid_by is required")
        elif not data.get('paid_by', '').strip():
            errors.append("paid_by cannot be empty")
    
    # Validate split_type and participants
    if not is_update or 'split_type' in data:
        split_type = data.get('split_type', 'equal')
        if split_type not in ['equal', 'percentage', 'exact', 'shares']:
            errors.append("split_type must be one of: equal, percentage, exact, shares")
    
    # Validate participants for non-equal splits
    if data.get('split_type') in ['percentage', 'exact', 'shares']:
        participants = data.get('participants', [])
        if not participants:
            errors.append("participants are required for percentage/exact/shares split")
        elif not isinstance(participants, list):
            errors.append("participants must be a list")
        else:
            # Validate participant data
            total_percentage = 0
            total_exact = 0
            total_shares = 0
            
            for participant in participants:
                if not isinstance(participant, dict):
                    errors.append("Each participant must be an object")
                    continue
                
                if 'person' not in participant:
                    errors.append("Each participant must have a 'person' field")
                    continue
                
                if data.get('split_type') == 'percentage':
                    if 'percentage' not in participant:
                        errors.append("Each participant must have a 'percentage' field for percentage split")
                    elif not isinstance(participant['percentage'], (int, float)) or participant['percentage'] <= 0:
                        errors.append("Percentage must be a positive number")
                    else:
                        total_percentage += participant['percentage']
                
                elif data.get('split_type') == 'exact':
                    if 'amount' not in participant:
                        errors.append("Each participant must have an 'amount' field for exact split")
                    elif not isinstance(participant['amount'], (int, float)) or participant['amount'] <= 0:
                        errors.append("Amount must be a positive number")
                    else:
                        total_exact += participant['amount']
                
                elif data.get('split_type') == 'shares':
                    if 'shares' not in participant:
                        errors.append("Each participant must have a 'shares' field for shares split")
                    elif not isinstance(participant['shares'], (int, float)) or participant['shares'] <= 0:
                        errors.append("Shares must be a positive number")
                    else:
                        total_shares += participant['shares']
            
            # Validate totals
            if data.get('split_type') == 'percentage' and abs(total_percentage - 100) > 0.01:
                errors.append("Total percentage must equal 100%")
            
            if data.get('split_type') == 'exact' and abs(total_exact - data.get('amount', 0)) > 0.01:
                errors.append("Sum of exact amounts must equal total expense amount")
    
    return errors

# Helper function to calculate individual amounts based on split type
def calculate_individual_amounts(expense):
    split_type = expense.get('split_type', 'equal')
    total_amount = float(expense['amount'])
    
    if split_type == 'equal':
        # Get all people involved in the expense
        all_expenses = list(mongo.db.expenses.find())
        all_people = set()
        for exp in all_expenses:
            all_people.add(exp['paid_by'])
        
        num_people = len(all_people)
        if num_people == 0:
            return {}
        
        amount_per_person = total_amount / num_people
        return {person: amount_per_person for person in all_people}
    
    elif split_type == 'percentage':
        result = {}
        for participant in expense.get('participants', []):
            person = participant['person']
            percentage = participant['percentage']
            amount = (total_amount * percentage) / 100
            result[person] = amount
        return result
    
    elif split_type == 'exact':
        result = {}
        for participant in expense.get('participants', []):
            person = participant['person']
            amount = participant['amount']
            result[person] = amount
        return result
    
    elif split_type == 'shares':
        result = {}
        total_shares = sum(p['shares'] for p in expense.get('participants', []))
        if total_shares == 0:
            return {}
        
        for participant in expense.get('participants', []):
            person = participant['person']
            shares = participant['shares']
            amount = (total_amount * shares) / total_shares
            result[person] = amount
        return result
    
    return {}

# Helper function to calculate settlements with enhanced logic
def calculate_settlements():
    try:
        expenses = list(mongo.db.expenses.find())
        
        if not expenses:
            return []
        
        # Calculate what each person owes and what they paid
        balances = {}
        
        for expense in expenses:
            paid_by = expense['paid_by']
            amount_paid = float(expense['amount'])
            
            # Initialize balance for payer
            if paid_by not in balances:
                balances[paid_by] = {'paid': 0, 'owes': 0, 'net': 0}
            
            balances[paid_by]['paid'] += amount_paid
            
            # Calculate individual amounts based on split type
            individual_amounts = calculate_individual_amounts(expense)
            
            for person, amount_owed in individual_amounts.items():
                if person not in balances:
                    balances[person] = {'paid': 0, 'owes': 0, 'net': 0}
                
                balances[person]['owes'] += amount_owed
        
        # Calculate net balances
        for person in balances:
            balances[person]['net'] = balances[person]['paid'] - balances[person]['owes']
            # Round to 2 decimal places
            balances[person]['paid'] = round(balances[person]['paid'], 2)
            balances[person]['owes'] = round(balances[person]['owes'], 2)
            balances[person]['net'] = round(balances[person]['net'], 2)
        
        # Create settlement transactions
        settlements = []
        debtors = []  # People who owe money
        creditors = []  # People who are owed money
        
        for person, balance in balances.items():
            if balance['net'] < -0.01:  # Owes money (with small tolerance for floating point)
                debtors.append({'person': person, 'amount': abs(balance['net'])})
            elif balance['net'] > 0.01:  # Is owed money
                creditors.append({'person': person, 'amount': balance['net']})
        
        # Create optimal settlements
        for debtor in debtors:
            remaining_debt = debtor['amount']
            
            for creditor in creditors:
                if remaining_debt <= 0.01:
                    break
                
                if creditor['amount'] <= 0.01:
                    continue
                
                # Calculate settlement amount
                settlement_amount = min(remaining_debt, creditor['amount'])
                
                settlements.append({
                    'from': debtor['person'],
                    'to': creditor['person'],
                    'amount': round(settlement_amount, 2)
                })
                
                remaining_debt -= settlement_amount
                creditor['amount'] -= settlement_amount
        
        return settlements
    except Exception as e:
        print(f"Error in calculate_settlements: {e}")
        return []

# Root endpoint - API welcome message
@app.route('/', methods=['GET'])
def welcome():
    return jsonify({
        'success': True,
        'message': 'Welcome to Split App API',
        'version': '1.0.0',
        'api_endpoints': [
            'GET /expenses - List all expenses',
            'POST /expenses - Add new expense',
            'PUT /expenses/:id - Update expense',
            'DELETE /expenses/:id - Delete expense',
            'GET /settlements - Get settlement summary',
            'GET /balances - Show each person\'s balance',
            'GET /people - List all people',
            'GET /health - Health check',
            'DELETE /clear-data - Clear all data (testing only)'
        ],
        'expense_split_types': {
            'equal': 'Split equally among all people',
            'percentage': 'Split by percentage (must total 100%)',
            'exact': 'Split by exact amounts (must total expense amount)',
            'shares': 'Split by shares/ratios'
        },
        'example_requests': {
            'equal_split': {
                'amount': 600,
                'description': 'Dinner at restaurant',
                'paid_by': 'Shantanu',
                'split_type': 'equal'
            },
            'percentage_split': {
                'amount': 600,
                'description': 'Dinner at restaurant',
                'paid_by': 'Shantanu',
                'split_type': 'percentage',
                'participants': [
                    {'person': 'Shantanu', 'percentage': 50},
                    {'person': 'Sanket', 'percentage': 30},
                    {'person': 'Om', 'percentage': 20}
                ]
            },
            'exact_split': {
                'amount': 600,
                'description': 'Dinner at restaurant',
                'paid_by': 'Shantanu',
                'split_type': 'exact',
                'participants': [
                    {'person': 'Shantanu', 'amount': 300},
                    {'person': 'Sanket', 'amount': 200},
                    {'person': 'Om', 'amount': 100}
                ]
            }
        }
    }), 200

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    try:
        # Test database connection
        mongo.db.command('ping')
        return jsonify({
            'success': True,
            'message': 'API is healthy',
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'API health check failed',
            'database': 'disconnected',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# API Routes
@app.route('/expenses', methods=['GET'])
def get_expenses():
    try:
        expenses = list(mongo.db.expenses.find().sort('created_at', -1))
        serialized_expenses = [serialize_doc(expense) for expense in expenses]
        
        return jsonify({
            'success': True,
            'data': serialized_expenses,
            'count': len(serialized_expenses),
            'message': f'Retrieved {len(serialized_expenses)} expenses successfully'
        }), 200
    except Exception as e:
        print(f"Error in get_expenses: {e}")
        return jsonify({
            'success': False,
            'message': f'Error retrieving expenses: {str(e)}'
        }), 500

@app.route('/expenses', methods=['POST'])
def add_expense():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        # Set default split_type if not provided
        if 'split_type' not in data:
            data['split_type'] = 'equal'
        
        # Validate data
        errors = validate_expense_data(data)
        if errors:
            return jsonify({
                'success': False,
                'message': 'Validation failed',
                'errors': errors
            }), 400
        
        # Create expense document
        expense = {
            'amount': float(data['amount']),
            'description': data['description'].strip(),
            'paid_by': data['paid_by'].strip(),
            'split_type': data.get('split_type', 'equal'),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        # Add participants if provided
        if 'participants' in data:
            expense['participants'] = data['participants']
        
        # Insert into database
        result = mongo.db.expenses.insert_one(expense)
        expense['_id'] = str(result.inserted_id)
        
        return jsonify({
            'success': True,
            'data': serialize_doc(expense),
            'message': 'Expense added successfully'
        }), 201
        
    except Exception as e:
        print(f"Error in add_expense: {e}")
        return jsonify({
            'success': False,
            'message': f'Error adding expense: {str(e)}'
        }), 500

@app.route('/expenses/<expense_id>', methods=['PUT'])
def update_expense(expense_id):
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(expense_id):
            return jsonify({
                'success': False,
                'message': 'Invalid expense ID'
            }), 400
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        # Validate data
        errors = validate_expense_data(data, is_update=True)
        if errors:
            return jsonify({
                'success': False,
                'message': 'Validation failed',
                'errors': errors
            }), 400
        
        # Prepare update data
        update_data = {'updated_at': datetime.utcnow()}
        
        if 'amount' in data:
            update_data['amount'] = float(data['amount'])
        if 'description' in data:
            update_data['description'] = data['description'].strip()
        if 'paid_by' in data:
            update_data['paid_by'] = data['paid_by'].strip()
        if 'split_type' in data:
            update_data['split_type'] = data['split_type']
        if 'participants' in data:
            update_data['participants'] = data['participants']
        
        # Update expense
        result = mongo.db.expenses.update_one(
            {'_id': ObjectId(expense_id)},
            {'$set': update_data}
        )
        
        if result.matched_count == 0:
            return jsonify({
                'success': False,
                'message': 'Expense not found'
            }), 404
        
        # Return updated expense
        updated_expense = mongo.db.expenses.find_one({'_id': ObjectId(expense_id)})
        
        return jsonify({
            'success': True,
            'data': serialize_doc(updated_expense),
            'message': 'Expense updated successfully'
        }), 200
        
    except Exception as e:
        print(f"Error in update_expense: {e}")
        return jsonify({
            'success': False,
            'message': f'Error updating expense: {str(e)}'
        }), 500

@app.route('/expenses/<expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(expense_id):
            return jsonify({
                'success': False,
                'message': 'Invalid expense ID'
            }), 400
        
        # Delete expense
        result = mongo.db.expenses.delete_one({'_id': ObjectId(expense_id)})
        
        if result.deleted_count == 0:
            return jsonify({
                'success': False,
                'message': 'Expense not found'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Expense deleted successfully'
        }), 200
        
    except Exception as e:
        print(f"Error in delete_expense: {e}")
        return jsonify({
            'success': False,
            'message': f'Error deleting expense: {str(e)}'
        }), 500

@app.route('/people', methods=['GET'])
def get_people():
    try:
        # Get unique people from expenses
        people = mongo.db.expenses.distinct('paid_by')
        
        return jsonify({
            'success': True,
            'data': sorted(people),
            'count': len(people),
            'message': f'Retrieved {len(people)} people successfully'
        }), 200
        
    except Exception as e:
        print(f"Error in get_people: {e}")
        return jsonify({
            'success': False,
            'message': f'Error retrieving people: {str(e)}'
        }), 500

@app.route('/balances', methods=['GET'])
def get_balances():
    try:
        expenses = list(mongo.db.expenses.find())
        
        if not expenses:
            return jsonify({
                'success': True,
                'data': {
                    'balances': {},
                    'total_amount': 0,
                    'summary': 'No expenses found'
                },
                'message': 'No expenses found'
            }), 200
        
        # Calculate balances with enhanced logic
        balances = {}
        total_amount = 0
        
        for expense in expenses:
            paid_by = expense['paid_by']
            amount_paid = float(expense['amount'])
            total_amount += amount_paid
            
            # Initialize balance for payer
            if paid_by not in balances:
                balances[paid_by] = {'paid': 0, 'owes': 0, 'net': 0}
            
            balances[paid_by]['paid'] += amount_paid
            
            # Calculate individual amounts based on split type
            individual_amounts = calculate_individual_amounts(expense)
            
            for person, amount_owed in individual_amounts.items():
                if person not in balances:
                    balances[person] = {'paid': 0, 'owes': 0, 'net': 0}
                
                balances[person]['owes'] += amount_owed
        
        # Calculate net balances
        for person in balances:
            balances[person]['net'] = balances[person]['paid'] - balances[person]['owes']
            # Round to 2 decimal places
            balances[person]['paid'] = round(balances[person]['paid'], 2)
            balances[person]['owes'] = round(balances[person]['owes'], 2)
            balances[person]['net'] = round(balances[person]['net'], 2)
        
        return jsonify({
            'success': True,
            'data': {
                'balances': balances,
                'total_amount': round(total_amount, 2),
                'num_people': len(balances)
            },
            'message': 'Balances calculated successfully'
        }), 200
        
    except Exception as e:
        print(f"Error in get_balances: {e}")
        return jsonify({
            'success': False,
            'message': f'Error calculating balances: {str(e)}'
        }), 500

@app.route('/settlements', methods=['GET'])
def get_settlements():
    try:
        settlements = calculate_settlements()
        
        # Calculate total settlement amount
        total_settlement = sum(settlement['amount'] for settlement in settlements)
        
        return jsonify({
            'success': True,
            'data': settlements,
            'count': len(settlements),
            'total_settlement_amount': round(total_settlement, 2),
            'message': f'Calculated {len(settlements)} settlements successfully'
        }), 200
        
    except Exception as e:
        print(f"Error in get_settlements: {e}")
        return jsonify({
            'success': False,
            'message': f'Error calculating settlements: {str(e)}'
        }), 500

# Additional utility endpoint to clear all data (for testing)
@app.route('/clear-data', methods=['DELETE'])
def clear_data():
    try:
        result = mongo.db.expenses.delete_many({})
        return jsonify({
            'success': True,
            'message': f'Cleared {result.deleted_count} expenses',
            'deleted_count': result.deleted_count
        }), 200
    except Exception as e:
        print(f"Error in clear_data: {e}")
        return jsonify({
            'success': False,
            'message': f'Error clearing data: {str(e)}'
        }), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': 'Endpoint not found',
        'available_endpoints': [
            'GET / - API welcome and documentation',
            'GET /health - Health check',
            'GET /expenses - List all expenses',
            'POST /expenses - Add new expense',
            'PUT /expenses/:id - Update expense',
            'DELETE /expenses/:id - Delete expense',
            'GET /people - List all people',
            'GET /balances - Show balances',
            'GET /settlements - Get settlements',
            'DELETE /clear-data - Clear all data'
        ]
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'success': False,
        'message': 'Method not allowed'
    }), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'message': 'Internal server error'
    }), 500

if __name__ == '__main__':
    print(f"🚀 Starting Enhanced Split App API server...")
    print(f"📊 Database: MongoDB Atlas")
    print(f"🌐 Environment: {os.getenv('FLASK_ENV', 'development')}")
    print(f"✨ Features: Equal/Percentage/Exact/Shares splitting")
    
    # Get port from environment variable for deployment
    port = int(os.environ.get('PORT', 5000))
    
    app.run(
        debug=os.getenv('FLASK_ENV') == 'development',
        host='0.0.0.0',
        port=port
    )