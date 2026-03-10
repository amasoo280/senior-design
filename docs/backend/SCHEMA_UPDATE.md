# Updating Schema Context for Sargon Partners Database

The schema context tells the AI model about your database structure so it can generate accurate SQL queries.

## Current Status

The application currently uses a default sample schema for equipment/asset management. **You must update this with your actual Sargon Partners database schema** before the chatbot will work correctly with your data.

## How to Update

### Option 1: Modify `_get_default_schema()` Method

Edit `backend/app/schema/context.py` and replace the `_get_default_schema()` method with your real schema:

```python
def _get_default_schema(self) -> Dict:
    return {
        "description": "Sargon Partners database",
        "tables": [
            {
                "name": "your_table_name",
                "description": "Description of what this table stores",
                "columns": [
                    {
                        "name": "id",
                        "type": "INTEGER",
                        "description": "Primary key"
                    },
                    {
                        "name": "tenant_id",
                        "type": "VARCHAR(50)",
                        "description": "Tenant identifier (REQUIRED in all queries)"
                    },
                    # ... more columns
                ],
                "relationships": [
                    {
                        "type": "JOIN",
                        "table": "other_table",
                        "foreign_key": "other_table_id",
                        "target_key": "id"
                    }
                ]
            },
            # ... more tables
        ],
        "notes": [
            "ALL queries MUST include WHERE tenant_id = '<tenant_id>'",
            "Important business rules or query patterns"
        ]
    }
```

### Option 2: Use `update_schema()` Method

If you have schema information in a file or from an API:

```python
from app.schema.context import SchemaContext
import json

# Load from JSON file
with open('schema.json', 'r') as f:
    schema_data = json.load(f)

schema_context = SchemaContext()
schema_context.update_schema(schema_data)
```

## Schema Information Needed

For each table, provide:

1. **Table name** - Exact name as it appears in the database
2. **Description** - What the table stores
3. **Columns** - All columns with:
   - Column name
   - Data type (VARCHAR, INTEGER, TIMESTAMP, etc.)
   - Description/purpose
4. **Relationships** - Foreign key relationships to other tables
5. **Important notes** - Business rules, common query patterns, etc.

## Getting Schema Information

### From MySQL

```sql
-- Get all tables
SHOW TABLES;

-- Get columns for a table
DESCRIBE table_name;
-- or
SHOW COLUMNS FROM table_name;

-- Get foreign keys
SELECT 
    TABLE_NAME,
    COLUMN_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'your_database_name'
AND REFERENCED_TABLE_NAME IS NOT NULL;
```

### From Database Tools

Most database management tools (MySQL Workbench, DBeaver, etc.) can export schema information.

## Critical Requirements

1. **Tenant Isolation**: Every table that needs tenant isolation must have a `tenant_id` column documented
2. **Primary Keys**: Document primary key columns
3. **Foreign Keys**: Document relationships for JOIN queries
4. **Data Types**: Accurate types help the AI generate correct SQL

## Testing After Update

After updating the schema:

1. Restart the backend server
2. Test with a simple query: "Show me all records from [your_table]"
3. Verify the generated SQL uses correct table/column names
4. Check that tenant_id filtering is included

## Example: Real Schema

Here's an example of how a real schema might look:

```python
{
    "description": "Sargon Partners equipment and job management database",
    "tables": [
        {
            "name": "equipment",
            "description": "Equipment and asset records",
            "columns": [
                {"name": "id", "type": "INT", "description": "Primary key"},
                {"name": "tenant_id", "type": "VARCHAR(50)", "description": "Tenant identifier"},
                {"name": "equipment_name", "type": "VARCHAR(255)", "description": "Equipment name"},
                {"name": "site_location", "type": "VARCHAR(255)", "description": "Current site location"},
                {"name": "status", "type": "ENUM('Active', 'Inactive', 'Maintenance')", "description": "Equipment status"},
                {"name": "created_at", "type": "TIMESTAMP", "description": "Creation timestamp"}
            ],
            "relationships": [
                {
                    "type": "JOIN",
                    "table": "equipment_assignments",
                    "foreign_key": "equipment_id",
                    "target_key": "id"
                }
            ]
        }
    ],
    "notes": [
        "ALL queries MUST include WHERE tenant_id = '<tenant_id>'",
        "Status values are: 'Active', 'Inactive', 'Maintenance'",
        "Join equipment with equipment_assignments to see job assignments"
    ]
}
```

