import requests
import json
import time
from datetime import datetime

# Base URL - Update this with deployed URL
BASE_URL = "http://localhost:5000"

class Colors:
    """ANSI color codes for better output formatting"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ {message}{Colors.END}")

def print_header(message):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{message}{Colors.END}")
    print("=" * len(message))

def test_connection():
    """Test if the API server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return True
        return False
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to API server. Make sure the Flask app is running.")
        print("  Run: python app.py")
        return False
    except Exception as e:
        print_error(f"Connection error: {e}")
        return False

def test_welcome_endpoint():
    """Test the welcome endpoint"""
    print_header("Testing Welcome Endpoint")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print_success("Welcome endpoint working")
            print_info(f"API Version: {data.get('version', 'Unknown')}")
            print_info(f"Available endpoints: {len(data.get('api_endpoints', []))}")
            return True
        else:
            print_error(f"Welcome endpoint failed - Status: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error testing welcome endpoint: {e}")
        return False

def test_health_check():
    """Test the health check endpoint"""
    print_header("Testing Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print_success("Health check passed")
            print_info(f"Database status: {data.get('database', 'unknown')}")
            print_info(f"Timestamp: {data.get('timestamp', 'unknown')}")
            return True
        else:
            print_error(f"Health check failed - Status: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error in health check: {e}")
        return False

def clear_test_data():
    """Clear all test data before starting tests"""
    print_header("Clearing Test Data")
    try:
        response = requests.delete(f"{BASE_URL}/clear-data", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Cleared {data.get('deleted_count', 0)} expenses")
            return True
        else:
            print_warning("Could not clear data, continuing with existing data")
            return False
    except Exception as e:
        print_warning(f"Error clearing data: {e}")
        return False

def test_equal_split_expenses():
    """Test adding expenses with equal split (default behavior)"""
    print_header("Testing Equal Split Expenses")
    
    expenses = [
        {"amount": 600, "description": "Dinner at restaurant", "paid_by": "Shantanu"},
        {"amount": 450, "description": "Groceries", "paid_by": "Sanket"},
        {"amount": 300, "description": "Petrol", "paid_by": "Om"},
        {"amount": 500, "description": "Movie Tickets", "paid_by": "Shantanu"},
        {"amount": 280, "description": "Pizza", "paid_by": "Sanket"}
    ]
    
    expense_ids = []
    for expense in expenses:
        try:
            response = requests.post(f"{BASE_URL}/expenses", json=expense, timeout=10)
            if response.status_code == 201:
                data = response.json()
                expense_ids.append(data['data']['_id'])
                print_success(f"Added: {expense['description']} - ₹{expense['amount']} (paid by {expense['paid_by']})")
            else:
                print_error(f"Failed to add: {expense['description']}")
                print(f"  Status: {response.status_code}")
                print(f"  Response: {response.text}")
        except Exception as e:
            print_error(f"Error adding {expense['description']}: {e}")
    
    return expense_ids

def test_percentage_split_expenses():
    """Test adding expenses with percentage split"""
    print_header("Testing Percentage Split Expenses")
    
    expense = {
        "amount": 1200,
        "description": "Weekend Trip - Hotel",
        "paid_by": "Shantanu",
        "split_type": "percentage",
        "participants": [
            {"person": "Shantanu", "percentage": 40},
            {"person": "Sanket", "percentage": 35},
            {"person": "Om", "percentage": 25}
        ]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/expenses", json=expense, timeout=10)
        if response.status_code == 201:
            data = response.json()
            print_success(f"Added percentage split: {expense['description']} - ₹{expense['amount']}")
            print_info("Split: Shantanu 40%, Sanket 35%, Om 25%")
            return data['data']['_id']
        else:
            print_error(f"Failed to add percentage split expense")
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Error adding percentage split expense: {e}")
        return None

def test_exact_split_expenses():
    """Test adding expenses with exact amount split"""
    print_header("Testing Exact Split Expenses")
    
    expense = {
        "amount": 750,
        "description": "Shopping - Different items",
        "paid_by": "Om",
        "split_type": "exact",
        "participants": [
            {"person": "Shantanu", "amount": 300},
            {"person": "Sanket", "amount": 250},
            {"person": "Om", "amount": 200}
        ]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/expenses", json=expense, timeout=10)
        if response.status_code == 201:
            data = response.json()
            print_success(f"Added exact split: {expense['description']} - ₹{expense['amount']}")
            print_info("Split: Shantanu ₹300, Sanket ₹250, Om ₹200")
            return data['data']['_id']
        else:
            print_error(f"Failed to add exact split expense")
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Error adding exact split expense: {e}")
        return None

def test_shares_split_expenses():
    """Test adding expenses with shares split"""
    print_header("Testing Shares Split Expenses")
    
    expense = {
        "amount": 900,
        "description": "Group Project - Equipment",
        "paid_by": "Sanket",
        "split_type": "shares",
        "participants": [
            {"person": "Shantanu", "shares": 3},
            {"person": "Sanket", "shares": 2},
            {"person": "Om", "shares": 1}
        ]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/expenses", json=expense, timeout=10)
        if response.status_code == 201:
            data = response.json()
            print_success(f"Added shares split: {expense['description']} - ₹{expense['amount']}")
            print_info("Split: Shantanu 3 shares, Sanket 2 shares, Om 1 share")
            return data['data']['_id']
        else:
            print_error(f"Failed to add shares split expense")
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Error adding shares split expense: {e}")
        return None

def test_validation_errors():
    """Test various validation scenarios"""
    print_header("Testing Validation & Error Handling")
    
    test_cases = [
        {
            "name": "Missing required fields",
            "data": {"amount": 100},
            "expected_status": 400
        },
        {
            "name": "Negative amount",
            "data": {"amount": -100, "description": "Test", "paid_by": "Test"},
            "expected_status": 400
        },
        {
            "name": "Empty description",
            "data": {"amount": 100, "description": "", "paid_by": "Test"},
            "expected_status": 400
        },
        {
            "name": "Empty paid_by",
            "data": {"amount": 100, "description": "Test", "paid_by": ""},
            "expected_status": 400
        },
        {
            "name": "Invalid split_type",
            "data": {"amount": 100, "description": "Test", "paid_by": "Test", "split_type": "invalid"},
            "expected_status": 400
        },
        {
            "name": "Percentage not totaling 100%",
            "data": {
                "amount": 100, "description": "Test", "paid_by": "Test",
                "split_type": "percentage",
                "participants": [
                    {"person": "A", "percentage": 50},
                    {"person": "B", "percentage": 30}
                ]
            },
            "expected_status": 400
        },
        {
            "name": "Exact amounts not matching total",
            "data": {
                "amount": 100, "description": "Test", "paid_by": "Test",
                "split_type": "exact",
                "participants": [
                    {"person": "A", "amount": 50},
                    {"person": "B", "amount": 30}
                ]
            },
            "expected_status": 400
        }
    ]
    
    passed = 0
    for test_case in test_cases:
        try:
            response = requests.post(f"{BASE_URL}/expenses", json=test_case["data"], timeout=10)
            if response.status_code == test_case["expected_status"]:
                print_success(f"Validation test passed: {test_case['name']}")
                passed += 1
            else:
                print_error(f"Validation test failed: {test_case['name']}")
                print(f"  Expected: {test_case['expected_status']}, Got: {response.status_code}")
        except Exception as e:
            print_error(f"Error in validation test '{test_case['name']}': {e}")
    
    print_info(f"Validation tests passed: {passed}/{len(test_cases)}")
    return passed == len(test_cases)

def test_get_operations():
    """Test all GET operations"""
    print_header("Testing GET Operations")
    
    # Test get all expenses
    try:
        response = requests.get(f"{BASE_URL}/expenses", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Retrieved {len(data['data'])} expenses")
            
            # Display expense summary
            for expense in data['data'][:3]:  # Show first 3 expenses
                print_info(f"  {expense['description']}: ₹{expense['amount']} by {expense['paid_by']} ({expense.get('split_type', 'equal')} split)")
        else:
            print_error(f"Failed to get expenses - Status: {response.status_code}")
    except Exception as e:
        print_error(f"Error getting expenses: {e}")
    
    # Test get people
    try:
        response = requests.get(f"{BASE_URL}/people", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print_success(f"People: {', '.join(data['data'])}")
        else:
            print_error(f"Failed to get people - Status: {response.status_code}")
    except Exception as e:
        print_error(f"Error getting people: {e}")

def test_balances():
    """Test balance calculations"""
    print_header("Testing Balance Calculations")
    try:
        response = requests.get(f"{BASE_URL}/balances", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print_success("Balance calculations:")
            balances = data['data']['balances']
            
            for person, balance in balances.items():
                net_color = Colors.GREEN if balance['net'] >= 0 else Colors.RED
                print(f"  {Colors.BOLD}{person}:{Colors.END}")
                print(f"    Paid: ₹{balance['paid']}")
                print(f"    Owes: ₹{balance['owes']}")
                print(f"    Net: {net_color}₹{balance['net']}{Colors.END}")
            
            print_info(f"Total amount: ₹{data['data']['total_amount']}")
            print_info(f"Number of people: {data['data']['num_people']}")
        else:
            print_error(f"Failed to get balances - Status: {response.status_code}")
    except Exception as e:
        print_error(f"Error getting balances: {e}")

def test_settlements():
    """Test settlement calculations"""
    print_header("Testing Settlement Calculations")
    try:
        response = requests.get(f"{BASE_URL}/settlements", timeout=10)
        if response.status_code == 200:
            data = response.json()
            settlements = data['data']
            
            if settlements:
                print_success("Settlement recommendations:")
                for settlement in settlements:
                    print(f"  {Colors.YELLOW}{settlement['from']}{Colors.END} → {Colors.GREEN}{settlement['to']}{Colors.END}: ₹{settlement['amount']}")
                print_info(f"Total settlement amount: ₹{data['total_settlement_amount']}")
            else:
                print_success("No settlements needed - everyone is balanced!")
        else:
            print_error(f"Failed to get settlements - Status: {response.status_code}")
    except Exception as e:
        print_error(f"Error getting settlements: {e}")

def test_update_operations(expense_ids):
    """Test update operations"""
    if not expense_ids:
        print_warning("No expense IDs available for update testing")
        return
    
    print_header("Testing Update Operations")
    
    # Test updating an expense
    try:
        update_data = {
            "amount": 350,
            "description": "Petrol (Updated with receipt)",
            "split_type": "percentage",
            "participants": [
                {"person": "Shantanu", "percentage": 40},
                {"person": "Sanket", "percentage": 35},
                {"person": "Om", "percentage": 25}
            ]
        }
        
        response = requests.put(f"{BASE_URL}/expenses/{expense_ids[0]}", json=update_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print_success("Updated expense successfully")
            print_info(f"New description: {data['data']['description']}")
            print_info(f"New amount: ₹{data['data']['amount']}")
            print_info(f"New split type: {data['data']['split_type']}")
        else:
            print_error(f"Failed to update expense - Status: {response.status_code}")
    except Exception as e:
        print_error(f"Error updating expense: {e}")
    
    # Test invalid expense ID
    try:
        response = requests.put(f"{BASE_URL}/expenses/invalid_id", json={"amount": 100}, timeout=10)
        if response.status_code == 400:
            print_success("Invalid ID handling works correctly")
        else:
            print_warning(f"Invalid ID test got status: {response.status_code}")
    except Exception as e:
        print_error(f"Error testing invalid ID: {e}")

def test_delete_operations(expense_ids):
    """Test delete operations"""
    if not expense_ids or len(expense_ids) < 2:
        print_warning("Not enough expense IDs available for delete testing")
        return
    
    print_header("Testing Delete Operations")
    
    # Test deleting an expense
    try:
        response = requests.delete(f"{BASE_URL}/expenses/{expense_ids[-1]}", timeout=10)
        if response.status_code == 200:
            print_success("Deleted expense successfully")
        else:
            print_error(f"Failed to delete expense - Status: {response.status_code}")
    except Exception as e:
        print_error(f"Error deleting expense: {e}")
    
    # Test deleting non-existent expense
    try:
        response = requests.delete(f"{BASE_URL}/expenses/507f1f77bcf86cd799439011", timeout=10)
        if response.status_code == 404:
            print_success("Non-existent expense handling works correctly")
        else:
            print_warning(f"Non-existent expense test got status: {response.status_code}")
    except Exception as e:
        print_error(f"Error testing non-existent expense: {e}")

def test_error_endpoints():
    """Test error handling for non-existent endpoints"""
    print_header("Testing Error Endpoints")
    
    # Test 404 endpoint
    try:
        response = requests.get(f"{BASE_URL}/nonexistent", timeout=10)
        if response.status_code == 404:
            print_success("404 error handling works correctly")
        else:
            print_warning(f"404 test got status: {response.status_code}")
    except Exception as e:
        print_error(f"Error testing 404: {e}")
    
    # Test 405 method not allowed
    try:
        response = requests.patch(f"{BASE_URL}/expenses", timeout=10)
        if response.status_code == 405:
            print_success("405 method not allowed handling works correctly")
        else:
            print_warning(f"405 test got status: {response.status_code}")
    except Exception as e:
        print_error(f"Error testing 405: {e}")

def run_comprehensive_test():
    """Run all tests in sequence"""
    print(f"{Colors.BOLD}{Colors.MAGENTA}🚀 Enhanced Split App API Testing Suite{Colors.END}")
    print(f"Base URL: {BASE_URL}")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test connection first
    if not test_connection():
        return
    
    print_success("API server is running")
    
    # Run all tests
    all_expense_ids = []
    
    # Basic endpoint tests
    test_welcome_endpoint()
    test_health_check()
    
    # Clear data for clean testing
    clear_test_data()
    
    # Test different split types
    equal_ids = test_equal_split_expenses()
    if equal_ids:
        all_expense_ids.extend(equal_ids)
    
    percentage_id = test_percentage_split_expenses()
    if percentage_id:
        all_expense_ids.append(percentage_id)
    
    exact_id = test_exact_split_expenses()
    if exact_id:
        all_expense_ids.append(exact_id)
    
    shares_id = test_shares_split_expenses()
    if shares_id:
        all_expense_ids.append(shares_id)
    
    # Test validation
    test_validation_errors()
    
    # Test GET operations
    test_get_operations()
    
    # Test calculations
    test_balances()
    test_settlements()
    
    # Test update and delete operations
    test_update_operations(all_expense_ids)
    test_delete_operations(all_expense_ids)
    
    # Test error handling
    test_error_endpoints()
    
    print_header("Test Summary")
    print_success("All tests completed!")
    print_info(f"Test finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info("Check the output above for any failed tests.")
    
    # Final balance check
    print_info("\nFinal system state:")
    test_balances()
    test_settlements()

if __name__ == "__main__":
    run_comprehensive_test()
