# LabTrack Database Setup Guide

This guide will help you set up your Supabase database for the LabTrack application.

## 📋 Prerequisites

1. A Supabase account (sign up at [supabase.com](https://supabase.com))
2. A new Supabase project created

## 🚀 Quick Setup Steps

### Step 1: Open SQL Editor
1. Log into your Supabase dashboard
2. Select your project
3. Click on **"SQL Editor"** in the left sidebar
4. Click **"New Query"**

### Step 2: Run the Setup Script
1. Open the `supabase_setup.sql` file in this repository
2. Copy the entire contents
3. Paste into the Supabase SQL Editor
4. Click **"Run"** (or press `Ctrl+Enter`)

### Step 3: Verify Setup
After running the script, verify everything worked by running these queries in the SQL Editor:

```sql
-- Check tables were created
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
    AND table_name IN ('inventory', 'items', 'students', 'staff', 'transactions', 'transaction_items')
ORDER BY table_name;
```

You should see 6 tables listed.

### Step 4: Get Your API Credentials
1. In Supabase dashboard, go to **Settings** → **API**
2. Copy the following:
   - **Project URL** (under "Project URL")
   - **anon/public key** (under "Project API keys" → "anon public")

### Step 5: Configure Your Application
1. Create a `.env` file in your project root (if it doesn't exist)
2. Add your credentials:

```env
SUPABASE_URL=your_project_url_here
SUPABASE_KEY=your_anon_public_key_here
```

Example:
```env
SUPABASE_URL=https://abcdefghijklmnop.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFiY2RlZmdoaWprbG1ub3AiLCJyb2xlIjoiYW5vbiIsImlhdCI6MTY0NTI5ODQwMCwiZXhwIjoxOTYwODc0NDAwfQ.example
```

## 📊 Database Schema Overview

### Tables Created

1. **inventory** - Component types (e.g., "Arduino", "Raspberry Pi")
   - `id` - Primary key
   - `name` - Component name (unique)
   - `total_qty` - Total quantity available
   - `course` - Course code (optional)
   - `description` - Component description (optional)
   - `custom_fields` - JSON field for additional data

2. **items** - Individual physical items
   - `id` - Primary key
   - `serial_number` - Unique serial number (e.g., "ARD001")
   - `status` - Status: "Available", "Issued", or "Damaged"
   - `inventory_id` - Foreign key to inventory table

3. **students** - Student records
   - `id` - Primary key
   - `name` - Student name
   - `student_id` - Unique student ID (e.g., "STU001")
   - `phone` - Phone number (optional)
   - `email` - Email address (optional)

4. **staff** - Staff/Issuer records
   - `id` - Primary key
   - `name` - Staff name
   - `staff_id` - Unique staff ID (e.g., "STAFF001")

5. **transactions** - Transaction records
   - `id` - Primary key
   - `student_id` - Foreign key to students
   - `issuer_id` - Foreign key to staff (optional)
   - `status` - "Active" or "Completed"
   - `issue_date` - Date when items were issued
   - `expected_return_date` - Expected return date (optional, for backdating feature)
   - `created_at` - Timestamp when transaction was created

6. **transaction_items** - Junction table linking transactions to items
   - `id` - Primary key
   - `transaction_id` - Foreign key to transactions
   - `item_id` - Foreign key to items

## 🔒 Security (Row Level Security)

The setup script enables Row Level Security (RLS) on all tables with a policy that allows all operations for authenticated users. 

**For production**, you should customize these policies based on your authentication setup. For development/testing, the current policies allow full access.

## 🧪 Testing Your Setup

### Option 1: Use Sample Data
The `supabase_setup.sql` file includes commented-out sample data. To use it:
1. Uncomment the "SAMPLE DATA" section in the SQL file
2. Run it again

### Option 2: Add Data via Application
1. Run your LabTrack application
2. Go to **Inventory** view → Click **"Add Component"**
3. Add a test component (e.g., "Arduino", quantity: 5)
4. Go to **Students** view → Add a test student
5. Go to **Issue Items** view → Try issuing an item

## 🔍 Troubleshooting

### Issue: "relation does not exist"
- **Solution**: Make sure you ran the entire `supabase_setup.sql` script
- Check that you're connected to the correct Supabase project

### Issue: "permission denied"
- **Solution**: Check your RLS policies in Supabase dashboard
- Go to **Authentication** → **Policies** and verify policies are set correctly

### Issue: "foreign key constraint violation"
- **Solution**: Make sure you're inserting data in the correct order:
  1. First: inventory, students, staff
  2. Then: items (references inventory)
  3. Finally: transactions and transaction_items

### Issue: Application can't connect
- **Solution**: 
  1. Verify your `.env` file has correct `SUPABASE_URL` and `SUPABASE_KEY`
  2. Check that your Supabase project is active (not paused)
  3. Verify the API key has the correct permissions

## 📝 Additional Notes

- All tables have `created_at` and `updated_at` timestamps that are automatically managed
- The `expected_return_date` column was added in v12 for the backdating feature
- Serial numbers are auto-generated using the format: `[PREFIX][NUMBER]` (e.g., "ARD001", "RPI002")
- The prefix is derived from the first 3 letters of the component name

## 🆘 Need Help?

If you encounter any issues:
1. Check the Supabase logs in the dashboard
2. Verify your SQL script ran without errors
3. Check the application console for error messages
4. Review the table structure in Supabase Table Editor

---

**Happy Tracking! 🎉**

