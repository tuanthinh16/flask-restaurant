# Restaurant Management System

## Overview
A comprehensive Flask-based restaurant management system that handles menu, reservations, orders, inventory, users, and administrative functions.
Use database with Mysql, running with docker-compose
Translate to target lang when GET methods
Cache data for menu,table time out 300
Limit 10 reqest per minute

## Features
- **Menu Management**: Add, edit, delete dishes
- **Table Management**: Book, cancel, and track table status
- **Order Processing**: Create and manage orders
- **Inventory Control**: Track ingredients and stock levels
- **User System**: Manage staff accounts and permissions
- **Transaction History**: Log inventory changes and key events
- **Reporting**: Generate revenue, order, and inventory reports

## Installation
```bash
git clone https://github.com/your-username/restaurant-management.git
cd restaurant-management
pip install -r requirements.txt
```
### Environment Setup
Create a secret_key.txt file with:
``` bash
thinhvipnghean #your secret key
```
Running the Application
```bash
flask run
```

## API Endpoints
- **Optional Body**: GET: limit, start, target-lang 
- **Token Required**:  POST,PUT,DELETE methods
### Login Service
    POST    /login              Body json {"username":"admin","password":"provip"}      Jwt token
### Menu Management
    Method	                    Endpoint	                    Description	Request/Response Example
    GET	    /api/menu	        Get all menu items	            Query Params: ?target_lang=en&limit=10
    POST    /api/menu	        Add a new dish	                Body: {name, price, description, image} (Token required)
    PUT	    /api/menu/{id}	    Update a dish	                Body: {name, price (optional), ...} (Token required)
    DELETE	/api/menu/{id}	    Delete a dish	                204 No Content  (Token required)
### Table Reservations
    Method	                    Endpoint	                    Description	Request/Response Example
    GET	    /api/tables	        List all tables	                Response:   [{id, table_number, capacity}] 
    POST    /api/tables	        Add a new table	                Body: {table_number, capacity}  (Token required)
    PUT	    /api/tables/{id}	Update table (e.g., capacity)	Body: {capacity: 6} (Token required)
    DELETE	/api/tables/{id}	Remove a table	                204 No Content  (Token required) 
### Order Processing
    Method	                    Endpoint	                    Description	Request/Response Example
    GET	    /api/orders	        List all orders	                Response: [{id, table_id, status, ...}]
    POST	/api/orders	        Create an order	                Body: {table_id, items: [{menu_item_id, quantity}]}
    PUT	    /api/orders/{id}	Update order status	            Body: {status: "completed"}
### Order Item Management
    Method	                         Endpoint	                Description	Request/Response Example
    GET     /api/order-items         Get orderitem              Response Object
    POST    /api/order-items         Add new                    201 Object
    PUT     /api/order-items/{id}    Update                     200 Object
    DELETE  /api/order-items/{id}    Delete                     200
### Inventory Management
    Method	                    Endpoint	                    Description	Request/Response Example
    GET	    /api/inventory	    List all inventory items	    Response: [{id, item_name, quantity}]
    POST	/api/inventory	    Add new inventory item	        Body: {item_name, quantity, unit}
    PUT	    /api/inventory/{id}	Update stock quantity	        Body: {quantity: 150}
    DELETE	/api/inventory/{id}	Remove item from inventory	    204 No Content
### Inventory Log Management
    Method	                            Endpoint	            Description	Parameters/Request Body	                 
    GET	     /api/inventory-logs	    Get all inventory logs	Response : [{id, creator, inventory_id...}]
    POST     /api/inventory-logs	    Create new inventorylog {Object}	201 Created
    POST/PUT /api/inventory-logs/approval/{id}	Approve 	    id (path parameter)	200 OK
### User Management
    Method	                    Endpoint	                    Description	Request/Response Example
    GET	    /api/users	        List all users	                Response: [{id, username, role}]
    POST	/api/users	        Create a user	                Body: {username, password, role}
    PUT	    /api/users/{id}	    Update user role	            Body: {role: "admin"}
    DELETE	/api/users/{id}	    Delete a user	                204 No Content
### Reservations Management
    Method	                                Endpoint	        Description	Request/Response Example
    GET	    /api/reservations	            List all users	    Response: Object
    POST	/api/reservations	            Create a user	    Body: Object
    PUT	    /api/reservations/{id}	        Update user role	Body: Object
    DELETE	/api/reservations/{id}	        Delete a user	    204 No Content
    POST    /api/reservations/approval/{id} Approval            200 Message
