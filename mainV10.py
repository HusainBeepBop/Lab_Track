"""
Lab Inventory Management System - Modern Dashboard Edition
A desktop application for managing university lab equipment using CustomTkinter and Supabase.

This version features:
- Left sidebar navigation (modern dashboard layout)
- Dashboard view with summary cards and data visualization
- Card-based UI design with dark theme
- Comprehensive educational comments for learning
"""

import customtkinter as ctk
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import os
from tkinter import filedialog

# Pandas for CSV import functionality
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("Warning: Pandas not installed. CSV import will not be available.")

# Matplotlib imports for data visualization
# We use TkAgg backend to embed matplotlib figures directly into CustomTkinter
try:
    import matplotlib
    matplotlib.use('TkAgg')  # Set backend before importing pyplot
    from matplotlib import pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: Matplotlib not installed. Charts will not be displayed.")

# Try to import supabase, fall back to mock if not available
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("Warning: Supabase not installed. Using mock data.")

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, use system env vars


class DatabaseManager:
    """Handles all database operations with Supabase."""
    
    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        """
        Initialize database manager.
        If credentials are not provided, uses mock data.
        """
        self.use_mock = False
        
        if url and key and SUPABASE_AVAILABLE:
            try:
                self.client: Client = create_client(url, key)
                # Test connection
                self.client.table('inventory').select('*').limit(1).execute()
                print("Connected to Supabase successfully.")
            except Exception as e:
                print(f"Failed to connect to Supabase: {e}. Using mock data.")
                self.use_mock = True
        else:
            self.use_mock = True
            print("Using mock data. Set SUPABASE_URL and SUPABASE_KEY to connect.")
        
        if self.use_mock:
            self._init_mock_data()
    
    def _init_mock_data(self):
        """Initialize mock data for testing without Supabase."""
        # Inventory with course field for tracking which course components belong to
        self.mock_inventory = [
            {"id": 1, "name": "Arduino", "total_qty": 10, "course": "ECE101"},
            {"id": 2, "name": "Raspberry Pi", "total_qty": 5, "course": "CS201"},
            {"id": 3, "name": "Sensor", "total_qty": 20, "course": "ECE101"},
        ]
        
        self.mock_items = [
            {"id": 1, "serial_number": "ARD001", "status": "Available", "inventory_id": 1},
            {"id": 2, "serial_number": "ARD002", "status": "Available", "inventory_id": 1},
            {"id": 3, "serial_number": "ARD003", "status": "Issued", "inventory_id": 1},
            {"id": 4, "serial_number": "ARD004", "status": "Damaged", "inventory_id": 1},
            {"id": 5, "serial_number": "RPI001", "status": "Available", "inventory_id": 2},
            {"id": 6, "serial_number": "RPI002", "status": "Available", "inventory_id": 2},
            {"id": 7, "serial_number": "SEN001", "status": "Available", "inventory_id": 3},
        ]
        
        self.mock_students = [
            {"id": 1, "name": "John Doe", "student_id": "STU001", "phone": "555-0101", "email": "john.doe@university.edu"},
            {"id": 2, "name": "Jane Smith", "student_id": "STU002", "phone": "555-0102", "email": "jane.smith@university.edu"},
            {"id": 3, "name": "Bob Johnson", "student_id": "STU003", "phone": "555-0103", "email": "bob.johnson@university.edu"},
        ]
        
        # Staff/Issuer data - tracks who issued the components
        self.mock_staff = [
            {"id": 1, "name": "Dr. Sarah Chen", "staff_id": "STAFF001"},
            {"id": 2, "name": "Prof. Michael Brown", "staff_id": "STAFF002"},
            {"id": 3, "name": "Lab Assistant", "staff_id": "STAFF003"},
        ]
        
        # Initialize with some sample transactions for testing
        # This creates realistic data for the Recent Activity feed and overdue testing
        now = datetime.now()
        self.mock_transactions = [
            {
                "id": 1,
                "student_id": 1,
                "issuer_id": 1,  # Issued by Dr. Sarah Chen
                "status": "Active",
                "created_at": now.isoformat(),
                "issue_date": now.isoformat()  # Current transaction
            },
            {
                "id": 2,
                "student_id": 2,
                "issuer_id": 2,  # Issued by Prof. Michael Brown
                "status": "Active",
                "created_at": (now - timedelta(days=10)).isoformat(),  # 10 days ago - OVERDUE
                "issue_date": (now - timedelta(days=10)).isoformat()
            }
        ]
        
        self.mock_transaction_items = [
            {
                "id": 1,
                "transaction_id": 1,
                "item_id": 3  # ARD003 is issued to John Doe (current)
            },
            {
                "id": 2,
                "transaction_id": 2,
                "item_id": 5  # RPI001 is issued to Jane Smith (overdue)
            }
        ]
    
    def get_item_by_serial(self, serial_number: str) -> Optional[Dict]:
        """Get item by serial number."""
        if self.use_mock:
            for item in self.mock_items:
                if item["serial_number"].upper() == serial_number.upper():
                    return item
            return None
        else:
            try:
                result = self.client.table('items').select('*, inventory(*)').eq('serial_number', serial_number).execute()
                if result.data:
                    return result.data[0]
                return None
            except Exception as e:
                print(f"Error fetching item: {e}")
                return None
    
    def get_available_items_by_name(self, component_name: str) -> List[Dict]:
        """Get all available items for a component name."""
        if self.use_mock:
            # Find inventory ID by name
            inventory_id = None
            for inv in self.mock_inventory:
                if inv["name"].upper() == component_name.upper():
                    inventory_id = inv["id"]
                    break
            
            if not inventory_id:
                return []
            
            # Return available items
            available = []
            for item in self.mock_items:
                if item["inventory_id"] == inventory_id and item["status"] == "Available":
                    available.append(item)
            return available
        else:
            try:
                # First get inventory by name
                inv_result = self.client.table('inventory').select('id').ilike('name', f'%{component_name}%').execute()
                if not inv_result.data:
                    return []
                
                inventory_ids = [inv["id"] for inv in inv_result.data]
                
                # Get available items
                result = self.client.table('items').select('*, inventory(*)').in_('inventory_id', inventory_ids).eq('status', 'Available').execute()
                return result.data
            except Exception as e:
                print(f"Error fetching available items: {e}")
                return []
    
    def get_all_students(self) -> List[Dict]:
        """Get all students."""
        if self.use_mock:
            return self.mock_students
        else:
            try:
                result = self.client.table('students').select('*').execute()
                return result.data
            except Exception as e:
                print(f"Error fetching students: {e}")
                return []
    
    def create_student(self, student_data: Dict) -> Optional[int]:
        """
        Create a new student record.
        
        This method automatically saves to Supabase if connected, otherwise uses mock data.
        All student operations (create, update, delete) work with both Supabase and mock data.
        
        Args:
            student_data: Dictionary with student fields (student_id, name, phone, email)
        
        Returns:
            ID of created student record, or None if failed
        """
        if self.use_mock:
            # Generate new ID
            new_id = max([s["id"] for s in self.mock_students], default=0) + 1
            new_student = {"id": new_id, **student_data}
            self.mock_students.append(new_student)
            return new_id
        else:
            try:
                result = self.client.table('students').insert(student_data).execute()
                return result.data[0]["id"] if result.data else None
            except Exception as e:
                print(f"Error creating student: {e}")
                return None
    
    def delete_student(self, student_id: int) -> bool:
        """
        Delete a student record.
        
        Args:
            student_id: The ID of the student to delete
            
        Returns:
            True if successful, False otherwise
        """
        if self.use_mock:
            # Remove student from mock list
            self.mock_students = [s for s in self.mock_students if s["id"] != student_id]
            return True
        else:
            try:
                self.client.table('students').delete().eq('id', student_id).execute()
                return True
            except Exception as e:
                print(f"Error deleting student: {e}")
                return False
    
    def get_all_staff(self) -> List[Dict]:
        """Get all staff/issuers."""
        if self.use_mock:
            return self.mock_staff
        else:
            try:
                result = self.client.table('staff').select('*').execute()
                return result.data
            except Exception as e:
                print(f"Error fetching staff: {e}")
                return []
    
    def create_transaction(self, student_id: int, item_ids: List[int], issuer_id: Optional[int] = None) -> Optional[int]:
        """
        Create a transaction and transaction items.
        
        Stores issue_date (created_at) for overdue tracking.
        Also tracks who issued the items (issuer_id).
        
        Args:
            student_id: ID of the student receiving items
            item_ids: List of item IDs to issue
            issuer_id: Optional ID of the staff member issuing the items
        """
        current_time = datetime.now()
        if self.use_mock:
            transaction_id = len(self.mock_transactions) + 1
            transaction_data = {
                "id": transaction_id,
                "student_id": student_id,
                "status": "Active",
                "created_at": current_time.isoformat(),
                "issue_date": current_time.isoformat()  # Store for overdue tracking
            }
            if issuer_id:
                transaction_data["issuer_id"] = issuer_id
            
            self.mock_transactions.append(transaction_data)
            
            for item_id in item_ids:
                self.mock_transaction_items.append({
                    "id": len(self.mock_transaction_items) + 1,
                    "transaction_id": transaction_id,
                    "item_id": item_id
                })
                # Update item status
                for item in self.mock_items:
                    if item["id"] == item_id:
                        item["status"] = "Issued"
                        break
            
            return transaction_id
        else:
            try:
                # Create transaction with issue_date for overdue tracking
                current_time = datetime.now()
                transaction_data = {
                    "student_id": student_id,
                    "status": "Active",
                    "created_at": current_time.isoformat(),
                    "issue_date": current_time.isoformat()  # Store for overdue tracking
                }
                if issuer_id:
                    transaction_data["issuer_id"] = issuer_id
                
                trans_result = self.client.table('transactions').insert(transaction_data).execute()
                
                transaction_id = trans_result.data[0]["id"]
                
                # Create transaction items and update item status
                for item_id in item_ids:
                    self.client.table('transaction_items').insert({
                        "transaction_id": transaction_id,
                        "item_id": item_id
                    }).execute()
                    
                    self.client.table('items').update({
                        "status": "Issued"
                    }).eq('id', item_id).execute()
                
                return transaction_id
            except Exception as e:
                print(f"Error creating transaction: {e}")
                return None
    
    def get_all_inventory(self) -> List[Dict]:
        """Get all inventory items."""
        if self.use_mock:
            return self.mock_inventory
        else:
            try:
                result = self.client.table('inventory').select('*').execute()
                return result.data
            except Exception as e:
                print(f"Error fetching inventory: {e}")
                return []
    
    def get_inventory_schema(self) -> Dict:
        """
        Get the schema/structure of inventory items.
        This dynamically detects all fields from existing inventory records.
        Returns a dictionary with field names and their types.
        """
        if self.use_mock:
            # Get sample inventory to detect fields
            if self.mock_inventory:
                sample = self.mock_inventory[0]
                schema = {}
                for key, value in sample.items():
                    if key == "id":
                        schema[key] = {"type": "int", "required": False, "editable": False}
                    elif isinstance(value, int):
                        schema[key] = {"type": "int", "required": True, "editable": True}
                    elif isinstance(value, str):
                        schema[key] = {"type": "str", "required": True, "editable": True}
                    else:
                        schema[key] = {"type": "str", "required": False, "editable": True}
                return schema
            else:
                # Default schema if no inventory exists
                return {
                    "name": {"type": "str", "required": True, "editable": True},
                    "total_qty": {"type": "int", "required": True, "editable": True},
                    "course": {"type": "str", "required": False, "editable": True}
                }
        else:
            try:
                # Get one record to detect schema
                result = self.client.table('inventory').select('*').limit(1).execute()
                if result.data:
                    sample = result.data[0]
                    schema = {}
                    for key, value in sample.items():
                        if key == "id":
                            schema[key] = {"type": "int", "required": False, "editable": False}
                        elif isinstance(value, int):
                            schema[key] = {"type": "int", "required": True, "editable": True}
                        elif isinstance(value, str):
                            schema[key] = {"type": "str", "required": True, "editable": True}
                        else:
                            schema[key] = {"type": "str", "required": False, "editable": True}
                    return schema
                else:
                    # Default schema if no inventory exists
                    return {
                        "name": {"type": "str", "required": True, "editable": True},
                        "total_qty": {"type": "int", "required": True, "editable": True},
                        "course": {"type": "str", "required": False, "editable": True}
                    }
            except Exception as e:
                print(f"Error fetching inventory schema: {e}")
                # Return default schema on error
                return {
                    "name": {"type": "str", "required": True, "editable": True},
                    "total_qty": {"type": "int", "required": True, "editable": True},
                    "course": {"type": "str", "required": False, "editable": True}
                }
    
    def create_inventory(self, inventory_data: Dict) -> Optional[int]:
        """
        Create a new inventory record.
        
        Args:
            inventory_data: Dictionary with inventory fields (name, total_qty, course, etc.)
        
        Returns:
            ID of created inventory record, or None if failed
        """
        if self.use_mock:
            # Generate new ID
            new_id = max([inv["id"] for inv in self.mock_inventory], default=0) + 1
            new_inventory = {"id": new_id, **inventory_data}
            self.mock_inventory.append(new_inventory)
            return new_id
        else:
            try:
                result = self.client.table('inventory').insert(inventory_data).execute()
                return result.data[0]["id"] if result.data else None
            except Exception as e:
                print(f"Error creating inventory: {e}")
                return None
    
    def get_all_items(self) -> List[Dict]:
        """Get all items with inventory info."""
        if self.use_mock:
            items_with_inv = []
            for item in self.mock_items:
                inv = next((inv for inv in self.mock_inventory if inv["id"] == item["inventory_id"]), None)
                item_copy = item.copy()
                item_copy["inventory"] = inv
                items_with_inv.append(item_copy)
            return items_with_inv
        else:
            try:
                result = self.client.table('items').select('*, inventory(*)').execute()
                return result.data
            except Exception as e:
                print(f"Error fetching items: {e}")
                return []
    
    def get_current_holder(self, item_id: int) -> Optional[str]:
        """
        Get the name of the student who currently has an item issued.
        
        This method performs a "JOIN" operation conceptually:
        1. Find the transaction_item that links to this item_id
        2. Find the transaction that contains this transaction_item
        3. Ensure the transaction is "Active" (not closed)
        4. Get the student associated with that transaction
        
        Args:
            item_id: The ID of the item to check
            
        Returns:
            Student name if item is issued, None if available
        """
        if self.use_mock:
            # Mock implementation: Find active transaction for this item
            # Step 1: Find transaction_item with this item_id
            for trans_item in self.mock_transaction_items:
                if trans_item["item_id"] == item_id:
                    # Step 2: Find the transaction
                    transaction_id = trans_item["transaction_id"]
                    for trans in self.mock_transactions:
                        if trans["id"] == transaction_id and trans["status"] == "Active":
                            # Step 3: Find the student
                            student_id = trans["student_id"]
                            for student in self.mock_students:
                                if student["id"] == student_id:
                                    return student["name"]
            return None
        else:
            try:
                # Real Supabase implementation using joins
                # This query joins: transaction_items -> transactions -> students
                result = self.client.table('transaction_items').select(
                    'transaction_id, transactions!inner(student_id, status, students!inner(name))'
                ).eq('item_id', item_id).eq('transactions.status', 'Active').execute()
                
                if result.data and len(result.data) > 0:
                    # Extract student name from nested structure
                    transaction_data = result.data[0]
                    if 'transactions' in transaction_data:
                        if 'students' in transaction_data['transactions']:
                            return transaction_data['transactions']['students']['name']
                return None
            except Exception as e:
                print(f"Error fetching current holder: {e}")
                return None
    
    def search_students(self, query: str) -> List[Dict]:
        """
        Search students by ID or name.
        
        Args:
            query: Search term (student_id or name)
            
        Returns:
            List of matching students
        """
        query_lower = query.lower().strip()
        if not query_lower:
            return []
        
        if self.use_mock:
            results = []
            for student in self.mock_students:
                if (query_lower in student["student_id"].lower() or 
                    query_lower in student["name"].lower()):
                    results.append(student)
            return results
        else:
            try:
                # Search in both student_id and name fields
                result = self.client.table('students').select('*').or_(
                    f'student_id.ilike.%{query}%,name.ilike.%{query}%'
                ).execute()
                return result.data
            except Exception as e:
                print(f"Error searching students: {e}")
                return []
    
    def get_active_loans(self, student_id: int) -> List[Dict]:
        """
        Get all items currently issued to a student.
        
        This performs a reverse join:
        1. Find all Active transactions for this student
        2. Find all transaction_items in those transactions
        3. Get the actual item details with inventory info
        
        Args:
            student_id: The ID of the student
            
        Returns:
            List of items with transaction information
        """
        if self.use_mock:
            loans = []
            # Find active transactions for this student
            for trans in self.mock_transactions:
                if trans["student_id"] == student_id and trans["status"] == "Active":
                    # Find items in this transaction
                    for trans_item in self.mock_transaction_items:
                        if trans_item["transaction_id"] == trans["id"]:
                            # Get the item details
                            item_id = trans_item["item_id"]
                            for item in self.mock_items:
                                if item["id"] == item_id:
                                    item_copy = item.copy()
                                    # Add inventory info
                                    inv = next((inv for inv in self.mock_inventory 
                                              if inv["id"] == item["inventory_id"]), None)
                                    item_copy["inventory"] = inv
                                    item_copy["transaction_id"] = trans["id"]
                                    item_copy["transaction_item_id"] = trans_item["id"]
                                    loans.append(item_copy)
            return loans
        else:
            try:
                # Get active transactions for student
                trans_result = self.client.table('transactions').select(
                    'id, transaction_items(*, items(*, inventory(*)))'
                ).eq('student_id', student_id).eq('status', 'Active').execute()
                
                loans = []
                for trans in trans_result.data:
                    if 'transaction_items' in trans:
                        for trans_item in trans['transaction_items']:
                            if 'items' in trans_item:
                                item = trans_item['items']
                                item['transaction_id'] = trans['id']
                                item['transaction_item_id'] = trans_item['id']
                                loans.append(item)
                return loans
            except Exception as e:
                print(f"Error fetching active loans: {e}")
                return []
    
    def return_item(self, item_id: int, transaction_id: int) -> bool:
        """
        Return an item: Set status to Available and close the transaction.
        
        Args:
            item_id: The item being returned
            transaction_id: The transaction to close
            
        Returns:
            True if successful, False otherwise
        """
        if self.use_mock:
            # Update item status
            for item in self.mock_items:
                if item["id"] == item_id:
                    item["status"] = "Available"
                    break
            
            # Close transaction
            for trans in self.mock_transactions:
                if trans["id"] == transaction_id:
                    trans["status"] = "Closed"
                    trans["closed_at"] = datetime.now().isoformat()
                    break
            
            return True
        else:
            try:
                # Update item status to Available
                self.client.table('items').update({
                    "status": "Available"
                }).eq('id', item_id).execute()
                
                # Close transaction
                self.client.table('transactions').update({
                    "status": "Closed",
                    "closed_at": datetime.now().isoformat()
                }).eq('id', transaction_id).execute()
                
                return True
            except Exception as e:
                print(f"Error returning item: {e}")
                return False
    
    def report_damaged(self, item_id: int, transaction_id: int) -> bool:
        """
        Report an item as damaged: Set status to Damaged and close the transaction.
        
        Args:
            item_id: The item being reported
            transaction_id: The transaction to close
            
        Returns:
            True if successful, False otherwise
        """
        if self.use_mock:
            # Update item status to Damaged
            for item in self.mock_items:
                if item["id"] == item_id:
                    item["status"] = "Damaged"
                    break
            
            # Close transaction
            for trans in self.mock_transactions:
                if trans["id"] == transaction_id:
                    trans["status"] = "Closed"
                    trans["closed_at"] = datetime.now().isoformat()
                    break
            
            return True
        else:
            try:
                # Update item status to Damaged
                self.client.table('items').update({
                    "status": "Damaged"
                }).eq('id', item_id).execute()
                
                # Close transaction
                self.client.table('transactions').update({
                    "status": "Closed",
                    "closed_at": datetime.now().isoformat()
                }).eq('id', transaction_id).execute()
                
                return True
            except Exception as e:
                print(f"Error reporting damaged item: {e}")
                return False
    
    def get_recent_transactions(self, limit: int = 5) -> List[Dict]:
        """
        Get recent transactions for the Dashboard activity feed.
        
        This returns the most recent transactions with:
        - Student name
        - Item details
        - Timestamp
        - Action type (Issue/Return/Damaged)
        
        Args:
            limit: Number of recent transactions to return
            
        Returns:
            List of recent transaction records
        """
        if self.use_mock:
            # Get recent transactions (most recent first)
            # Sort by created_at descending, then take limit
            sorted_transactions = sorted(
                self.mock_transactions,
                key=lambda x: x.get("created_at", ""),
                reverse=True
            )[:limit]
            
            recent = []
            for trans in sorted_transactions:
                # Get student name
                student_name = "Unknown"
                for student in self.mock_students:
                    if student["id"] == trans["student_id"]:
                        student_name = student["name"]
                        break
                
                # Get items in this transaction
                items = []
                for trans_item in self.mock_transaction_items:
                    if trans_item["transaction_id"] == trans["id"]:
                        for item in self.mock_items:
                            if item["id"] == trans_item["item_id"]:
                                items.append(item)
                                break
                
                # Create activity record for each item
                for item in items:
                    inv_name = "Unknown"
                    if item.get("inventory_id"):
                        for inv in self.mock_inventory:
                            if inv["id"] == item["inventory_id"]:
                                inv_name = inv["name"]
                                break
                    
                    recent.append({
                        "student_name": student_name,
                        "item_name": inv_name,
                        "serial_number": item.get("serial_number", "N/A"),
                        "action": "Issue" if trans["status"] == "Active" else "Return",
                        "timestamp": trans.get("created_at", datetime.now().isoformat()),
                        "transaction_id": trans["id"]
                    })
            
            return recent[:limit]
        else:
            try:
                # Get recent transactions with joins
                result = self.client.table('transactions').select(
                    'id, status, created_at, students(name), transaction_items(items(serial_number, inventory(name)))'
                ).order('created_at', desc=True).limit(limit * 2).execute()  # Get more to account for multiple items
                
                recent = []
                for trans in result.data:
                    student_name = trans.get('students', {}).get('name', 'Unknown')
                    action = "Issue" if trans["status"] == "Active" else "Return"
                    
                    if 'transaction_items' in trans:
                        for trans_item in trans['transaction_items']:
                            if 'items' in trans_item:
                                item = trans_item['items']
                                inv_name = item.get('inventory', {}).get('name', 'Unknown')
                                recent.append({
                                    "student_name": student_name,
                                    "item_name": inv_name,
                                    "serial_number": item.get('serial_number', 'N/A'),
                                    "action": action,
                                    "timestamp": trans.get('created_at'),
                                    "transaction_id": trans['id']
                                })
                                if len(recent) >= limit:
                                    break
                    if len(recent) >= limit:
                        break
                
                return recent[:limit]
            except Exception as e:
                print(f"Error fetching recent transactions: {e}")
                return []
    
    def get_overdue_items(self, days_threshold: int = 7) -> List[Dict]:
        """
        Get all items that are overdue (issued for more than threshold days).
        
        This method:
        1. Finds all Active transactions
        2. Checks their issue_date (or created_at as fallback)
        3. Calculates days since issue
        4. Returns items that exceed the threshold
        
        Args:
            days_threshold: Number of days before an item is considered overdue (default: 7)
            
        Returns:
            List of overdue items with transaction info
        """
        if self.use_mock:
            overdue_items = []
            threshold_date = datetime.now() - timedelta(days=days_threshold)
            
            for trans in self.mock_transactions:
                if trans["status"] == "Active":
                    # Get issue date (use created_at as fallback)
                    issue_date_str = trans.get("issue_date") or trans.get("created_at")
                    if issue_date_str:
                        try:
                            issue_date = datetime.fromisoformat(issue_date_str.replace('Z', ''))
                            if issue_date < threshold_date:
                                # This transaction is overdue, get its items
                                for trans_item in self.mock_transaction_items:
                                    if trans_item["transaction_id"] == trans["id"]:
                                        for item in self.mock_items:
                                            if item["id"] == trans_item["item_id"]:
                                                item_copy = item.copy()
                                                item_copy["transaction_id"] = trans["id"]
                                                item_copy["days_overdue"] = (datetime.now() - issue_date).days
                                                overdue_items.append(item_copy)
                                                break
                        except:
                            pass
            
            return overdue_items
        else:
            try:
                # Get all active transactions older than threshold
                threshold_date = (datetime.now() - timedelta(days=days_threshold)).isoformat()
                
                # Query transactions with their items
                result = self.client.table('transactions').select(
                    'id, issue_date, created_at, transaction_items(items(*))'
                ).eq('status', 'Active').lt('issue_date', threshold_date).execute()
                
                overdue_items = []
                for trans in result.data:
                    issue_date_str = trans.get('issue_date') or trans.get('created_at')
                    if issue_date_str:
                        try:
                            issue_date = datetime.fromisoformat(issue_date_str.replace('Z', ''))
                            days_overdue = (datetime.now() - issue_date).days
                            
                            if 'transaction_items' in trans:
                                for trans_item in trans['transaction_items']:
                                    if 'items' in trans_item:
                                        item = trans_item['items']
                                        item['transaction_id'] = trans['id']
                                        item['days_overdue'] = days_overdue
                                        overdue_items.append(item)
                        except:
                            pass
                
                return overdue_items
            except Exception as e:
                print(f"Error fetching overdue items: {e}")
                return []
    
    def bulk_import_inventory(self, csv_data: List[Dict]) -> Tuple[int, int]:
        """
        Bulk import inventory from CSV data.
        
        This method:
        1. Creates inventory records for each component
        2. Generates individual item records with auto-generated serial numbers
        3. Handles bulk inserts efficiently
        
        Expected CSV columns:
        - Component Name: Name of the component
        - Quantity: Number of items to create
        - Description: Optional description
        
        Serial Number Generation Logic:
        - Takes first 3 letters of component name (uppercase)
        - Appends sequential number (001, 002, etc.)
        - Example: "Arduino" -> "ARD001", "ARD002", etc.
        
        Args:
            csv_data: List of dictionaries with 'Component Name', 'Quantity', 'Description'
            
        Returns:
            Tuple of (inventory_records_created, item_records_created)
        """
        inventory_created = 0
        items_created = 0
        
        if self.use_mock:
            for row in csv_data:
                component_name = row.get('Component Name', '').strip()
                quantity = int(row.get('Quantity', 0))
                description = row.get('Description', '').strip()
                
                if not component_name or quantity <= 0:
                    continue
                
                # Check if inventory already exists
                existing_inv = None
                for inv in self.mock_inventory:
                    if inv["name"].upper() == component_name.upper():
                        existing_inv = inv
                        break
                
                if existing_inv:
                    inventory_id = existing_inv["id"]
                    # Update total quantity
                    existing_inv["total_qty"] += quantity
                else:
                    # Create new inventory record
                    inventory_id = len(self.mock_inventory) + 1
                    self.mock_inventory.append({
                        "id": inventory_id,
                        "name": component_name,
                        "total_qty": quantity,
                        "description": description
                    })
                    inventory_created += 1
                
                # ============================================================
                # SERIAL NUMBER GENERATION LOGIC (For Project Presentation)
                # ============================================================
                # This algorithm generates unique serial numbers automatically:
                # 
                # Step 1: Extract prefix from component name
                #   - Take first 3 letters of component name (uppercase)
                #   - Remove spaces: "Raspberry Pi" -> "RAS"
                #   - If name is too short, pad with 'X': "Pi" -> "PIX"
                #
                # Step 2: Find highest existing serial number
                #   - Search all existing items for this inventory
                #   - Extract numeric suffix from matching serials
                #   - Track the maximum number found
                #
                # Step 3: Generate sequential serials
                #   - Start from (max_num + 1)
                #   - Format as 3-digit zero-padded: "001", "002", etc.
                #   - Combine: prefix + number = "ARD001", "ARD002"
                #
                # Example: Importing 5 "Arduino" items when ARD001-ARD003 exist:
                #   - Prefix: "ARD"
                #   - Max found: 3
                #   - Generated: ARD004, ARD005, ARD006, ARD007, ARD008
                #
                # This ensures no duplicate serials and maintains logical grouping.
                
                prefix = component_name[:3].upper().replace(' ', '')
                if len(prefix) < 3:
                    prefix = prefix.ljust(3, 'X')  # Pad if too short
                
                # Find highest existing serial for this component
                max_num = 0
                for item in self.mock_items:
                    if item.get("inventory_id") == inventory_id:
                        serial = item.get("serial_number", "")
                        if serial.startswith(prefix):
                            try:
                                num = int(serial[len(prefix):])
                                max_num = max(max_num, num)
                            except:
                                pass
                
                # Create items with sequential serial numbers
                for i in range(quantity):
                    serial_number = f"{prefix}{max_num + i + 1:03d}"
                    self.mock_items.append({
                        "id": len(self.mock_items) + 1,
                        "serial_number": serial_number,
                        "status": "Available",
                        "inventory_id": inventory_id
                    })
                    items_created += 1
        else:
            try:
                for row in csv_data:
                    component_name = row.get('Component Name', '').strip()
                    quantity = int(row.get('Quantity', 0))
                    description = row.get('Description', '').strip()
                    
                    if not component_name or quantity <= 0:
                        continue
                    
                    # Check if inventory exists
                    existing = self.client.table('inventory').select('id, total_qty').ilike(
                        'name', component_name
                    ).execute()
                    
                    if existing.data:
                        inventory_id = existing.data[0]['id']
                        # Update total quantity
                        self.client.table('inventory').update({
                            'total_qty': existing.data[0]['total_qty'] + quantity
                        }).eq('id', inventory_id).execute()
                    else:
                        # Create new inventory
                        inv_result = self.client.table('inventory').insert({
                            'name': component_name,
                            'total_qty': quantity,
                            'description': description
                        }).execute()
                        inventory_id = inv_result.data[0]['id']
                        inventory_created += 1
                    
                    # ============================================================
                    # SERIAL NUMBER GENERATION LOGIC (For Project Presentation)
                    # ============================================================
                    # Same algorithm as mock data (see detailed comments above)
                    # This ensures consistency between mock and real database
                    
                    prefix = component_name[:3].upper().replace(' ', '')
                    if len(prefix) < 3:
                        prefix = prefix.ljust(3, 'X')
                    
                    # Find highest existing serial
                    existing_items = self.client.table('items').select('serial_number').eq(
                        'inventory_id', inventory_id
                    ).execute()
                    
                    max_num = 0
                    for item in existing_items.data:
                        serial = item.get('serial_number', '')
                        if serial.startswith(prefix):
                            try:
                                num = int(serial[len(prefix):])
                                max_num = max(max_num, num)
                            except:
                                pass
                    
                    # Bulk insert items
                    items_to_insert = []
                    for i in range(quantity):
                        serial_number = f"{prefix}{max_num + i + 1:03d}"
                        items_to_insert.append({
                            'serial_number': serial_number,
                            'status': 'Available',
                            'inventory_id': inventory_id
                        })
                    
                    # Insert in batches (Supabase has limits)
                    batch_size = 100
                    for i in range(0, len(items_to_insert), batch_size):
                        batch = items_to_insert[i:i + batch_size]
                        self.client.table('items').insert(batch).execute()
                        items_created += len(batch)
            
            except Exception as e:
                print(f"Error bulk importing inventory: {e}")
                return (inventory_created, items_created)
        
        return (inventory_created, items_created)


class ComponentSelectionPopup(ctk.CTkToplevel):
    """
    Popup window for selecting a component when user types component name.
    
    This popup appears when:
    - User types a component name (e.g., "Arduino")
    - Multiple available serial numbers exist for that component
    
    The popup displays all available serial numbers and allows the user
    to select one, which is then added to the cart.
    """
    
    def __init__(self, parent, available_items: List[Dict], callback):
        """
        Initialize the component selection popup.
        
        Args:
            parent: The parent window (main app window)
            available_items: List of available items for the component
            callback: Function to call when an item is selected
        """
        super().__init__(parent)
        self.callback = callback
        self.selected_item = None
        
        # Window configuration
        # geometry: "widthxheight" in pixels
        # To resize popup: change these values
        self.title("Select Component")
        self.geometry("500x400")
        
        # ============================================================
        # MODAL WINDOW EXPLANATION
        # ============================================================
        # transient(parent): Makes this window a child of parent
        # This ensures the popup stays on top of the parent window
        self.transient(parent)
        
        # grab_set(): Makes the popup modal
        # Modal means: User MUST interact with this window before
        # they can click on the parent window again
        # This prevents accidental clicks outside the popup
        self.grab_set()
        
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="Available Serial Numbers",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=20)
        
        # Scrollable frame for items
        scroll_frame = ctk.CTkScrollableFrame(self, width=450, height=250)
        scroll_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        if not available_items:
            no_items_label = ctk.CTkLabel(
                scroll_frame,
                text="No available items found.",
                text_color="gray"
            )
            no_items_label.pack(pady=20)
        else:
            for item in available_items:
                item_frame = ctk.CTkFrame(scroll_frame)
                item_frame.pack(fill="x", pady=5, padx=10)
                
                serial_label = ctk.CTkLabel(
                    item_frame,
                    text=f"Serial: {item['serial_number']}",
                    font=ctk.CTkFont(size=14)
                )
                serial_label.pack(side="left", padx=15, pady=10)
                
                select_btn = ctk.CTkButton(
                    item_frame,
                    text="Select",
                    width=100,
                    command=lambda i=item: self._select_item(i)
                )
                select_btn.pack(side="right", padx=15, pady=10)
        
        # Cancel button
        cancel_btn = ctk.CTkButton(
            self,
            text="Cancel",
            command=self._cancel,
            fg_color="gray",
            hover_color="darkgray"
        )
        cancel_btn.pack(pady=20)
    
    def _select_item(self, item: Dict):
        """Select an item and close popup."""
        self.selected_item = item
        self.callback(item)
        self.destroy()
    
    def _cancel(self):
        """Cancel selection."""
        self.destroy()


class LabApp(ctk.CTk):
    """
    Main application window with modern sidebar navigation.
    
    This class implements a dashboard-style layout with:
    - Left sidebar for navigation (instead of top tabs)
    - Content area that switches views based on sidebar selection
    - Card-based design for better visual hierarchy
    """
    
    def __init__(self):
        super().__init__()
        
        # ============================================================
        # CONFIG ZONE: Window Configuration
        # ============================================================
        # You can modify these values to change the window appearance:
        self.title("Lab Inventory Management System")
        self.geometry("1400x900")  # Increased size for better dashboard layout
        # To change window size: modify the string above (width x height)

        try:
            self.iconbitmap("icon.ico")
        except:
            pass
        
        # ============================================================
        # CONFIG ZONE: Premium SaaS Design System - Zinc Monochrome Palette
        # ============================================================
        # We're using a custom monochrome zinc palette for a premium SaaS aesthetic
        # This creates a sophisticated, modern look similar to Vercel/Linear
        ctk.set_appearance_mode("Dark")
        
        # Define our custom zinc color palette
        # These colors create depth and hierarchy without using bright colors
        self.colors = {
            "bg_primary": "#09090b",      # Very dark zinc - main background
            "bg_secondary": "#18181b",    # Dark zinc - sidebar and cards
            "border": "#27272a",           # Subtle gray borders for separation
            "text_primary": "#fafafa",     # Primary text - high contrast
            "text_secondary": "#a1a1aa",   # Secondary text - lower contrast
            "accent": "#ffffff",            # White for active states and accents
            "status_available": "#22c55e", # Green for available status
            "status_issued": "#3b82f6",    # Blue for issued status
            "status_damaged": "#ef4444"    # Red for damaged status
        }
        
        # Configure window background to match our palette
        self.configure(bg=self.colors["bg_primary"])
        
        # ============================================================
        # CONFIG ZONE: Database Credentials
        # ============================================================
        # PASTE YOUR SUPABASE CREDENTIALS HERE:
        # Option 1: Set environment variables in your system
        # Option 2: Create a .env file in the project root with:
        #   SUPABASE_URL=your_project_url_here
        #   SUPABASE_KEY=your_anon_key_here
        # Option 3: Hardcode them below (NOT RECOMMENDED for production)
        # =============================================================
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        # If you want to hardcode (for testing only), uncomment below:
        # supabase_url = "your_url_here"
        # supabase_key = "your_key_here"
        
        # Store credentials for sync functionality
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        
        self.db = DatabaseManager(supabase_url, supabase_key)
        
        # Cart for issue items (stores items before finalizing transaction)
        self.cart_items: List[Dict] = []
        
        # Track current view for sidebar highlighting
        self.current_view = "dashboard"
        
        # Track overdue items for highlighting in Catalog
        self.overdue_item_ids: set = set()
        
        # Track current selected issuer (staff member) - global across app
        self.current_issuer_id: Optional[int] = None
        self.current_issuer_name: Optional[str] = None
        
        # Create UI
        self._create_ui()
    
    def _create_ui(self):
        """
        Create the main UI with sidebar navigation.
        
        This method sets up:
        1. Left sidebar with navigation buttons
        2. Main content area that displays different views
        3. Initial view (Dashboard) when app starts
        """
        # Create main container using grid for better control
        # Grid allows us to have fixed sidebar and flexible content area
        self.grid_columnconfigure(1, weight=1)  # Content area expands
        self.grid_rowconfigure(1, weight=1)  # Content area row expands (row 0 is header)
        
        # ============================================================
        # GLOBAL HEADER - Top Right Staff Selector
        # ============================================================
        # Header spans across the top, accessible from all views
        header_frame = ctk.CTkFrame(
            self,
            height=60,
            corner_radius=0,
            fg_color=self.colors["bg_secondary"],
            border_width=0
        )
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=0, pady=0)
        header_frame.grid_columnconfigure(1, weight=1)  # Push sync button and staff selector to right
        header_frame.grid_propagate(False)  # Maintain fixed height
        
        # Staff selector on the right
        staff_label = ctk.CTkLabel(
            header_frame,
            text="Issuer:",
            font=ctk.CTkFont(size=12, weight="normal"),
            text_color=self.colors["text_secondary"]
        )
        staff_label.grid(row=0, column=0, padx=(20, 10), pady=15, sticky="e")
        
        # Sync button - refreshes data from Supabase
        sync_btn = ctk.CTkButton(
            header_frame,
            text="🔄 Sync",
            command=self._sync_data,
            width=100,
            height=36,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=self.colors["status_issued"],
            hover_color="#2563eb",
            text_color="#ffffff",
            corner_radius=8
        )
        sync_btn.grid(row=0, column=1, padx=(0, 12), pady=15, sticky="e")
        
        # Global staff dropdown - accessible from anywhere
        self.global_issuer_dropdown = ctk.CTkComboBox(
            header_frame,
            values=[],
            width=300,
            font=ctk.CTkFont(size=13),
            fg_color=self.colors["bg_primary"],
            border_color=self.colors["border"],
            text_color=self.colors["text_primary"],
            command=self._on_issuer_changed
        )
        self.global_issuer_dropdown.grid(row=0, column=2, padx=(0, 20), pady=15, sticky="e")
        self._load_global_staff()  # Populate on startup
        
        # ============================================================
        # LEFT SIDEBAR NAVIGATION - Premium SaaS Design
        # ============================================================
        # Sidebar uses bg_secondary (#18181b) to create visual separation
        # This darker panel creates depth and focuses attention on navigation
        sidebar_width = 240  # Slightly wider for better spacing
        sidebar = ctk.CTkFrame(
            self, 
            width=sidebar_width, 
            corner_radius=0,
            fg_color=self.colors["bg_secondary"],
            bg_color=self.colors["bg_primary"]
        )
        sidebar.grid(row=1, column=0, sticky="nsew", rowspan=1)
        sidebar.grid_rowconfigure(5, weight=1)  # Push buttons to top (updated for new tab)
        
        # App Title in Sidebar
        # Typography: Heavy weight for brand identity
        title_label = ctk.CTkLabel(
            sidebar,
            text="Lab Track",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=self.colors["text_primary"]
        )
        title_label.pack(pady=(40, 8))
        
        # Subtitle - Uppercase, small, secondary color
        # This creates hierarchy: main title is prominent, subtitle is subtle
        subtitle_label = ctk.CTkLabel(
            sidebar,
            text="INVENTORY SYSTEM",
            font=ctk.CTkFont(size=10, weight="normal"),
            text_color=self.colors["text_secondary"]
        )
        subtitle_label.pack(pady=(0, 40))
        
        # Navigation Buttons - Premium Design
        # Design rationale: Transparent buttons with subtle hover effects
        # Active state uses white accent for clear visual feedback
        # Spacing: 8px between buttons creates breathing room
        
        self.dashboard_btn = ctk.CTkButton(
            sidebar,
            text="Dashboard",
            command=lambda: self._switch_view("dashboard"),
            height=44,
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
            fg_color=self.colors["accent"] if self.current_view == "dashboard" else "transparent",
            text_color=self.colors["bg_primary"] if self.current_view == "dashboard" else self.colors["text_primary"],
            hover_color="#27272a",  # Subtle hover on inactive buttons
            corner_radius=8
        )
        self.dashboard_btn.pack(pady=4, padx=12, fill="x")
        
        self.issue_btn = ctk.CTkButton(
            sidebar,
            text="Issue Items",
            command=lambda: self._switch_view("issue"),
            height=44,
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
            fg_color=self.colors["accent"] if self.current_view == "issue" else "transparent",
            text_color=self.colors["bg_primary"] if self.current_view == "issue" else self.colors["text_primary"],
            hover_color="#27272a",
            corner_radius=8
        )
        self.issue_btn.pack(pady=4, padx=12, fill="x")
        
        self.returns_btn = ctk.CTkButton(
            sidebar,
            text="Returns",
            command=lambda: self._switch_view("returns"),
            height=44,
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
            fg_color=self.colors["accent"] if self.current_view == "returns" else "transparent",
            text_color=self.colors["bg_primary"] if self.current_view == "returns" else self.colors["text_primary"],
            hover_color="#27272a",
            corner_radius=8
        )
        self.returns_btn.pack(pady=4, padx=12, fill="x")
        
        self.inventory_btn = ctk.CTkButton(
            sidebar,
            text="Inventory",
            command=lambda: self._switch_view("inventory"),
            height=44,
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
            fg_color=self.colors["accent"] if self.current_view == "inventory" else "transparent",
            text_color=self.colors["bg_primary"] if self.current_view == "inventory" else self.colors["text_primary"],
            hover_color="#27272a",
            corner_radius=8
        )
        self.inventory_btn.pack(pady=4, padx=12, fill="x")
        
        # NEW: Catalog Tab - Master Inventory View
        self.catalog_btn = ctk.CTkButton(
            sidebar,
            text="Catalog",
            command=lambda: self._switch_view("catalog"),
            height=44,
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
            fg_color=self.colors["accent"] if self.current_view == "catalog" else "transparent",
            text_color=self.colors["bg_primary"] if self.current_view == "catalog" else self.colors["text_primary"],
            hover_color="#27272a",
            corner_radius=8
        )
        self.catalog_btn.pack(pady=4, padx=12, fill="x")
        
        # NEW: Students Tab - Student Management
        self.students_btn = ctk.CTkButton(
            sidebar,
            text="Students",
            command=lambda: self._switch_view("students"),
            height=44,
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
            fg_color=self.colors["accent"] if self.current_view == "students" else "transparent",
            text_color=self.colors["bg_primary"] if self.current_view == "students" else self.colors["text_primary"],
            hover_color="#27272a",
            corner_radius=8
        )
        self.students_btn.pack(pady=4, padx=12, fill="x")
        
        # ============================================================
        # MAIN CONTENT AREA - Premium Spacing
        # ============================================================
        # Content area uses primary background with generous padding
        # 32px padding creates "breathing room" - a key SaaS design principle
        # This prevents the UI from feeling cramped
        self.content_frame = ctk.CTkFrame(
            self, 
            corner_radius=0,
            fg_color=self.colors["bg_primary"],
            bg_color=self.colors["bg_primary"]
        )
        self.content_frame.grid(row=1, column=1, sticky="nsew", padx=32, pady=32)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        # Show dashboard by default
        self._show_dashboard()
    
    def _switch_view(self, view_name: str):
        """
        Switch between different views in the content area.
        
        This method:
        1. Clears the current content
        2. Updates sidebar button highlights
        3. Shows the selected view
        
        Args:
            view_name: One of "dashboard", "issue", "returns", "inventory"
        """
        self.current_view = view_name
        
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Update button highlights - Premium active state
        # Reset all buttons to transparent (inactive state)
        for btn in [self.dashboard_btn, self.issue_btn, self.returns_btn, self.inventory_btn, self.catalog_btn, self.students_btn]:
            btn.configure(fg_color="transparent", text_color=self.colors["text_primary"])
        
        # Highlight active button with white accent
        # White (#ffffff) on dark background creates strong visual hierarchy
        if view_name == "dashboard":
            self.dashboard_btn.configure(fg_color=self.colors["accent"], text_color=self.colors["bg_primary"])
            self._show_dashboard()
        elif view_name == "issue":
            self.issue_btn.configure(fg_color=self.colors["accent"], text_color=self.colors["bg_primary"])
            self._show_issue_view()
        elif view_name == "returns":
            self.returns_btn.configure(fg_color=self.colors["accent"], text_color=self.colors["bg_primary"])
            self._show_returns_view()
        elif view_name == "inventory":
            self.inventory_btn.configure(fg_color=self.colors["accent"], text_color=self.colors["bg_primary"])
            self._show_inventory_view()
        elif view_name == "catalog":
            self.catalog_btn.configure(fg_color=self.colors["accent"], text_color=self.colors["bg_primary"])
            self._show_catalog_view()
        elif view_name == "students":
            self.students_btn.configure(fg_color=self.colors["accent"], text_color=self.colors["bg_primary"])
            self._show_students_view()
    
    def _show_dashboard(self):
        """
        Display the Dashboard view with premium SaaS-style summary cards and charts.
        
        This is the home screen that appears when the app starts.
        Design principles applied:
        - Generous spacing (30px padding in cards)
        - Typography hierarchy (bold headings, small labels)
        - Trend indicators for professional SaaS look
        - Monochrome zinc palette throughout
        - Overdue tracking with visual alerts
        """
        # Create scrollable container for dashboard content
        scroll_frame = ctk.CTkScrollableFrame(
            self.content_frame,
            fg_color=self.colors["bg_primary"]
        )
        scroll_frame.pack(fill="both", expand=True)
        
        # Title - Premium Typography
        # Large, bold heading creates clear hierarchy
        title = ctk.CTkLabel(
            scroll_frame,
            text="Dashboard",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color=self.colors["text_primary"]
        )
        title.pack(pady=(0, 40), anchor="w")
        
        # ============================================================
        # SUMMARY CARDS SECTION - Premium SaaS Design
        # ============================================================
        # Cards use bg_secondary (#18181b) with subtle borders for depth
        # 20px internal padding creates "breathing room" - key SaaS principle
        cards_container = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        cards_container.pack(fill="x", pady=(0, 40))
        
        # Get data for summary cards
        all_items = self.db.get_all_items()
        all_students = self.db.get_all_students()
        
        total_items = len(all_items)
        issued_count = sum(1 for item in all_items if item.get("status") == "Issued")
        total_students = len(all_students)
        
        # Get overdue items for warning (refresh on each dashboard view)
        # This ensures the overdue count is always current
        overdue_items = self.db.get_overdue_items(days_threshold=7)
        overdue_count = len(overdue_items)
        # Store overdue item IDs for highlighting in Catalog
        self.overdue_item_ids = {item["id"] for item in overdue_items}
        
        # Card dimensions: Premium sizing for visual impact
        card_width = 320
        card_height = 200
        
        # Card 1: Total Items - Premium Design
        # Border creates subtle separation from background
        card1 = ctk.CTkFrame(
            cards_container, 
            width=card_width, 
            height=card_height, 
            corner_radius=12,
            fg_color=self.colors["bg_secondary"],
            border_width=1,
            border_color=self.colors["border"]
        )
        card1.pack(side="left", padx=12, pady=10)
        card1.pack_propagate(False)
        
        # Label: Uppercase, small, secondary color - creates hierarchy
        card1_label = ctk.CTkLabel(
            card1,
            text="TOTAL ITEMS",
            font=ctk.CTkFont(size=11, weight="normal"),
            text_color=self.colors["text_secondary"]
        )
        card1_label.pack(pady=(30, 8), anchor="w", padx=30)
        
        # Value: Large, bold, primary color - draws attention
        card1_value = ctk.CTkLabel(
            card1,
            text=str(total_items),
            font=ctk.CTkFont(size=52, weight="bold"),
            text_color=self.colors["text_primary"]
        )
        card1_value.pack(anchor="w", padx=30)
        
        # Trend indicator: Mock data for professional SaaS look
        # "+2 this week" creates sense of activity and engagement
        card1_trend = ctk.CTkLabel(
            card1,
            text="+2 this week",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_secondary"]
        )
        card1_trend.pack(anchor="w", padx=30, pady=(8, 0))
        
        # Card 2: Currently Issued
        card2 = ctk.CTkFrame(
            cards_container, 
            width=card_width, 
            height=card_height, 
            corner_radius=12,
            fg_color=self.colors["bg_secondary"],
            border_width=1,
            border_color=self.colors["border"]
        )
        card2.pack(side="left", padx=12, pady=10)
        card2.pack_propagate(False)
        
        card2_label = ctk.CTkLabel(
            card2,
            text="CURRENTLY ISSUED",
            font=ctk.CTkFont(size=11, weight="normal"),
            text_color=self.colors["text_secondary"]
        )
        card2_label.pack(pady=(30, 8), anchor="w", padx=30)
        
        # Value color changes to orange if overdue items exist
        value_color = "#f59e0b" if overdue_count > 0 else self.colors["status_issued"]
        card2_value = ctk.CTkLabel(
            card2,
            text=str(issued_count),
            font=ctk.CTkFont(size=52, weight="bold"),
            text_color=value_color
        )
        card2_value.pack(anchor="w", padx=30)
        
        # Show overdue warning if items are overdue
        if overdue_count > 0:
            card2_trend = ctk.CTkLabel(
                card2,
                text=f"⚠️ {overdue_count} Item{'s' if overdue_count != 1 else ''} Overdue",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#f59e0b"  # Orange warning color
            )
            card2_trend.pack(anchor="w", padx=30, pady=(8, 0))
        else:
            card2_trend = ctk.CTkLabel(
                card2,
                text="+1 today",
                font=ctk.CTkFont(size=12),
                text_color=self.colors["text_secondary"]
            )
            card2_trend.pack(anchor="w", padx=30, pady=(8, 0))
        
        # Make card clickable to navigate to Catalog with filter
        def navigate_to_overdue():
            """Navigate to Catalog tab and filter for Issued items."""
            self._switch_view("catalog")
            # Set filter to "Issued" after a short delay to ensure view is loaded
            self.after(100, lambda: self._set_catalog_filter("Issued"))
        
        # Make entire card clickable with hover effect
        def on_enter(e):
            card2.configure(cursor="hand2")
        def on_leave(e):
            card2.configure(cursor="")
        
        card2.bind("<Enter>", on_enter)
        card2.bind("<Leave>", on_leave)
        card2.bind("<Button-1>", lambda e: navigate_to_overdue())
        
        # Make all child widgets clickable too
        for widget in card2.winfo_children():
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.bind("<Button-1>", lambda e: navigate_to_overdue())
        
        # Card 3: Total Students
        card3 = ctk.CTkFrame(
            cards_container, 
            width=card_width, 
            height=card_height, 
            corner_radius=12,
            fg_color=self.colors["bg_secondary"],
            border_width=1,
            border_color=self.colors["border"]
        )
        card3.pack(side="left", padx=12, pady=10)
        card3.pack_propagate(False)
        
        card3_label = ctk.CTkLabel(
            card3,
            text="TOTAL STUDENTS",
            font=ctk.CTkFont(size=11, weight="normal"),
            text_color=self.colors["text_secondary"]
        )
        card3_label.pack(pady=(30, 8), anchor="w", padx=30)
        
        card3_value = ctk.CTkLabel(
            card3,
            text=str(total_students),
            font=ctk.CTkFont(size=52, weight="bold"),
            text_color=self.colors["text_primary"]
        )
        card3_value.pack(anchor="w", padx=30)
        
        card3_trend = ctk.CTkLabel(
            card3,
            text="No change",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_secondary"]
        )
        card3_trend.pack(anchor="w", padx=30, pady=(8, 0))
        
        # ============================================================
        # CHARTS SECTION
        # ============================================================
        # Charts container: Two charts side by side
        charts_container = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        charts_container.pack(fill="both", expand=True, pady=20)
        
        if MATPLOTLIB_AVAILABLE:
            # Chart 1: Bar Chart - Top 5 Components by Inventory Level
            self._create_bar_chart(charts_container, all_items)
            
            # Chart 2: Pie Chart - Item Status Distribution
            self._create_pie_chart(charts_container, all_items)
        else:
            # Fallback if matplotlib is not available
            no_charts_label = ctk.CTkLabel(
                charts_container,
                text="Install matplotlib to view charts: pip install matplotlib",
                font=ctk.CTkFont(size=14),
                text_color=self.colors["text_secondary"]
            )
            no_charts_label.pack(pady=50)
        
        # ============================================================
        # RECENT ACTIVITY SECTION
        # ============================================================
        # Recent Transactions card for activity feed
        activity_card = ctk.CTkFrame(
            scroll_frame,
            corner_radius=12,
            fg_color=self.colors["bg_secondary"],
            border_width=1,
            border_color=self.colors["border"]
        )
        activity_card.pack(fill="x", pady=(40, 0))
        
        # Section title
        activity_title = ctk.CTkLabel(
            activity_card,
            text="RECENT TRANSACTIONS",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=self.colors["text_secondary"]
        )
        activity_title.pack(pady=(30, 20), padx=30, anchor="w")
        
        # Activity list container
        activity_list = ctk.CTkFrame(activity_card, fg_color="transparent")
        activity_list.pack(fill="x", padx=30, pady=(0, 30))
        
        # Get recent transactions
        recent_transactions = self.db.get_recent_transactions(limit=5)
        
        if not recent_transactions:
            no_activity = ctk.CTkLabel(
                activity_list,
                text="No recent activity.",
                font=ctk.CTkFont(size=14),
                text_color=self.colors["text_secondary"]
            )
            no_activity.pack(pady=20)
        else:
            # Display each activity item
            for i, activity in enumerate(recent_transactions):
                self._create_activity_item(activity_list, activity, i == len(recent_transactions) - 1)
    
    def _create_activity_item(self, parent, activity: Dict, is_last: bool):
        """
        Create an activity item row for the Recent Transactions feed.
        
        Args:
            parent: Parent frame to add activity to
            activity: Activity dictionary with student_name, item_name, serial_number, action, timestamp
            is_last: Whether this is the last item (no bottom border)
        """
        activity_frame = ctk.CTkFrame(
            parent,
            fg_color="transparent",
            height=56
        )
        activity_frame.pack(fill="x", pady=(0, 0))
        activity_frame.pack_propagate(False)
        
        # Format timestamp (relative time)
        timestamp_str = self._format_timestamp(activity.get("timestamp", ""))
        
        # Activity text
        action_emoji = "📦" if activity["action"] == "Issue" else "↩️"
        activity_text = f"{action_emoji} {activity['student_name']} {activity['action'].lower()}ed {activity['item_name']} ({activity['serial_number']})"
        
        activity_label = ctk.CTkLabel(
            activity_frame,
            text=activity_text,
            font=ctk.CTkFont(size=14),
            text_color=self.colors["text_primary"],
            anchor="w"
        )
        activity_label.pack(side="left", padx=0, pady=16)
        
        # Timestamp
        time_label = ctk.CTkLabel(
            activity_frame,
            text=timestamp_str,
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_secondary"]
        )
        time_label.pack(side="right", padx=0, pady=16)
        
        # Bottom border (except for last item)
        if not is_last:
            border = ctk.CTkFrame(
                activity_frame,
                height=1,
                fg_color=self.colors["border"]
            )
            border.pack(side="bottom", fill="x", pady=(0, 0))
    
    def _format_timestamp(self, timestamp_str: str) -> str:
        """
        Format timestamp to relative time (e.g., "2 mins ago", "1 hour ago").
        
        This method handles ISO format timestamps and converts them to human-readable
        relative time for the activity feed.
        
        Args:
            timestamp_str: ISO format timestamp string (e.g., "2024-01-15T10:30:00")
            
        Returns:
            Formatted relative time string
        """
        if not timestamp_str:
            return "Just now"
        
        try:
            # Parse ISO timestamp - handle various formats
            # Remove 'Z' timezone indicator if present
            clean_timestamp = timestamp_str.replace('Z', '').replace('+00:00', '')
            
            # Try parsing with fromisoformat (Python 3.7+)
            try:
                timestamp = datetime.fromisoformat(clean_timestamp)
            except ValueError:
                # Fallback: try parsing common formats
                for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f']:
                    try:
                        timestamp = datetime.strptime(clean_timestamp, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    return "Recently"
            
            now = datetime.now()
            
            # Calculate difference
            diff = now - timestamp
            
            # Handle negative differences (future timestamps)
            if diff.total_seconds() < 0:
                return "Just now"
            
            # Format relative time
            if diff.total_seconds() < 60:
                return "Just now"
            elif diff.total_seconds() < 3600:
                mins = int(diff.total_seconds() / 60)
                return f"{mins} min{'s' if mins != 1 else ''} ago"
            elif diff.total_seconds() < 86400:
                hours = int(diff.total_seconds() / 3600)
                return f"{hours} hour{'s' if hours != 1 else ''} ago"
            else:
                days = int(diff.total_seconds() / 86400)
                return f"{days} day{'s' if days != 1 else ''} ago"
        except Exception as e:
            # Fallback for any parsing errors
            return "Recently"
    
    def _create_bar_chart(self, parent, all_items: List[Dict]):
        """
        Create a bar chart showing inventory levels for top 5 components.
        
        This method:
        1. Calculates available items per component
        2. Creates a matplotlib figure with dark theme
        3. Embeds it into a CustomTkinter frame
        
        Args:
            parent: The parent frame to embed the chart into
            all_items: List of all items from the database
        """
        # Get inventory data
        inventory_list = self.db.get_all_inventory()
        
        # Calculate available count for each inventory item
        component_data = {}
        for inv in inventory_list:
            available = sum(1 for item in all_items 
                          if item.get("inventory_id") == inv["id"] 
                          and item.get("status") == "Available")
            component_data[inv["name"]] = available
        
        # Sort by value and get top 5
        sorted_components = sorted(component_data.items(), key=lambda x: x[1], reverse=True)[:5]
        component_names = [item[0] for item in sorted_components]
        component_counts = [item[1] for item in sorted_components]
        
        # ============================================================
        # MATPLOTLIB INTEGRATION - Premium Zinc Palette
        # ============================================================
        # Step 1: Create a Figure object with zinc background
        # Using bg_secondary (#18181b) to match card backgrounds
        # This creates seamless visual integration
        fig = Figure(figsize=(5.5, 4.5), facecolor=self.colors["bg_secondary"], edgecolor=self.colors["bg_secondary"])
        
        # Step 2: Create a subplot (axes) on the figure
        ax = fig.add_subplot(111)
        
        # Step 3: Configure zinc palette for the plot
        # All backgrounds match our design system
        ax.set_facecolor(self.colors["bg_secondary"])  # Chart background
        fig.patch.set_facecolor(self.colors["bg_secondary"])  # Figure background
        
        # Step 4: Create the bar chart with subtle styling
        # Using white bars for contrast against dark background
        # This creates a clean, premium look
        bars = ax.bar(component_names, component_counts, color=self.colors["accent"], alpha=0.9)
        
        # Step 5: Style the chart - Premium Typography
        # All text uses text_secondary (#a1a1aa) for subtle, professional look
        ax.set_title("Top 5 Components - Available Stock", 
                    color=self.colors["text_primary"], fontsize=15, fontweight="bold", pad=24)
        ax.set_xlabel("Component", color=self.colors["text_secondary"], fontsize=12)
        ax.set_ylabel("Available Quantity", color=self.colors["text_secondary"], fontsize=12)
        
        # Set text colors to match zinc palette
        ax.tick_params(colors=self.colors["text_secondary"], labelsize=10)
        
        # Remove boxy borders - create clean, minimal look
        # Only show bottom and left spines for cleaner aesthetic
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color(self.colors["border"])
        ax.spines['left'].set_color(self.colors["border"])
        
        # Rotate x-axis labels if they're long
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", color=self.colors["text_secondary"])
        
        # Step 6: Embed the matplotlib figure into CustomTkinter
        # FigureCanvasTkAgg is the bridge between matplotlib and Tkinter
        # master: The parent widget (our CustomTkinter frame)
        # figure: The matplotlib figure we created
        canvas = FigureCanvasTkAgg(fig, master=parent)
        
        # Step 7: Draw the canvas and pack it
        # get_tk_widget(): Gets the Tkinter widget from the canvas
        # This allows us to use it with CustomTkinter's pack/grid system
        canvas.draw()
        canvas.get_tk_widget().pack(side="left", padx=20, pady=10, fill="both", expand=True)
    
    def _create_pie_chart(self, parent, all_items: List[Dict]):
        """
        Create a pie chart showing the distribution of item statuses.
        
        This chart shows the ratio of Available vs Issued vs Damaged items.
        
        Args:
            parent: The parent frame to embed the chart into
            all_items: List of all items from the database
        """
        # Count items by status
        status_counts = {
            "Available": sum(1 for item in all_items if item.get("status") == "Available"),
            "Issued": sum(1 for item in all_items if item.get("status") == "Issued"),
            "Damaged": sum(1 for item in all_items if item.get("status") == "Damaged")
        }
        
        # Filter out zero values for cleaner chart
        labels = []
        sizes = []
        colors_list = []
        
        # Color mapping: Change these hex codes to customize pie slice colors
        color_map = {
            "Available": "#4CAF50",  # Green
            "Issued": "#2196F3",     # Blue
            "Damaged": "#F44336"     # Red
        }
        
        for status, count in status_counts.items():
            if count > 0:
                labels.append(status)
                sizes.append(count)
                colors_list.append(color_map.get(status, "#808080"))
        
        if not sizes:  # No data to display
            return
        
        # Create figure with zinc palette
        fig = Figure(figsize=(5.5, 4.5), facecolor=self.colors["bg_secondary"], edgecolor=self.colors["bg_secondary"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(self.colors["bg_secondary"])
        fig.patch.set_facecolor(self.colors["bg_secondary"])
        
        # Create pie chart with status colors
        # autopct: Shows percentage on each slice
        # startangle: Rotates the pie (90 degrees = starts at top)
        wedges, texts, autotexts = ax.pie(
            sizes, 
            labels=labels, 
            autopct='%1.1f%%',
            startangle=90,
            colors=colors_list
        )
        
        # Style the text - Premium Typography
        ax.set_title("Item Status Distribution", 
                    color=self.colors["text_primary"], fontsize=15, fontweight="bold", pad=24)
        
        # Set label colors to secondary text color
        for text in texts:
            text.set_color(self.colors["text_secondary"])
            text.set_fontsize(12)
        
        # Set percentage text color to primary for readability
        for autotext in autotexts:
            autotext.set_color(self.colors["text_primary"])
            autotext.set_fontweight("bold")
        
        # Embed into CustomTkinter
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(side="left", padx=20, pady=10, fill="both", expand=True)
    
    def _show_issue_view(self):
        """
        Display the Issue Items view.
        
        This is the main workflow for issuing items to students.
        It includes:
        - Staff/Issuer selector at the top (tracks who is issuing)
        - Student selection dropdown (above search bar)
        - Input field for serial number or component name
        - Cart showing selected items
        - Finalize button
        """
        # Create scrollable container
        scroll_frame = ctk.CTkScrollableFrame(self.content_frame)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title = ctk.CTkLabel(
            scroll_frame,
            text="Issue Items",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title.pack(pady=(0, 30))
        
        # ============================================================
        # STAFF/ISSUER SELECTOR CARD - At the top
        # ============================================================
        issuer_card = ctk.CTkFrame(
            scroll_frame, 
            corner_radius=12,
            fg_color=self.colors["bg_secondary"],
            border_width=1,
            border_color=self.colors["border"]
        )
        issuer_card.pack(pady=20, padx=0, fill="x")
        
        issuer_label = ctk.CTkLabel(
            issuer_card,
            text="Select Issuer (Staff Member):",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["text_primary"]
        )
        issuer_label.pack(pady=(30, 12), padx=30, anchor="w")
        
        self.issuer_dropdown = ctk.CTkComboBox(
            issuer_card,
            values=[],
            width=400,
            font=ctk.CTkFont(size=15),
            fg_color=self.colors["bg_primary"],
            border_color=self.colors["border"],
            text_color=self.colors["text_primary"]
        )
        self.issuer_dropdown.pack(pady=(0, 30), padx=30, fill="x", anchor="w")
        self._load_staff()
        
        # ============================================================
        # STUDENT SELECTOR CARD - Above search bar
        # ============================================================
        student_card = ctk.CTkFrame(
            scroll_frame, 
            corner_radius=12,
            fg_color=self.colors["bg_secondary"],
            border_width=1,
            border_color=self.colors["border"]
        )
        student_card.pack(pady=20, padx=0, fill="x")
        
        student_label = ctk.CTkLabel(
            student_card,
            text="Select Student:",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["text_primary"]
        )
        student_label.pack(pady=(30, 12), padx=30, anchor="w")
        
        self.student_dropdown = ctk.CTkComboBox(
            student_card,
            values=[],
            width=400,
            font=ctk.CTkFont(size=15),
            fg_color=self.colors["bg_primary"],
            border_color=self.colors["border"],
            text_color=self.colors["text_primary"]
        )
        self.student_dropdown.pack(pady=(0, 30), padx=30, fill="x", anchor="w")
        self._load_students()
        
        # ============================================================
        # INPUT SECTION CARD - Premium Zinc Design
        # ============================================================
        # Card uses bg_secondary with border for depth
        # 30px internal padding creates premium spacing
        input_card = ctk.CTkFrame(
            scroll_frame, 
            corner_radius=12,
            fg_color=self.colors["bg_secondary"],
            border_width=1,
            border_color=self.colors["border"]
        )
        input_card.pack(pady=20, padx=0, fill="x")
        
        input_label = ctk.CTkLabel(
            input_card,
            text="Scan Serial # or Type Component Name",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["text_primary"]
        )
        input_label.pack(pady=(30, 12), padx=30, anchor="w")
        
        # Entry field with zinc styling
        self.issue_entry = ctk.CTkEntry(
            input_card,
            placeholder_text="Enter serial number or component name...",
            height=50,
            font=ctk.CTkFont(size=15),
            fg_color=self.colors["bg_primary"],
            border_color=self.colors["border"],
            text_color=self.colors["text_primary"]
        )
        self.issue_entry.pack(pady=(0, 12), padx=30, fill="x")
        self.issue_entry.bind("<Return>", lambda e: self._add_to_cart())
        
        # Add button with white accent
        add_btn = ctk.CTkButton(
            input_card,
            text="Add to List",
            command=self._add_to_cart,
            height=48,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=self.colors["accent"],
            text_color=self.colors["bg_primary"],
            hover_color="#e5e5e5",
            corner_radius=8
        )
        add_btn.pack(pady=(0, 30), padx=30, fill="x")
        
        # ============================================================
        # CART SECTION CARD
        # ============================================================
        cart_card = ctk.CTkFrame(
            scroll_frame, 
            corner_radius=12,
            fg_color=self.colors["bg_secondary"],
            border_width=1,
            border_color=self.colors["border"]
        )
        cart_card.pack(pady=20, padx=0, fill="both", expand=True)
        
        cart_label = ctk.CTkLabel(
            cart_card,
            text="Selected Items",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["text_primary"]
        )
        cart_label.pack(pady=(30, 12), padx=30, anchor="w")
        
        self.cart_scroll = ctk.CTkScrollableFrame(cart_card, height=300, fg_color="transparent")
        self.cart_scroll.pack(pady=(0, 20), padx=30, fill="both", expand=True)
        
        # ============================================================
        # CHECKOUT SECTION CARD
        # ============================================================
        checkout_card = ctk.CTkFrame(
            cart_card, 
            corner_radius=8,
            fg_color=self.colors["bg_primary"],
            border_width=1,
            border_color=self.colors["border"]
        )
        checkout_card.pack(pady=(0, 30), padx=30, fill="x")
        
        # Finalize button with white accent
        finalize_btn = ctk.CTkButton(
            checkout_card,
            text="Finalize Issue",
            command=self._finalize_issue,
            height=48,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=self.colors["accent"],
            text_color=self.colors["bg_primary"],
            hover_color="#e5e5e5",
            corner_radius=8
        )
        finalize_btn.pack(side="right", padx=20, pady=20)
        
        # Update cart display
        self._update_cart_display()
    
    def _show_returns_view(self):
        """
        Display the Returns view with split-screen UI.
        
        Left Column: Student search and selection
        Right Column: Active loans for selected student with Return/Damaged actions
        
        Design: Premium zinc palette with card-based layout
        """
        # Main container
        main_container = ctk.CTkFrame(
            self.content_frame,
            fg_color=self.colors["bg_primary"]
        )
        main_container.pack(fill="both", expand=True)
        
        # Title
        title = ctk.CTkLabel(
            main_container,
            text="Returns Management",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color=self.colors["text_primary"]
        )
        title.pack(pady=(0, 30), anchor="w", padx=0)
        
        # ============================================================
        # SPLIT-SCREEN LAYOUT
        # ============================================================
        # Container for left and right columns
        split_container = ctk.CTkFrame(main_container, fg_color="transparent")
        split_container.pack(fill="both", expand=True)
        split_container.grid_columnconfigure(0, weight=1)
        split_container.grid_columnconfigure(1, weight=1)
        split_container.grid_rowconfigure(0, weight=1)
        
        # ============================================================
        # LEFT COLUMN: STUDENT SEARCH
        # ============================================================
        left_card = ctk.CTkFrame(
            split_container,
            corner_radius=12,
            fg_color=self.colors["bg_secondary"],
            border_width=1,
            border_color=self.colors["border"]
        )
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12), pady=0)
        
        # Left column title
        left_title = ctk.CTkLabel(
            left_card,
            text="SEARCH STUDENT",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=self.colors["text_secondary"]
        )
        left_title.pack(pady=(30, 12), padx=30, anchor="w")
        
        # Search entry
        self.returns_search_entry = ctk.CTkEntry(
            left_card,
            placeholder_text="Enter Student ID or Name...",
            height=48,
            font=ctk.CTkFont(size=14),
            fg_color=self.colors["bg_primary"],
            border_color=self.colors["border"],
            text_color=self.colors["text_primary"]
        )
        self.returns_search_entry.pack(fill="x", padx=30, pady=(0, 20))
        self.returns_search_entry.bind("<KeyRelease>", lambda e: self._search_students_for_returns())
        
        # Results scrollable frame
        self.returns_students_list = ctk.CTkScrollableFrame(
            left_card,
            fg_color="transparent"
        )
        self.returns_students_list.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        
        # Store selected student
        self.selected_return_student = None
        
        # ============================================================
        # RIGHT COLUMN: ACTIVE LOANS
        # ============================================================
        right_card = ctk.CTkFrame(
            split_container,
            corner_radius=12,
            fg_color=self.colors["bg_secondary"],
            border_width=1,
            border_color=self.colors["border"]
        )
        right_card.grid(row=0, column=1, sticky="nsew", padx=(12, 0), pady=0)
        
        # Right column title
        right_title = ctk.CTkLabel(
            right_card,
            text="ACTIVE LOANS",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=self.colors["text_secondary"]
        )
        right_title.pack(pady=(30, 12), padx=30, anchor="w")
        
        # Active loans scrollable frame
        self.returns_loans_list = ctk.CTkScrollableFrame(
            right_card,
            fg_color="transparent"
        )
        self.returns_loans_list.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        
        # Initial state: Show placeholder
        self._show_returns_placeholder()
    
    def _search_students_for_returns(self):
        """
        Search for students and display results in the left column.
        
        This is called on every keystroke in the search field.
        """
        query = self.returns_search_entry.get().strip()
        
        # Clear existing results
        for widget in self.returns_students_list.winfo_children():
            widget.destroy()
        
        if not query:
            return
        
        # Search students
        students = self.db.search_students(query)
        
        if not students:
            no_results = ctk.CTkLabel(
                self.returns_students_list,
                text="No students found.",
                font=ctk.CTkFont(size=14),
                text_color=self.colors["text_secondary"]
            )
            no_results.pack(pady=20)
            return
        
        # Display student results
        for student in students:
            self._create_student_result_item(student)
    
    def _create_student_result_item(self, student: Dict):
        """
        Create a clickable student result item.
        
        Args:
            student: Student dictionary with id, name, student_id
        """
        student_frame = ctk.CTkFrame(
            self.returns_students_list,
            corner_radius=8,
            fg_color=self.colors["bg_primary"],
            border_width=1,
            border_color=self.colors["border"]
        )
        student_frame.pack(fill="x", pady=6, padx=0)
        
        # Student info
        info_text = f"{student['name']} ({student['student_id']})"
        student_label = ctk.CTkLabel(
            student_frame,
            text=info_text,
            font=ctk.CTkFont(size=14),
            text_color=self.colors["text_primary"]
        )
        student_label.pack(side="left", padx=20, pady=12)
        
        # Click handler: Select this student
        def select_student():
            self.selected_return_student = student
            self._load_active_loans(student["id"])
            # Highlight selected student
            for widget in self.returns_students_list.winfo_children():
                if isinstance(widget, ctk.CTkFrame):
                    widget.configure(border_color=self.colors["border"])
            student_frame.configure(border_color=self.colors["accent"], border_width=2)
        
        # Make entire frame clickable
        student_frame.bind("<Button-1>", lambda e: select_student())
        student_label.bind("<Button-1>", lambda e: select_student())
    
    def _load_active_loans(self, student_id: int):
        """
        Load and display active loans for the selected student.
        
        Args:
            student_id: The ID of the selected student
        """
        # Clear existing loans
        for widget in self.returns_loans_list.winfo_children():
            widget.destroy()
        
        # Get active loans
        loans = self.db.get_active_loans(student_id)
        
        if not loans:
            no_loans = ctk.CTkLabel(
                self.returns_loans_list,
                text="No active loans for this student.",
                font=ctk.CTkFont(size=14),
                text_color=self.colors["text_secondary"]
            )
            no_loans.pack(pady=30)
            return
        
        # Display each loaned item
        for loan in loans:
            self._create_loan_item(loan)
    
    def _create_loan_item(self, loan: Dict):
        """
        Create a loan item row with Return and Report Damaged buttons.
        
        Args:
            loan: Item dictionary with transaction info
        """
        loan_frame = ctk.CTkFrame(
            self.returns_loans_list,
            corner_radius=8,
            fg_color=self.colors["bg_primary"],
            border_width=1,
            border_color=self.colors["border"]
        )
        loan_frame.pack(fill="x", pady=8, padx=0)
        
        # Item info container
        info_container = ctk.CTkFrame(loan_frame, fg_color="transparent")
        info_container.pack(side="left", fill="x", expand=True, padx=20, pady=12)
        
        # Get inventory name
        inventory_name = "Unknown"
        if "inventory" in loan and loan["inventory"]:
            inventory_name = loan["inventory"].get("name", "Unknown")
        elif "inventory_id" in loan:
            inv_list = self.db.get_all_inventory()
            for inv in inv_list:
                if inv["id"] == loan["inventory_id"]:
                    inventory_name = inv["name"]
                    break
        
        # Item name and serial
        item_text = f"{inventory_name} - {loan.get('serial_number', 'N/A')}"
        item_label = ctk.CTkLabel(
            info_container,
            text=item_text,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors["text_primary"]
        )
        item_label.pack(anchor="w")
        
        # Buttons container
        buttons_container = ctk.CTkFrame(loan_frame, fg_color="transparent")
        buttons_container.pack(side="right", padx=20, pady=12)
        
        # Return button (Green)
        return_btn = ctk.CTkButton(
            buttons_container,
            text="Return",
            width=120,
            height=36,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=self.colors["status_available"],
            hover_color="#16a34a",
            corner_radius=8,
            command=lambda: self._handle_return_item(loan)
        )
        return_btn.pack(side="left", padx=(0, 8))
        
        # Report Damaged button (Red)
        damaged_btn = ctk.CTkButton(
            buttons_container,
            text="Report Damaged",
            width=140,
            height=36,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=self.colors["status_damaged"],
            hover_color="#dc2626",
            corner_radius=8,
            command=lambda: self._handle_report_damaged(loan)
        )
        damaged_btn.pack(side="left")
    
    def _handle_return_item(self, loan: Dict):
        """
        Handle returning an item: Set to Available and close transaction.
        
        Args:
            loan: Item dictionary with transaction_id
        """
        item_id = loan["id"]
        transaction_id = loan.get("transaction_id")
        
        if not transaction_id:
            self._show_error("Transaction ID not found.", "Error")
            return
        
        success = self.db.return_item(item_id, transaction_id)
        
        if success:
            # Refresh the loans list
            if self.selected_return_student:
                self._load_active_loans(self.selected_return_student["id"])
            
            # Show success message
            self._show_success(f"Item {loan.get('serial_number', 'N/A')} returned successfully!")
        else:
            self._show_error("Failed to return item. Please try again.", "Error")
    
    def _handle_report_damaged(self, loan: Dict):
        """
        Handle reporting an item as damaged: Set to Damaged and close transaction.
        
        Args:
            loan: Item dictionary with transaction_id
        """
        item_id = loan["id"]
        transaction_id = loan.get("transaction_id")
        
        if not transaction_id:
            self._show_error("Transaction ID not found.", "Error")
            return
        
        # Confirm action
        popup = ctk.CTkToplevel(self)
        popup.title("Confirm Damage Report")
        popup.geometry("500x280")
        popup.configure(bg=self.colors["bg_primary"])
        popup.transient(self)
        popup.grab_set()
        
        main_frame = ctk.CTkFrame(
            popup,
            fg_color=self.colors["bg_secondary"],
            corner_radius=12,
            border_width=1,
            border_color=self.colors["border"]
        )
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        label = ctk.CTkLabel(
            main_frame,
            text=f"Report {loan.get('serial_number', 'N/A')} as DAMAGED?\n\nThis will mark the item as damaged and close the transaction.",
            font=ctk.CTkFont(size=14),
            text_color=self.colors["status_damaged"],
            wraplength=430
        )
        label.pack(pady=40, padx=30)
        
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(pady=(0, 30))
        
        confirm_btn = ctk.CTkButton(
            btn_frame,
            text="Confirm",
            command=lambda: self._confirm_damage_report(loan, popup),
            fg_color=self.colors["status_damaged"],
            hover_color="#dc2626",
            height=40,
            corner_radius=8,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        confirm_btn.pack(side="left", padx=10)
        
        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=popup.destroy,
            fg_color="transparent",
            hover_color="#27272a",
            height=40,
            corner_radius=8,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors["text_primary"]
        )
        cancel_btn.pack(side="left", padx=10)
    
    def _confirm_damage_report(self, loan: Dict, popup):
        """Confirm and execute damage report."""
        popup.destroy()
        
        item_id = loan["id"]
        transaction_id = loan.get("transaction_id")
        
        success = self.db.report_damaged(item_id, transaction_id)
        
        if success:
            # Refresh the loans list
            if self.selected_return_student:
                self._load_active_loans(self.selected_return_student["id"])
            
            self._show_success(f"Item {loan.get('serial_number', 'N/A')} reported as damaged.")
        else:
            self._show_error("Failed to report damage. Please try again.", "Error")
    
    def _show_returns_placeholder(self):
        """Show placeholder message in loans list."""
        placeholder = ctk.CTkLabel(
            self.returns_loans_list,
            text="Select a student to view their active loans.",
            font=ctk.CTkFont(size=14),
            text_color=self.colors["text_secondary"]
        )
        placeholder.pack(pady=50)
    
    def _show_success(self, message: str):
        """Show success popup (simpler than error popup)."""
        popup = ctk.CTkToplevel(self)
        popup.title("Success")
        popup.geometry("450x200")
        popup.configure(bg=self.colors["bg_primary"])
        popup.transient(self)
        popup.grab_set()
        
        main_frame = ctk.CTkFrame(
            popup,
            fg_color=self.colors["bg_secondary"],
            corner_radius=12,
            border_width=1,
            border_color=self.colors["border"]
        )
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        label = ctk.CTkLabel(
            main_frame,
            text=message,
            font=ctk.CTkFont(size=14),
            text_color=self.colors["status_available"],
            wraplength=380
        )
        label.pack(pady=40, padx=30)
        
        btn = ctk.CTkButton(
            main_frame,
            text="OK",
            command=popup.destroy,
            fg_color=self.colors["status_available"],
            hover_color="#16a34a",
            height=40,
            corner_radius=8,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        btn.pack(pady=(0, 30))
    
    def _show_inventory_view(self):
        """Display the Inventory view with detailed inventory information."""
        # Create scrollable container
        scroll_frame = ctk.CTkScrollableFrame(
            self.content_frame,
            fg_color=self.colors["bg_primary"]
        )
        scroll_frame.pack(fill="both", expand=True)
        
        # Title row with Import CSV button
        title_container = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        title_container.pack(fill="x", pady=(0, 40))
        
        title = ctk.CTkLabel(
            title_container,
            text="Inventory Overview",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color=self.colors["text_primary"]
        )
        title.pack(side="left", anchor="w")
        
        # Button container for Import CSV and Add Component
        button_container = ctk.CTkFrame(title_container, fg_color="transparent")
        button_container.pack(side="right")
        
        # Add Component button - Premium design
        add_component_btn = ctk.CTkButton(
            button_container,
            text="Add Component",
            command=self._show_add_component_form,
            height=44,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.colors["status_available"],
            text_color="#ffffff",
            hover_color="#16a34a",
            corner_radius=8,
            width=160
        )
        add_component_btn.pack(side="left", padx=(0, 10))
        
        # Import CSV button - Premium design
        import_btn = ctk.CTkButton(
            button_container,
            text="Import CSV",
            command=self._handle_csv_import,
            height=44,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.colors["accent"],
            text_color=self.colors["bg_primary"],
            hover_color="#e5e5e5",
            corner_radius=8,
            width=140
        )
        import_btn.pack(side="left")
        
        # Load and display inventory
        self._load_inventory_display(scroll_frame)
    
    def _handle_csv_import(self):
        """
        Handle CSV import for bulk inventory creation.
        
        This opens a file dialog, parses the CSV, and creates inventory records
        with auto-generated serial numbers.
        """
        if not PANDAS_AVAILABLE:
            self._show_error(
                "Pandas is not installed. Install it with: pip install pandas",
                "Missing Dependency"
            )
            return
        
        # Open file dialog
        file_path = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not file_path:
            return  # User cancelled
        
        try:
            # Read CSV file
            # Expected columns: Component Name, Quantity, Description
            df = pd.read_csv(file_path)
            
            # Validate required columns
            required_columns = ['Component Name', 'Quantity']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                self._show_error(
                    f"CSV is missing required columns: {', '.join(missing_columns)}\n\n"
                    f"Required columns: Component Name, Quantity\n"
                    f"Optional columns: Description",
                    "Invalid CSV Format"
                )
                return
            
            # Convert DataFrame to list of dictionaries
            csv_data = df.to_dict('records')
            
            # Perform bulk import
            inventory_created, items_created = self.db.bulk_import_inventory(csv_data)
            
            # Show success message
            success_msg = (
                f"Import completed successfully!\n\n"
                f"Inventory records created: {inventory_created}\n"
                f"Item records created: {items_created}"
            )
            
            success_popup = ctk.CTkToplevel(self)
            success_popup.title("Import Success")
            success_popup.geometry("500x240")
            success_popup.configure(bg=self.colors["bg_primary"])
            success_popup.transient(self)
            success_popup.grab_set()
            
            main_frame = ctk.CTkFrame(
                success_popup,
                fg_color=self.colors["bg_secondary"],
                corner_radius=12,
                border_width=1,
                border_color=self.colors["border"]
            )
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            label = ctk.CTkLabel(
                main_frame,
                text=success_msg,
                font=ctk.CTkFont(size=14),
                text_color=self.colors["status_available"],
                wraplength=430,
                justify="left"
            )
            label.pack(pady=40, padx=30)
            
            btn = ctk.CTkButton(
                main_frame,
                text="OK",
                command=lambda: self._close_import_success(success_popup),
                fg_color=self.colors["status_available"],
                hover_color="#16a34a",
                height=40,
                corner_radius=8,
                font=ctk.CTkFont(size=14, weight="bold")
            )
            btn.pack(pady=(0, 30))
            
        except pd.errors.EmptyDataError:
            self._show_error("The CSV file is empty.", "Import Error")
        except pd.errors.ParserError as e:
            self._show_error(f"Error parsing CSV file: {str(e)}", "Import Error")
        except Exception as e:
            self._show_error(f"Error importing CSV: {str(e)}", "Import Error")
    
    def _close_import_success(self, popup):
        """Close import success popup and refresh inventory view."""
        popup.destroy()
        # Refresh the inventory view to show new items
        self._switch_view("inventory")
    
    def _show_add_component_form(self):
        """
        Show a dynamic form to add a new component.
        
        This form automatically detects all fields from the inventory schema
        and creates appropriate input fields. This makes it robust for future
        schema changes - if you add new fields to inventory, they'll automatically
        appear in this form.
        """
        # Get schema dynamically
        schema = self.db.get_inventory_schema()
        
        # Create popup window
        popup = ctk.CTkToplevel(self)
        popup.title("Add New Component")
        popup.geometry("600x700")
        popup.configure(bg=self.colors["bg_primary"])
        popup.transient(self)
        popup.grab_set()
        
        # Main frame
        main_frame = ctk.CTkFrame(
            popup,
            fg_color=self.colors["bg_secondary"],
            corner_radius=12,
            border_width=1,
            border_color=self.colors["border"]
        )
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title = ctk.CTkLabel(
            main_frame,
            text="Add New Component",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.colors["text_primary"]
        )
        title.pack(pady=(30, 20))
        
        # Scrollable form container
        form_scroll = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        form_scroll.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        
        # Store form fields dynamically
        form_fields = {}
        
        # Create form fields based on schema
        # Skip 'id' field as it's auto-generated
        for field_name, field_info in schema.items():
            if field_name == "id" or not field_info.get("editable", True):
                continue
            
            field_type = field_info.get("type", "str")
            is_required = field_info.get("required", False)
            
            # Field label
            label_text = field_name.replace("_", " ").title()
            if is_required:
                label_text += " *"
            
            label = ctk.CTkLabel(
                form_scroll,
                text=label_text,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=self.colors["text_primary"],
                anchor="w"
            )
            label.pack(anchor="w", pady=(15, 5), padx=10)
            
            # Create appropriate input field based on type
            if field_type == "int":
                entry = ctk.CTkEntry(
                    form_scroll,
                    placeholder_text=f"Enter {label_text.lower()}...",
                    height=40,
                    font=ctk.CTkFont(size=13),
                    fg_color=self.colors["bg_primary"],
                    border_color=self.colors["border"],
                    text_color=self.colors["text_primary"]
                )
            else:
                entry = ctk.CTkEntry(
                    form_scroll,
                    placeholder_text=f"Enter {label_text.lower()}...",
                    height=40,
                    font=ctk.CTkFont(size=13),
                    fg_color=self.colors["bg_primary"],
                    border_color=self.colors["border"],
                    text_color=self.colors["text_primary"]
                )
            
            entry.pack(fill="x", padx=10, pady=(0, 10))
            form_fields[field_name] = {"widget": entry, "type": field_type, "required": is_required}
        
        # Button container
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(pady=(0, 30), padx=30, fill="x")
        
        # Cancel button
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=popup.destroy,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="transparent",
            hover_color="#27272a",
            text_color=self.colors["text_primary"],
            corner_radius=8,
            width=120
        )
        cancel_btn.pack(side="left", padx=(0, 10))
        
        # Submit button
        submit_btn = ctk.CTkButton(
            button_frame,
            text="Add Component",
            command=lambda: self._submit_add_component(form_fields, popup),
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.colors["status_available"],
            hover_color="#16a34a",
            text_color="#ffffff",
            corner_radius=8,
            width=200
        )
        submit_btn.pack(side="right")
    
    def _submit_add_component(self, form_fields: Dict, popup):
        """
        Submit the add component form.
        
        Args:
            form_fields: Dictionary of form field widgets and metadata
            popup: The popup window to close on success
        """
        # Collect form data
        inventory_data = {}
        errors = []
        
        for field_name, field_info in form_fields.items():
            widget = field_info["widget"]
            field_type = field_info["type"]
            is_required = field_info["required"]
            
            value = widget.get().strip()
            
            # Validate required fields
            if is_required and not value:
                errors.append(f"{field_name.replace('_', ' ').title()} is required")
                continue
            
            # Convert and validate based on type
            if field_type == "int":
                try:
                    if value:
                        inventory_data[field_name] = int(value)
                    elif is_required:
                        errors.append(f"{field_name.replace('_', ' ').title()} must be a number")
                except ValueError:
                    errors.append(f"{field_name.replace('_', ' ').title()} must be a valid number")
            else:
                if value:
                    inventory_data[field_name] = value
        
        # Show errors if any
        if errors:
            error_msg = "Please fix the following errors:\n\n" + "\n".join(f"• {e}" for e in errors)
            self._show_error(error_msg, "Validation Error")
            return
        
        # Create inventory
        inventory_id = self.db.create_inventory(inventory_data)
        
        if inventory_id:
            # Success
            success_popup = ctk.CTkToplevel(self)
            success_popup.title("Success")
            success_popup.geometry("500x200")
            success_popup.configure(bg=self.colors["bg_primary"])
            success_popup.transient(self)
            success_popup.grab_set()
            
            main_frame = ctk.CTkFrame(
                success_popup,
                fg_color=self.colors["bg_secondary"],
                corner_radius=12,
                border_width=1,
                border_color=self.colors["border"]
            )
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            label = ctk.CTkLabel(
                main_frame,
                text=f"Component '{inventory_data.get('name', 'N/A')}' added successfully!",
                font=ctk.CTkFont(size=14),
                text_color=self.colors["status_available"],
                wraplength=430
            )
            label.pack(pady=40, padx=30)
            
            btn = ctk.CTkButton(
                main_frame,
                text="OK",
                command=lambda: self._close_add_component_success(success_popup, popup),
                fg_color=self.colors["status_available"],
                hover_color="#16a34a",
                height=40,
                corner_radius=8,
                font=ctk.CTkFont(size=14, weight="bold")
            )
            btn.pack(pady=(0, 30))
        else:
            self._show_error("Failed to create component. Please try again.", "Error")
    
    def _close_add_component_success(self, success_popup, form_popup):
        """Close success popup and form, then refresh inventory view."""
        success_popup.destroy()
        form_popup.destroy()
        # Refresh the inventory view to show new component
        self._switch_view("inventory")
    
    def _load_students(self):
        """Load students into dropdown."""
        students = self.db.get_all_students()
        student_values = [f"{s['name']} ({s['student_id']})" for s in students]
        self.student_dropdown.configure(values=student_values)
        if student_values:
            self.student_dropdown.set(student_values[0])
    
    def _load_staff(self):
        """Load staff/issuers into dropdown (for Issue Items view)."""
        staff = self.db.get_all_staff()
        staff_values = [f"{s['name']} ({s['staff_id']})" for s in staff]
        if hasattr(self, 'issuer_dropdown'):
            self.issuer_dropdown.configure(values=staff_values)
            if staff_values:
                self.issuer_dropdown.set(staff_values[0])
    
    def _load_global_staff(self):
        """Load staff/issuers into global header dropdown."""
        staff = self.db.get_all_staff()
        staff_values = [f"{s['name']} ({s['staff_id']})" for s in staff]
        if hasattr(self, 'global_issuer_dropdown'):
            self.global_issuer_dropdown.configure(values=staff_values)
            if staff_values:
                self.global_issuer_dropdown.set(staff_values[0])
                # Set initial issuer
                self._on_issuer_changed(staff_values[0])
    
    def _on_issuer_changed(self, value: str):
        """Handle global issuer selection change."""
        if not value:
            return
        
        staff = self.db.get_all_staff()
        for s in staff:
            if f"{s['name']} ({s['staff_id']})" == value:
                self.current_issuer_id = s["id"]
                self.current_issuer_name = s["name"]
                # Also update Issue Items view if it exists
                if hasattr(self, 'issuer_dropdown'):
                    self.issuer_dropdown.set(value)
                break
    
    def _sync_data(self):
        """
        Sync data from Supabase - refreshes all data and reloads current view.
        
        This method:
        1. Reconnects to Supabase using stored credentials
        2. Refreshes all data from the database
        3. Reloads the current view to show updated data
        4. Shows a success/error message
        """
        # Get credentials from stored values or environment
        supabase_url = getattr(self, 'supabase_url', None) or os.getenv("SUPABASE_URL")
        supabase_key = getattr(self, 'supabase_key', None) or os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        # Try to reconnect to Supabase
        try:
            # Reinitialize database manager with current credentials
            # This will reconnect if Supabase is available
            self.db = DatabaseManager(supabase_url, supabase_key)
            
            # Reload global staff dropdown
            self._load_global_staff()
            
            # Refresh the current view to show updated data
            current_view = self.current_view
            self._switch_view(current_view)
            
            # Show success message
            if not self.db.use_mock:
                self._show_success("Data synced successfully from Supabase!")
            else:
                self._show_error("Not connected to Supabase. Using mock data.", "Sync Warning")
        except Exception as e:
            self._show_error(f"Error syncing data: {str(e)}", "Sync Error")
    
    def _add_to_cart(self):
        """
        Add item to cart based on user input.
        
        This method implements the "smart" logic:
        - If input matches a serial number → Check status and handle accordingly
        - If input is a component name → Show popup with available serial numbers
        
        The method first tries to find by serial number (exact match),
        then falls back to component name search if no serial match is found.
        """
        # Get input text and remove leading/trailing whitespace
        input_text = self.issue_entry.get().strip()
        
        # Validation: Check if input is empty
        if not input_text:
            self._show_error("Please enter a serial number or component name.")
            return
        
        # Strategy: Try serial number lookup first (more specific)
        # This is faster and more accurate than component name search
        item = self.db.get_item_by_serial(input_text)
        
        if item:
            # Found by serial number → Handle based on item status
            self._handle_serial_number(item)
        else:
            # Not found by serial → Try component name search
            # This will show a popup if multiple items are available
            self._handle_component_name(input_text)
    
    def _handle_serial_number(self, item: Dict):
        """
        Handle when user enters a serial number.
        
        This method implements the status checking logic:
        - "Issued" → Show RED error (item already in use)
        - "Damaged" → Show YELLOW warning (ask for confirmation)
        - "Available" → Add directly to cart (green path)
        - Other statuses → Show error (invalid state)
        
        Args:
            item: Dictionary containing item data from database
        """
        # Get status and convert to lowercase for case-insensitive comparison
        status = item.get("status", "").lower()
        
        if status == "issued":
            # RED ERROR: Item is already issued to another student
            # This prevents double-issuing
            self._show_error("Item already issued!", "Error")
            return
        elif status == "damaged":
            # YELLOW WARNING: Item is damaged but can still be issued with confirmation
            # This allows flexibility for special cases
            self._show_warning(item)
        elif status == "available":
            # GREEN PATH: Item is available, add directly to cart
            self._add_item_to_cart(item)
        else:
            # Unknown status: Show error for safety
            self._show_error(f"Item status: {status}. Cannot issue.", "Error")
    
    def _handle_component_name(self, component_name: str):
        """Handle when user enters a component name."""
        available_items = self.db.get_available_items_by_name(component_name)
        
        if not available_items:
            self._show_error(f"No available items found for '{component_name}'.", "Not Found")
            return
        
        # Open popup to select serial number
        popup = ComponentSelectionPopup(self, available_items, self._add_item_to_cart)
        popup.focus()
    
    def _add_item_to_cart(self, item: Dict):
        """Add item to cart."""
        # Check if already in cart
        for cart_item in self.cart_items:
            if cart_item["id"] == item["id"]:
                self._show_error("Item already in cart!", "Duplicate")
                return
        
        self.cart_items.append(item)
        self.issue_entry.delete(0, "end")
        self._update_cart_display()
    
    def _show_error(self, message: str, title: str = "Error"):
        """Show error popup with zinc palette styling."""
        popup = ctk.CTkToplevel(self)
        popup.title(title)
        popup.geometry("450x220")
        popup.configure(bg=self.colors["bg_primary"])
        popup.transient(self)
        popup.grab_set()
        
        # Main frame with zinc styling
        main_frame = ctk.CTkFrame(
            popup,
            fg_color=self.colors["bg_secondary"],
            corner_radius=12,
            border_width=1,
            border_color=self.colors["border"]
        )
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        label = ctk.CTkLabel(
            main_frame,
            text=message,
            font=ctk.CTkFont(size=14),
            text_color=self.colors["status_damaged"],
            wraplength=380
        )
        label.pack(pady=40, padx=30)
        
        btn = ctk.CTkButton(
            main_frame,
            text="OK",
            command=popup.destroy,
            fg_color=self.colors["status_damaged"],
            hover_color="#dc2626",
            height=40,
            corner_radius=8,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        btn.pack(pady=(0, 30))
    
    def _show_warning(self, item: Dict):
        """Show warning popup for damaged items with zinc styling."""
        popup = ctk.CTkToplevel(self)
        popup.title("Warning")
        popup.geometry("500x280")
        popup.configure(bg=self.colors["bg_primary"])
        popup.transient(self)
        popup.grab_set()
        
        main_frame = ctk.CTkFrame(
            popup,
            fg_color=self.colors["bg_secondary"],
            corner_radius=12,
            border_width=1,
            border_color=self.colors["border"]
        )
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        label = ctk.CTkLabel(
            main_frame,
            text=f"Item {item['serial_number']} is marked as DAMAGED.\n\nDo you want to issue it anyway?",
            font=ctk.CTkFont(size=14),
            text_color="#f59e0b",  # Amber for warning
            wraplength=430
        )
        label.pack(pady=40, padx=30)
        
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(pady=(0, 30))
        
        confirm_btn = ctk.CTkButton(
            btn_frame,
            text="Confirm Issue",
            command=lambda: self._confirm_damaged_issue(item, popup),
            fg_color="#f59e0b",
            hover_color="#d97706",
            height=40,
            corner_radius=8,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        confirm_btn.pack(side="left", padx=10)
        
        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=popup.destroy,
            fg_color="transparent",
            hover_color="#27272a",
            height=40,
            corner_radius=8,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors["text_primary"]
        )
        cancel_btn.pack(side="left", padx=10)
    
    def _confirm_damaged_issue(self, item: Dict, popup):
        """Confirm issuing a damaged item."""
        popup.destroy()
        self._add_item_to_cart(item)
    
    def _update_cart_display(self):
        """Update the cart display."""
        # Clear existing widgets
        for widget in self.cart_scroll.winfo_children():
            widget.destroy()
        
        if not self.cart_items:
            empty_label = ctk.CTkLabel(
                self.cart_scroll,
                text="Cart is empty. Add items to get started.",
                font=ctk.CTkFont(size=14),
                text_color=self.colors["text_secondary"]
            )
            empty_label.pack(pady=50)
            return
        
        # Display items with premium card design
        for item in self.cart_items:
            item_frame = ctk.CTkFrame(
                self.cart_scroll, 
                corner_radius=8,
                fg_color=self.colors["bg_primary"],
                border_width=1,
                border_color=self.colors["border"]
            )
            item_frame.pack(fill="x", pady=6, padx=0)
            
            # Get inventory name
            inventory_name = "Unknown"
            if "inventory" in item and item["inventory"]:
                inventory_name = item["inventory"].get("name", "Unknown")
            elif "inventory_id" in item:
                inv_list = self.db.get_all_inventory()
                for inv in inv_list:
                    if inv["id"] == item["inventory_id"]:
                        inventory_name = inv["name"]
                        break
            
            info_text = f"{inventory_name} - {item['serial_number']}"
            info_label = ctk.CTkLabel(
                item_frame,
                text=info_text,
                font=ctk.CTkFont(size=14),
                text_color=self.colors["text_primary"]
            )
            info_label.pack(side="left", padx=20, pady=12)
            
            remove_btn = ctk.CTkButton(
                item_frame,
                text="Remove",
                width=100,
                height=32,
                command=lambda i=item: self._remove_from_cart(i),
                fg_color=self.colors["status_damaged"],
                hover_color="#dc2626",
                corner_radius=6,
                font=ctk.CTkFont(size=12, weight="bold")
            )
            remove_btn.pack(side="right", padx=20, pady=12)
    
    def _remove_from_cart(self, item: Dict):
        """Remove item from cart."""
        self.cart_items = [i for i in self.cart_items if i["id"] != item["id"]]
        self._update_cart_display()
    
    def _finalize_issue(self):
        """Finalize the issue transaction."""
        if not self.cart_items:
            self._show_error("Cart is empty. Add items before finalizing.", "Empty Cart")
            return
        
        # Use global issuer if available, otherwise try to get from Issue Items view
        issuer_id = None
        if self.current_issuer_id:
            issuer_id = self.current_issuer_id
        elif hasattr(self, 'issuer_dropdown'):
            issuer_value = self.issuer_dropdown.get()
            if issuer_value:
                staff = self.db.get_all_staff()
                for s in staff:
                    if f"{s['name']} ({s['staff_id']})" == issuer_value:
                        issuer_id = s["id"]
                        break
        
        if not issuer_id:
            self._show_error("Please select an issuer (staff member) from the top right selector.", "No Issuer Selected")
            return
        
        # Get student
        student_value = self.student_dropdown.get()
        if not student_value:
            self._show_error("Please select a student.", "No Student Selected")
            return
        
        # Extract student ID from dropdown value
        students = self.db.get_all_students()
        selected_student = None
        for student in students:
            if f"{student['name']} ({student['student_id']})" == student_value:
                selected_student = student
                break
        
        if not selected_student:
            self._show_error("Invalid student selection.", "Error")
            return
        
        # Create transaction with issuer_id (already validated above)
        item_ids = [item["id"] for item in self.cart_items]
        transaction_id = self.db.create_transaction(selected_student["id"], item_ids, issuer_id=issuer_id)
        
        if transaction_id:
            # Success popup with zinc styling
            success_popup = ctk.CTkToplevel(self)
            success_popup.title("Success")
            success_popup.geometry("500x240")
            success_popup.configure(bg=self.colors["bg_primary"])
            success_popup.transient(self)
            success_popup.grab_set()
            
            main_frame = ctk.CTkFrame(
                success_popup,
                fg_color=self.colors["bg_secondary"],
                corner_radius=12,
                border_width=1,
                border_color=self.colors["border"]
            )
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            label = ctk.CTkLabel(
                main_frame,
                text=f"Transaction #{transaction_id} created successfully!\n\n{len(self.cart_items)} item(s) issued to {selected_student['name']}.",
                font=ctk.CTkFont(size=14),
                text_color=self.colors["status_available"],
                wraplength=430
            )
            label.pack(pady=40, padx=30)
            
            btn = ctk.CTkButton(
                main_frame,
                text="OK",
                command=lambda: self._close_success_popup(success_popup),
                fg_color=self.colors["status_available"],
                hover_color="#16a34a",
                height=40,
                corner_radius=8,
                font=ctk.CTkFont(size=14, weight="bold")
            )
            btn.pack(pady=(0, 30))
        else:
            self._show_error("Failed to create transaction. Please try again.", "Error")
    
    def _close_success_popup(self, popup):
        """Close success popup and clear cart."""
        popup.destroy()
        self.cart_items = []
        self._update_cart_display()
        self.issue_entry.delete(0, "end")
    
    def _load_inventory_display(self, parent):
        """
        Load and display inventory items in a card-based table format.
        
        This method:
        1. Fetches inventory and item data from the database
        2. Calculates statistics (available, issued, damaged counts)
        3. Displays them in a table-like card layout
        
        Args:
            parent: The parent frame to display inventory in
        """
        inventory_list = self.db.get_all_inventory()
        items_list = self.db.get_all_items()
        
        if not inventory_list:
            label = ctk.CTkLabel(
                parent,
                text="No inventory items found.",
                font=ctk.CTkFont(size=16),
                text_color="gray"
            )
            label.pack(pady=50)
            return
        
        # ============================================================
        # TABLE HEADER CARD - Premium Design
        # ============================================================
        header_card = ctk.CTkFrame(
            parent, 
            corner_radius=12,
            fg_color=self.colors["bg_secondary"],
            border_width=1,
            border_color=self.colors["border"]
        )
        header_card.pack(fill="x", pady=(0, 12), padx=0)
        
        # Column headers: Uppercase, small, secondary color
        headers = ["Component Name", "Total Quantity", "Available", "Issued", "Damaged"]
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(
                header_card,
                text=header.upper(),
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=self.colors["text_secondary"]
            )
            label.grid(row=0, column=i, padx=30, pady=20, sticky="w")
        
        # ============================================================
        # INVENTORY DATA ROWS (CARD-BASED)
        # ============================================================
        # Each inventory item gets its own card for better visual separation
        for inv in inventory_list:
            # Calculate statistics for this inventory item
            # This loops through all items and counts by status
            available = sum(1 for item in items_list 
                          if item.get("inventory_id") == inv["id"] 
                          and item.get("status") == "Available")
            issued = sum(1 for item in items_list 
                        if item.get("inventory_id") == inv["id"] 
                        and item.get("status") == "Issued")
            damaged = sum(1 for item in items_list 
                         if item.get("inventory_id") == inv["id"] 
                         and item.get("status") == "Damaged")
            
            # Data row card: Premium card design
            row_card = ctk.CTkFrame(
                parent, 
                corner_radius=12,
                fg_color=self.colors["bg_secondary"],
                border_width=1,
                border_color=self.colors["border"]
            )
            row_card.pack(fill="x", pady=8, padx=0)
            
            # Component name
            name_label = ctk.CTkLabel(
                row_card, 
                text=inv["name"], 
                font=ctk.CTkFont(size=15),
                text_color=self.colors["text_primary"]
            )
            name_label.grid(row=0, column=0, padx=30, pady=20, sticky="w")
            
            # Total quantity
            total_label = ctk.CTkLabel(
                row_card, 
                text=str(inv.get("total_qty", 0)), 
                font=ctk.CTkFont(size=15),
                text_color=self.colors["text_primary"]
            )
            total_label.grid(row=0, column=1, padx=30, pady=20, sticky="w")
            
            # Available count - Status color
            avail_label = ctk.CTkLabel(
                row_card, 
                text=str(available), 
                font=ctk.CTkFont(size=15), 
                text_color=self.colors["status_available"]
            )
            avail_label.grid(row=0, column=2, padx=30, pady=20, sticky="w")
            
            # Issued count
            issued_label = ctk.CTkLabel(
                row_card, 
                text=str(issued), 
                font=ctk.CTkFont(size=15), 
                text_color=self.colors["status_issued"]
            )
            issued_label.grid(row=0, column=3, padx=30, pady=20, sticky="w")
            
            # Damaged count
            damaged_label = ctk.CTkLabel(
                row_card, 
                text=str(damaged), 
                font=ctk.CTkFont(size=15), 
                text_color=self.colors["status_damaged"]
            )
            damaged_label.grid(row=0, column=4, padx=30, pady=20, sticky="w")
    
    def _show_catalog_view(self):
        """
        Display the Catalog view - Master Inventory Data Table.
        
        This is a powerful data table view showing all items with:
        - Search functionality (by serial number or component name)
        - Filter pills for status filtering
        - Professional table layout with status badges
        - Scrollable rows for large datasets
        - Overdue item highlighting (red borders and text)
        
        Design principles:
        - Clean table design with subtle borders
        - Status badges use colored pills for quick visual scanning
        - Generous spacing for readability
        - Overdue items stand out with red highlighting
        """
        # Refresh overdue tracking when Catalog is opened
        overdue_items = self.db.get_overdue_items(days_threshold=7)
        self.overdue_item_ids = {item["id"] for item in overdue_items}
        
        # Create main container - make it scrollable so all content is accessible
        main_container = ctk.CTkScrollableFrame(
            self.content_frame,
            fg_color=self.colors["bg_primary"]
        )
        main_container.pack(fill="both", expand=True)
        
        # Title
        title = ctk.CTkLabel(
            main_container,
            text="Catalog",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color=self.colors["text_primary"]
        )
        title.pack(pady=(0, 30), anchor="w", padx=0)
        
        # ============================================================
        # SEARCH AND FILTER SECTION
        # ============================================================
        # Search card: Contains search bar and filter pills
        search_card = ctk.CTkFrame(
            main_container,
            corner_radius=12,
            fg_color=self.colors["bg_secondary"],
            border_width=1,
            border_color=self.colors["border"]
        )
        search_card.pack(fill="x", pady=(0, 20))
        
        # Search bar container
        search_container = ctk.CTkFrame(search_card, fg_color="transparent")
        search_container.pack(fill="x", padx=30, pady=20)
        
        # Search label - Uppercase, small, secondary color
        search_label = ctk.CTkLabel(
            search_container,
            text="SEARCH",
            font=ctk.CTkFont(size=10, weight="normal"),
            text_color=self.colors["text_secondary"]
        )
        search_label.pack(anchor="w", pady=(0, 8))
        
        # Search entry - Wide search bar
        # Height: 48px for comfortable input
        self.catalog_search_entry = ctk.CTkEntry(
            search_container,
            placeholder_text="Search by Serial # or Component Name...",
            height=48,
            font=ctk.CTkFont(size=14),
            fg_color=self.colors["bg_primary"],
            border_color=self.colors["border"],
            text_color=self.colors["text_primary"]
        )
        self.catalog_search_entry.pack(fill="x")
        # Bind search on text change for real-time filtering
        self.catalog_search_entry.bind("<KeyRelease>", lambda e: self._filter_catalog_table())
        
        # Filter pills container
        filter_container = ctk.CTkFrame(search_card, fg_color="transparent")
        filter_container.pack(fill="x", padx=30, pady=(0, 20))
        
        # Status filter section
        status_filter_label = ctk.CTkLabel(
            filter_container,
            text="FILTER BY STATUS",
            font=ctk.CTkFont(size=10, weight="normal"),
            text_color=self.colors["text_secondary"]
        )
        status_filter_label.pack(anchor="w", pady=(0, 12))
        
        # Status filter pills frame
        status_pills_frame = ctk.CTkFrame(filter_container, fg_color="transparent")
        status_pills_frame.pack(anchor="w", pady=(0, 20))
        
        # Store filter state
        self.catalog_filter_status = "All"
        self.catalog_filter_course = "All"
        
        # Status filter pills: Small clickable badges
        # Design: Transparent background, white text when active
        # Spacing: 8px between pills for clean grouping
        status_filter_options = ["All", "Available", "Issued", "Damaged"]
        self.filter_buttons = {}
        
        for i, status in enumerate(status_filter_options):
            btn = ctk.CTkButton(
                status_pills_frame,
                text=status,
                width=100,
                height=32,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=self.colors["accent"] if status == "All" else "transparent",
                text_color=self.colors["bg_primary"] if status == "All" else self.colors["text_primary"],
                hover_color="#27272a",
                corner_radius=16,  # Pill shape
                command=lambda s=status: self._set_catalog_filter(s)
            )
            btn.pack(side="left", padx=(0, 8))
            self.filter_buttons[status] = btn
        
        # Course filter section
        course_filter_label = ctk.CTkLabel(
            filter_container,
            text="FILTER BY COURSE",
            font=ctk.CTkFont(size=10, weight="normal"),
            text_color=self.colors["text_secondary"]
        )
        course_filter_label.pack(anchor="w", pady=(0, 12))
        
        # Course filter pills frame
        course_pills_frame = ctk.CTkFrame(filter_container, fg_color="transparent")
        course_pills_frame.pack(anchor="w")
        
        # Get unique courses from inventory
        all_inventory = self.db.get_all_inventory()
        # Filter out None, empty strings, and only include actual course codes
        unique_courses = sorted(set([
            inv.get("course") for inv in all_inventory 
            if inv.get("course") and str(inv.get("course")).strip() and inv.get("course") != "N/A"
        ]))
        course_filter_options = ["All"] + unique_courses
        self.course_filter_buttons = {}
        
        for i, course in enumerate(course_filter_options):
            btn = ctk.CTkButton(
                course_pills_frame,
                text=course,
                width=100,
                height=32,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=self.colors["accent"] if course == "All" else "transparent",
                text_color=self.colors["bg_primary"] if course == "All" else self.colors["text_primary"],
                hover_color="#27272a",
                corner_radius=16,  # Pill shape
                command=lambda c=course: self._set_catalog_course_filter(c)
            )
            btn.pack(side="left", padx=(0, 8))
            self.course_filter_buttons[course] = btn
        
        # ============================================================
        # DATA TABLE SECTION
        # ============================================================
        # Table card: Contains the actual data table
        table_card = ctk.CTkFrame(
            main_container,
            corner_radius=12,
            fg_color=self.colors["bg_secondary"],
            border_width=1,
            border_color=self.colors["border"]
        )
        # Pack table card to fill horizontally and size to content vertically
        # This allows the scrollable main_container to handle scrolling
        table_card.pack(fill="x", pady=(0, 20))
        
        # Table header
        header_frame = ctk.CTkFrame(table_card, fg_color="transparent")
        header_frame.pack(fill="x", padx=30, pady=(30, 0))
        
        # Column headers: Uppercase, small, secondary color
        # Grid layout for aligned columns
        headers = ["Component", "Serial #", "Course", "Status", "Issued To"]
        column_widths = [250, 150, 120, 120, 200]  # Column widths in pixels
        
        for i, (header, width) in enumerate(zip(headers, column_widths)):
            header_label = ctk.CTkLabel(
                header_frame,
                text=header.upper(),
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=self.colors["text_secondary"],
                width=width,
                anchor="w"
            )
            header_label.grid(row=0, column=i, padx=(0, 20), sticky="w")
        
        # Divider line under header
        divider = ctk.CTkFrame(
            header_frame,
            height=1,
            fg_color=self.colors["border"]
        )
        divider.grid(row=1, column=0, columnspan=5, sticky="ew", pady=(12, 0))
        header_frame.grid_columnconfigure(0, weight=1)
        
        # Scrollable table body
        # Set a minimum height to ensure it's visible and scrollable
        self.catalog_table_body = ctk.CTkScrollableFrame(
            table_card,
            fg_color="transparent",
            height=500  # Minimum height to ensure visibility and enable scrolling
        )
        self.catalog_table_body.pack(fill="both", expand=True, padx=30, pady=(20, 30))
        
        # Ensure search entry is empty and filters are set to "All" before loading
        # This ensures all items are displayed on initial load
        if hasattr(self, 'catalog_search_entry'):
            try:
                self.catalog_search_entry.delete(0, "end")
            except:
                pass
        
        # Ensure filters are initialized to "All"
        self.catalog_filter_status = "All"
        self.catalog_filter_course = "All"
        
        # Load and display table data immediately
        # Use update_idletasks to ensure UI is ready
        self.update_idletasks()
        self._load_catalog_table()
    
    def _set_catalog_filter(self, status: str):
        """
        Set the catalog filter status and update button states.
        
        Args:
            status: One of "All", "Available", "Issued", "Damaged"
        """
        self.catalog_filter_status = status
        
        # Update button states
        for btn_status, btn in self.filter_buttons.items():
            if btn_status == status:
                btn.configure(
                    fg_color=self.colors["accent"],
                    text_color=self.colors["bg_primary"]
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=self.colors["text_primary"]
                )
        
        # Refresh table
        self._filter_catalog_table()
    
    def _set_catalog_course_filter(self, course: str):
        """
        Set the catalog course filter and update button states.
        
        Args:
            course: Course code (e.g., "ECE101", "CS201") or "All"
        """
        self.catalog_filter_course = course
        
        # Update button states
        for btn_course, btn in self.course_filter_buttons.items():
            if btn_course == course:
                btn.configure(
                    fg_color=self.colors["accent"],
                    text_color=self.colors["bg_primary"]
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=self.colors["text_primary"]
                )
        
        # Refresh table
        self._filter_catalog_table()
    
    def _filter_catalog_table(self):
        """
        Filter and display the catalog table based on search and status filter.
        
        This method:
        1. Gets search query from entry field
        2. Applies status filter
        3. Filters items from database
        4. Updates the table display
        5. Highlights overdue items in red
        """
        # Safety check: Ensure required attributes exist
        if not hasattr(self, 'catalog_table_body'):
            return
        
        # Refresh overdue tracking (in case items were returned/issued)
        overdue_items = self.db.get_overdue_items(days_threshold=7)
        self.overdue_item_ids = {item["id"] for item in overdue_items}
        
        # Get search query - ensure it's empty string if entry doesn't exist
        search_query = ""
        if hasattr(self, 'catalog_search_entry'):
            try:
                search_query = self.catalog_search_entry.get().strip().lower()
            except (AttributeError, Exception):
                search_query = ""
        
        # Ensure filter status is initialized
        if not hasattr(self, 'catalog_filter_status'):
            self.catalog_filter_status = "All"
        if not hasattr(self, 'catalog_filter_course'):
            self.catalog_filter_course = "All"
        
        # Get all items
        all_items = self.db.get_all_items()
        
        if not all_items:
            # Clear table body and show message
            for widget in self.catalog_table_body.winfo_children():
                widget.destroy()
            empty_label = ctk.CTkLabel(
                self.catalog_table_body,
                text="No items found in database. Add items through the Inventory tab.",
                font=ctk.CTkFont(size=14),
                text_color=self.colors["text_secondary"]
            )
            empty_label.pack(pady=50)
            return
        
        # Debug: Print item details
        print(f"Catalog: Retrieved {len(all_items)} items, status_filter='{self.catalog_filter_status}', course_filter='{self.catalog_filter_course}', search='{search_query}'")
        
        all_students = self.db.get_all_students()
        
        # Create student lookup dictionary for "Issued To" column
        student_lookup = {s["id"]: s["name"] for s in all_students}
        
        # Filter items
        filtered_items = []
        for item in all_items:
            # Status filter - only apply if not "All"
            # Use case-insensitive comparison to handle any case variations
            if self.catalog_filter_status != "All":
                item_status = str(item.get("status", "")).strip()
                filter_status = str(self.catalog_filter_status).strip()
                if item_status != filter_status:
                    continue
            
            # Course filter - only apply if not "All"
            if self.catalog_filter_course != "All":
                # Get course from inventory
                item_course = None
                inventory = item.get("inventory", {})
                if isinstance(inventory, dict) and inventory:
                    item_course = inventory.get("course")
                else:
                    # If inventory is not a dict, try to get from inventory_id
                    inventory_id = item.get("inventory_id")
                    if inventory_id:
                        all_inventory = self.db.get_all_inventory()
                        inv = next((inv for inv in all_inventory if inv["id"] == inventory_id), None)
                        item_course = inv.get("course") if inv else None
                
                # Normalize course values for comparison (handle None, empty strings, "N/A")
                if item_course:
                    item_course = str(item_course).strip()
                    if item_course == "N/A" or not item_course:
                        item_course = None
                else:
                    item_course = None
                
                filter_course = str(self.catalog_filter_course).strip()
                
                # Skip items that don't match the course filter
                # If item has no course and filter is for a specific course, skip it
                if not item_course or item_course != filter_course:
                    continue
            
            # Search filter - only apply if there's a search query
            if search_query:
                # Search in serial number
                serial_number = str(item.get("serial_number", "")).lower()
                serial_match = search_query in serial_number
                
                # Search in component name
                inventory_name = "Unknown"
                if "inventory" in item and item["inventory"]:
                    inventory_name = item["inventory"].get("name", "Unknown")
                elif "inventory_id" in item:
                    inv_list = self.db.get_all_inventory()
                    for inv in inv_list:
                        if inv["id"] == item["inventory_id"]:
                            inventory_name = inv["name"]
                            break
                
                name_match = search_query in inventory_name.lower()
                
                if not (serial_match or name_match):
                    continue
            
            # Item passed all filters, add to filtered list
            filtered_items.append(item)
        
        print(f"Catalog: Filtered {len(filtered_items)} items from {len(all_items)} total items")
        
        # Clear table body completely
        for widget in self.catalog_table_body.winfo_children():
            widget.destroy()
        
        # Force update to ensure widgets are destroyed
        self.update_idletasks()
        
        # Display filtered items or empty state
        if not filtered_items:
            print(f"Catalog: No items match filters - showing empty state")
            empty_label = ctk.CTkLabel(
                self.catalog_table_body,
                text="No items found matching your search criteria.",
                font=ctk.CTkFont(size=14),
                text_color=self.colors["text_secondary"]
            )
            empty_label.pack(pady=50)
            self.catalog_table_body.update_idletasks()
            return
        
        # Display items as table rows - create all rows
        rows_created = 0
        print(f"Catalog: Starting to create rows for {len(filtered_items)} filtered items")
        
        # Debug: Check table body before creating rows
        child_count_before = len(self.catalog_table_body.winfo_children())
        print(f"Catalog: Table body has {child_count_before} widgets before creating rows")
        
        for idx, item in enumerate(filtered_items):
            try:
                print(f"Catalog: Creating row {idx+1}/{len(filtered_items)} for item ID={item.get('id')}, Serial={item.get('serial_number')}")
                self._create_catalog_table_row(item, student_lookup)
                rows_created += 1
            except Exception as e:
                print(f"Error creating catalog row for item {item.get('id', 'unknown')}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"Catalog: Created {rows_created} rows from {len(filtered_items)} filtered items")
        
        # Force update to ensure all rows are displayed
        self.catalog_table_body.update_idletasks()
        self.update_idletasks()
        
        # Debug: Check if widgets are actually in the table body
        child_count_after = len(self.catalog_table_body.winfo_children())
        print(f"Catalog: Table body now has {child_count_after} child widgets after creating rows (was {child_count_before})")
        
        # If no children but we created rows, something is wrong with packing
        if child_count_after == 0 and rows_created > 0:
            print(f"Catalog: WARNING - Created {rows_created} rows but table body has no children!")
    
    def _load_catalog_table(self):
        """
        Load initial catalog table data and refresh overdue tracking.
        
        This method ensures the catalog displays all items on initial load
        by setting the filter to "All" and clearing any search query.
        """
        # Ensure filters are set to "All" for initial load
        if not hasattr(self, 'catalog_filter_status'):
            self.catalog_filter_status = "All"
        if not hasattr(self, 'catalog_filter_course'):
            self.catalog_filter_course = "All"
        
        # Clear search entry if it exists
        if hasattr(self, 'catalog_search_entry'):
            try:
                self.catalog_search_entry.delete(0, "end")
            except:
                pass
        
        # Refresh overdue items list for highlighting
        overdue_items = self.db.get_overdue_items(days_threshold=7)
        self.overdue_item_ids = {item["id"] for item in overdue_items}
        
        # Load and filter table (will show all items since filter is "All" and search is empty)
        self._filter_catalog_table()
    
    def _create_catalog_table_row(self, item: Dict, student_lookup: Dict):
        """
        Create a table row for an item in the catalog.
        
        Args:
            item: Item dictionary from database
            student_lookup: Dictionary mapping student IDs to names
        """
        # Check if item is overdue for highlighting
        is_overdue = item.get("id") in self.overdue_item_ids if item.get("id") else False
        
        # Row frame: Each row is a separate frame with bottom border
        # Overdue items get red border for visual alert
        # Note: Use a subtle background color instead of transparent to ensure visibility
        if is_overdue:
            row_frame = ctk.CTkFrame(
                self.catalog_table_body,
                fg_color="#1a0a0a",  # Subtle red background for overdue
                border_width=2,
                border_color="#ef4444",
                height=56
            )
        else:
            # Use the same background as the card for consistency
            row_frame = ctk.CTkFrame(
                self.catalog_table_body,
                fg_color=self.colors["bg_secondary"],  # Match card background
                border_width=0,
                border_color=None,
                height=56
            )
        row_frame.pack(fill="x", pady=(0, 1))
        row_frame.pack_propagate(False)  # Keep fixed height to ensure visibility
        print(f"Catalog: Packed row_frame for item {item.get('serial_number', 'N/A')} into table body")
        
        # Configure grid columns for proper alignment
        row_frame.grid_columnconfigure(0, weight=0, minsize=250)  # Component
        row_frame.grid_columnconfigure(1, weight=0, minsize=150)  # Serial #
        row_frame.grid_columnconfigure(2, weight=0, minsize=120)  # Course
        row_frame.grid_columnconfigure(3, weight=0, minsize=120)  # Status
        row_frame.grid_columnconfigure(4, weight=1, minsize=200)  # Issued To
        row_frame.grid_rowconfigure(0, weight=1)  # Allow content row to expand
        row_frame.grid_rowconfigure(1, weight=0)  # Border row
        
        # Get component name and course
        inventory_name = "Unknown"
        inventory_course = "N/A"
        if "inventory" in item and item["inventory"]:
            inventory_name = item["inventory"].get("name", "Unknown")
            course_val = item["inventory"].get("course")
            inventory_course = str(course_val) if course_val else "N/A"
        elif "inventory_id" in item:
            inv_list = self.db.get_all_inventory()
            for inv in inv_list:
                if inv["id"] == item["inventory_id"]:
                    inventory_name = inv["name"]
                    course_val = inv.get("course")
                    inventory_course = str(course_val) if course_val else "N/A"
                    break
        
        # Column 1: Component Name
        # Overdue items shown in red for immediate attention
        component_label = ctk.CTkLabel(
            row_frame,
            text=inventory_name,
            font=ctk.CTkFont(size=14, weight="bold" if is_overdue else "normal"),
            text_color="#ef4444" if is_overdue else self.colors["text_primary"],
            anchor="w"
        )
        component_label.grid(row=0, column=0, padx=(20, 20), sticky="w", pady=16)
        
        # Column 2: Serial Number
        serial_label = ctk.CTkLabel(
            row_frame,
            text=item.get("serial_number", "N/A"),
            font=ctk.CTkFont(size=14, weight="bold" if is_overdue else "normal"),
            text_color="#ef4444" if is_overdue else self.colors["text_primary"],
            anchor="w"
        )
        serial_label.grid(row=0, column=1, padx=(0, 20), sticky="w", pady=16)
        
        # Column 3: Course
        course_label = ctk.CTkLabel(
            row_frame,
            text=inventory_course,
            font=ctk.CTkFont(size=14),
            text_color=self.colors["text_secondary"],
            anchor="w"
        )
        course_label.grid(row=0, column=2, padx=(0, 20), sticky="w", pady=16)
        
        # Column 4: Status Badge
        status = item.get("status", "Unknown")
        status_colors = {
            "Available": self.colors["status_available"],
            "Issued": self.colors["status_issued"],
            "Damaged": self.colors["status_damaged"]
        }
        status_bg = status_colors.get(status, "#a1a1aa")
        
        # Status badge: Small colored pill
        status_badge = ctk.CTkFrame(
            row_frame,
            width=100,
            height=24,
            corner_radius=12,
            fg_color=status_bg
        )
        status_badge.grid(row=0, column=3, padx=(0, 20), sticky="w", pady=16)
        status_badge.pack_propagate(False)
        
        status_text = ctk.CTkLabel(
            status_badge,
            text=status,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#ffffff"  # White text on colored background
        )
        status_text.pack(expand=True)
        
        # Column 5: Issued To
        # Use get_current_holder to find who has this item
        # This performs a JOIN operation: transaction_items -> transactions -> students
        issued_to_text = "N/A"
        if status == "Issued":
            holder_name = self.db.get_current_holder(item["id"])
            issued_to_text = holder_name if holder_name else "Unknown"
        
        issued_to_label = ctk.CTkLabel(
            row_frame,
            text=issued_to_text,
            font=ctk.CTkFont(size=14),
            text_color=self.colors["text_secondary"],
            anchor="w"
        )
        issued_to_label.grid(row=0, column=4, padx=(0, 20), sticky="w", pady=16)
        
        # Bottom border for row separation
        border = ctk.CTkFrame(
            row_frame,
            height=1,
            fg_color=self.colors["border"]
        )
        border.grid(row=1, column=0, columnspan=5, sticky="ew", pady=(0, 0))
        row_frame.grid_rowconfigure(0, weight=1)
    
    def _show_students_view(self):
        """
        Display the Students management view.
        
        This view allows:
        - Viewing all students in a table format
        - Adding new students with phone and email
        - Removing students
        """
        # Create scrollable container
        scroll_frame = ctk.CTkScrollableFrame(
            self.content_frame,
            fg_color=self.colors["bg_primary"]
        )
        scroll_frame.pack(fill="both", expand=True)
        
        # Title row with Add Student button
        title_container = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        title_container.pack(fill="x", pady=(0, 40))
        
        title = ctk.CTkLabel(
            title_container,
            text="Student Management",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color=self.colors["text_primary"]
        )
        title.pack(side="left", anchor="w")
        
        # Add Student button
        add_student_btn = ctk.CTkButton(
            title_container,
            text="Add Student",
            command=self._show_add_student_form,
            height=44,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.colors["status_available"],
            text_color="#ffffff",
            hover_color="#16a34a",
            corner_radius=8,
            width=160
        )
        add_student_btn.pack(side="right")
        
        # Load and display students
        self._load_students_display(scroll_frame)
    
    def _load_students_display(self, parent):
        """Load and display students in a table format."""
        students_list = self.db.get_all_students()
        
        if not students_list:
            label = ctk.CTkLabel(
                parent,
                text="No students found. Click 'Add Student' to create one.",
                font=ctk.CTkFont(size=16),
                text_color=self.colors["text_secondary"]
            )
            label.pack(pady=50)
            return
        
        # Table header card
        header_card = ctk.CTkFrame(
            parent, 
            corner_radius=12,
            fg_color=self.colors["bg_secondary"],
            border_width=1,
            border_color=self.colors["border"]
        )
        header_card.pack(fill="x", pady=(0, 12), padx=0)
        
        headers = ["Student ID", "Name", "Phone", "Email", "Actions"]
        column_widths = [150, 250, 180, 300, 120]
        
        for i, (header, width) in enumerate(zip(headers, column_widths)):
            label = ctk.CTkLabel(
                header_card,
                text=header.upper(),
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=self.colors["text_secondary"],
                width=width,
                anchor="w"
            )
            label.grid(row=0, column=i, padx=30, pady=20, sticky="w")
        
        # Student data rows
        for student in students_list:
            row_card = ctk.CTkFrame(
                parent, 
                corner_radius=12,
                fg_color=self.colors["bg_secondary"],
                border_width=1,
                border_color=self.colors["border"]
            )
            row_card.pack(fill="x", pady=8, padx=0)
            
            # Student ID
            id_label = ctk.CTkLabel(
                row_card, 
                text=student.get("student_id", "N/A"), 
                font=ctk.CTkFont(size=15),
                text_color=self.colors["text_primary"],
                width=150,
                anchor="w"
            )
            id_label.grid(row=0, column=0, padx=30, pady=20, sticky="w")
            
            # Name
            name_label = ctk.CTkLabel(
                row_card, 
                text=student.get("name", "N/A"), 
                font=ctk.CTkFont(size=15),
                text_color=self.colors["text_primary"],
                width=250,
                anchor="w"
            )
            name_label.grid(row=0, column=1, padx=30, pady=20, sticky="w")
            
            # Phone
            phone_label = ctk.CTkLabel(
                row_card, 
                text=student.get("phone", "N/A"), 
                font=ctk.CTkFont(size=15),
                text_color=self.colors["text_secondary"],
                width=180,
                anchor="w"
            )
            phone_label.grid(row=0, column=2, padx=30, pady=20, sticky="w")
            
            # Email
            email_label = ctk.CTkLabel(
                row_card, 
                text=student.get("email", "N/A"), 
                font=ctk.CTkFont(size=15),
                text_color=self.colors["text_secondary"],
                width=300,
                anchor="w"
            )
            email_label.grid(row=0, column=3, padx=30, pady=20, sticky="w")
            
            # Actions: Remove button
            actions_frame = ctk.CTkFrame(row_card, fg_color="transparent")
            actions_frame.grid(row=0, column=4, padx=30, pady=20, sticky="e")
            
            remove_btn = ctk.CTkButton(
                actions_frame,
                text="Remove",
                width=100,
                height=36,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=self.colors["status_damaged"],
                hover_color="#dc2626",
                corner_radius=8,
                command=lambda s=student: self._remove_student(s)
            )
            remove_btn.pack()
    
    def _show_add_student_form(self):
        """Show a form to add a new student."""
        popup = ctk.CTkToplevel(self)
        popup.title("Add New Student")
        popup.geometry("600x600")  # Increased height to accommodate all fields
        popup.configure(bg=self.colors["bg_primary"])
        popup.transient(self)
        popup.grab_set()
        
        main_frame = ctk.CTkFrame(
            popup,
            fg_color=self.colors["bg_secondary"],
            corner_radius=12,
            border_width=1,
            border_color=self.colors["border"]
        )
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        title = ctk.CTkLabel(
            main_frame,
            text="Add New Student",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.colors["text_primary"]
        )
        title.pack(pady=(30, 20))
        
        # Make form frame scrollable to ensure all fields are accessible
        form_scroll = ctk.CTkScrollableFrame(main_frame, fg_color="transparent", height=400)
        form_scroll.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        
        # Student ID field
        id_label = ctk.CTkLabel(
            form_scroll,
            text="Student ID *",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["text_primary"],
            anchor="w"
        )
        id_label.pack(anchor="w", pady=(15, 5))
        
        id_entry = ctk.CTkEntry(
            form_scroll,
            placeholder_text="Enter Student ID (e.g., STU001)...",
            height=40,
            font=ctk.CTkFont(size=13),
            fg_color=self.colors["bg_primary"],
            border_color=self.colors["border"],
            text_color=self.colors["text_primary"]
        )
        id_entry.pack(fill="x", pady=(0, 10))
        
        # Name field
        name_label = ctk.CTkLabel(
            form_scroll,
            text="Name *",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["text_primary"],
            anchor="w"
        )
        name_label.pack(anchor="w", pady=(15, 5))
        
        name_entry = ctk.CTkEntry(
            form_scroll,
            placeholder_text="Enter full name...",
            height=40,
            font=ctk.CTkFont(size=13),
            fg_color=self.colors["bg_primary"],
            border_color=self.colors["border"],
            text_color=self.colors["text_primary"]
        )
        name_entry.pack(fill="x", pady=(0, 10))
        
        # Phone field
        phone_label = ctk.CTkLabel(
            form_scroll,
            text="Phone",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["text_primary"],
            anchor="w"
        )
        phone_label.pack(anchor="w", pady=(15, 5))
        
        phone_entry = ctk.CTkEntry(
            form_scroll,
            placeholder_text="Enter phone number (optional)...",
            height=40,
            font=ctk.CTkFont(size=13),
            fg_color=self.colors["bg_primary"],
            border_color=self.colors["border"],
            text_color=self.colors["text_primary"]
        )
        phone_entry.pack(fill="x", pady=(0, 10))
        
        # Email field
        email_label = ctk.CTkLabel(
            form_scroll,
            text="Email",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["text_primary"],
            anchor="w"
        )
        email_label.pack(anchor="w", pady=(15, 5))
        
        email_entry = ctk.CTkEntry(
            form_scroll,
            placeholder_text="Enter email address (optional)...",
            height=40,
            font=ctk.CTkFont(size=13),
            fg_color=self.colors["bg_primary"],
            border_color=self.colors["border"],
            text_color=self.colors["text_primary"]
        )
        email_entry.pack(fill="x", pady=(0, 20))  # Extra padding at bottom
        
        # Button container (outside scrollable frame, always visible)
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(pady=(0, 30), padx=30, fill="x")
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=popup.destroy,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="transparent",
            hover_color="#27272a",
            text_color=self.colors["text_primary"],
            corner_radius=8,
            width=120
        )
        cancel_btn.pack(side="left", padx=(0, 10))
        
        submit_btn = ctk.CTkButton(
            button_frame,
            text="Add Student",
            command=lambda: self._submit_add_student(
                id_entry.get().strip(),
                name_entry.get().strip(),
                phone_entry.get().strip(),
                email_entry.get().strip(),
                popup
            ),
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.colors["status_available"],
            hover_color="#16a34a",
            text_color="#ffffff",
            corner_radius=8,
            width=200
        )
        submit_btn.pack(side="right")
        
        # Bind Enter key to submit form (works from any field)
        def submit_on_enter(e):
            self._submit_add_student(
                id_entry.get().strip(),
                name_entry.get().strip(),
                phone_entry.get().strip(),
                email_entry.get().strip(),
                popup
            )
        
        id_entry.bind("<Return>", submit_on_enter)
        name_entry.bind("<Return>", submit_on_enter)
        phone_entry.bind("<Return>", submit_on_enter)
        email_entry.bind("<Return>", submit_on_enter)
        
        # Focus on first field for better UX
        id_entry.focus()
    
    def _submit_add_student(self, student_id: str, name: str, phone: str, email: str, popup):
        """Submit the add student form."""
        errors = []
        if not student_id:
            errors.append("Student ID is required")
        if not name:
            errors.append("Name is required")
        
        # Check for duplicate student ID
        existing_students = self.db.get_all_students()
        for student in existing_students:
            if student.get("student_id") == student_id:
                errors.append(f"Student ID '{student_id}' already exists")
                break
        
        if errors:
            error_msg = "Please fix the following errors:\n\n" + "\n".join(f"• {e}" for e in errors)
            self._show_error(error_msg, "Validation Error")
            return
        
        student_data = {
            "student_id": student_id,
            "name": name,
            "phone": phone if phone else None,
            "email": email if email else None
        }
        
        student_id_result = self.db.create_student(student_data)
        
        if student_id_result:
            # Success - data has been saved to Supabase (if connected) or mock data
            success_popup = ctk.CTkToplevel(self)
            success_popup.title("Success")
            success_popup.geometry("500x200")
            success_popup.configure(bg=self.colors["bg_primary"])
            success_popup.transient(self)
            success_popup.grab_set()
            
            main_frame = ctk.CTkFrame(
                success_popup,
                fg_color=self.colors["bg_secondary"],
                corner_radius=12,
                border_width=1,
                border_color=self.colors["border"]
            )
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            label = ctk.CTkLabel(
                main_frame,
                text=f"Student '{name}' added successfully!",
                font=ctk.CTkFont(size=14),
                text_color=self.colors["status_available"],
                wraplength=430
            )
            label.pack(pady=40, padx=30)
            
            btn = ctk.CTkButton(
                main_frame,
                text="OK",
                command=lambda: self._close_add_student_success(success_popup, popup),
                fg_color=self.colors["status_available"],
                hover_color="#16a34a",
                height=40,
                corner_radius=8,
                font=ctk.CTkFont(size=14, weight="bold")
            )
            btn.pack(pady=(0, 30))
        else:
            self._show_error("Failed to create student. Please try again.", "Error")
    
    def _close_add_student_success(self, success_popup, form_popup):
        """Close success popup and form, then refresh students view."""
        success_popup.destroy()
        form_popup.destroy()
        self._switch_view("students")
    
    def _remove_student(self, student: Dict):
        """Remove a student after confirmation."""
        popup = ctk.CTkToplevel(self)
        popup.title("Confirm Removal")
        popup.geometry("500x280")
        popup.configure(bg=self.colors["bg_primary"])
        popup.transient(self)
        popup.grab_set()
        
        main_frame = ctk.CTkFrame(
            popup,
            fg_color=self.colors["bg_secondary"],
            corner_radius=12,
            border_width=1,
            border_color=self.colors["border"]
        )
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        label = ctk.CTkLabel(
            main_frame,
            text=f"Remove student '{student.get('name', 'N/A')}' ({student.get('student_id', 'N/A')})?\n\nThis action cannot be undone.",
            font=ctk.CTkFont(size=14),
            text_color=self.colors["status_damaged"],
            wraplength=430
        )
        label.pack(pady=40, padx=30)
        
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(pady=(0, 30))
        
        confirm_btn = ctk.CTkButton(
            btn_frame,
            text="Confirm",
            command=lambda: self._confirm_remove_student(student, popup),
            fg_color=self.colors["status_damaged"],
            hover_color="#dc2626",
            height=40,
            corner_radius=8,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        confirm_btn.pack(side="left", padx=10)
        
        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=popup.destroy,
            fg_color="transparent",
            hover_color="#27272a",
            height=40,
            corner_radius=8,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors["text_primary"]
        )
        cancel_btn.pack(side="left", padx=10)
    
    def _confirm_remove_student(self, student: Dict, popup):
        """Confirm and execute student removal."""
        popup.destroy()
        success = self.db.delete_student(student["id"])
        
        if success:
            self._switch_view("students")
            self._show_success(f"Student '{student.get('name', 'N/A')}' removed successfully.")
        else:
            self._show_error("Failed to remove student. Please try again.", "Error")


def main():
    """Main entry point."""
    app = LabApp()
    app.mainloop()


if __name__ == "__main__":
    main()
