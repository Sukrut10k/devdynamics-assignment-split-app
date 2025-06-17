# Split App Backend

![Flask](https://img.shields.io/badge/Flask-2.3.3-blue)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)

A robust backend system for splitting expenses fairly among groups of people, built with Flask and MongoDB Atlas. This API handles expense management, settlement calculations, and balance tracking with multiple split types.

## Table of Contents
- [Project Overview](#project-overview)
- [Key Features](#key-features)
- [Project Structure](#project-structure)
- [Installation Guide](#installation-guide)
- [Database Setup](#mongodb-atlas-database-setup)
- [Usage Guide](#usage-guide)
- [API Documentation](#api-documentation)
- [System Workflows](#system-workflows)
- [Testing](#testing)
- [Deployment](#deployment)

## Project Overview

The Split App Backend provides a RESTful API for managing shared expenses among groups. It automatically calculates who owes whom and provides optimized settlement transactions to simplify group finances.

### Key Highlights
- **Multiple Split Types**: Equal, percentage-based, exact amounts, and shares/ratios
- **Automated Settlements**: Calculates optimal transactions to settle balances
- **Real-time Balances**: Tracks what each person has paid and owes
- **Validation & Error Handling**: Comprehensive input validation and error responses
- **MongoDB Atlas**: Cloud-based database with connection pooling and indexing

## Project Structure

```
split-app-backend/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── postman_collection.json     # API testing collection
├── test_api.py                 # Test suite
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore file
├── README.md                  # Project documentation
```

## Key Features

1. **Expense Management**
   - Create, read, update, and delete expenses
   - Detailed expense tracking with timestamps
   - Support for multiple split types

2. **Balance Tracking**
   - Real-time calculation of individual balances
   - Shows total paid, owes, and net amount per person

3. **Settlement Calculations**
   - Optimized transactions to minimize money transfers
   - Clear "who should pay whom" instructions

4. **People Management**
   - Automatic tracking of participants from expenses
   - No manual user management required

## Installation Guide

### Prerequisites
- Python 3.8+
- MongoDB Atlas account
- pip package manager

### Project Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/split-app-backend.git
   cd split-app-backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create your `.env` file:
   ```bash
   cp .env.example .env
   ```

## MongoDB Atlas Database Setup

1. Log in to your [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) account
2. Create a new cluster or use an existing one
3. Go to Database Access and create a user with read/write privileges
4. Go to Network Access and whitelist your IP (or 0.0.0.0/0 for all IPs)
5. Get your connection URI from the Connect button
6. Update `.env` with your MongoDB URI:
   ```
   MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/splitapp?retryWrites=true&w=majority
   ```

## Usage Guide

### Running the Application

Start the development server:
```bash
flask run
```

For production:
```bash
gunicorn app:app
```

The API will be available at `http://localhost:5000`

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `MONGO_URI` | MongoDB connection string | `mongodb+srv://user:pass@cluster.mongodb.net/db` |
| `FLASK_ENV` | Flask environment | `production` or `development` |
| `PORT` | Port to run the application | `5000` |

## API Documentation

### Base URL
`http://localhost:5000` (or your deployed URL)

### Endpoints

#### Expense Management
- `POST /expenses` - Add new expense
- `GET /expenses` - List all expenses
- `PUT /expenses/:id` - Update expense
- `DELETE /expenses/:id` - Delete expense

#### Settlements & Balances
- `GET /settlements` - Get optimized settlement transactions
- `GET /balances` - Show each person's balance
- `GET /people` - List all people in the system

#### Utility
- `GET /health` - Health check endpoint
- `DELETE /clear-data` - Clear all data (testing only)

For complete API documentation with examples, import the provided Postman collection.

## System Workflows

1. **Adding Expenses**
   - User submits expense with amount, description, and payer
   - System validates input and stores in database
   - Expense is immediately available for balance calculations

2. **Calculating Balances**
   - System aggregates all expenses
   - Calculates what each person has paid
   - Calculates what each person owes based on split types
   - Computes net balance for each person

3. **Generating Settlements**
   - System identifies debtors and creditors
   - Creates optimal transactions to settle balances
   - Minimizes the number of transactions needed

4. **Updating Data**
   - Any changes to expenses trigger recalculations
   - Balances and settlements are always up-to-date

## Testing

The project includes comprehensive tests:

1. Run the test suite:
   ```bash
   python test_api.py
   ```

2. Test coverage includes:
   - All API endpoints
   - Different split types
   - Error handling
   - Database operations
   - Edge cases

3. For manual testing, import the provided Postman collection.

## Deployment

### Heroku
1. Create a new Heroku app
2. Set config vars from your `.env` file
3. Push your code:
   ```bash
   git push heroku main
   ```

### Docker
1. Build the image:
   ```bash
   docker build -t split-app-backend .
   ```
2. Run the container:
   ```bash
   docker run -p 5000:5000 --env-file .env split-app-backend
   ```

## Contributing

1. Fork the project
2. Create your feature branch (`git checkout -b feature/NewFeature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/NewFeature`)
5. Open a Pull Request

## Contact

Project Maintainer - [Sukrut Kulkarni](mailto:k.sukrut1010@gmail.com)
```