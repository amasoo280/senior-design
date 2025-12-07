"""Database schema context provider for NL→SQL generation."""

from typing import Dict, List, Optional


class SchemaContext:
    """Provides database schema context for SQL generation."""

    def __init__(self, schema_info: Optional[Dict] = None):
        """
        Initialize schema context.

        Args:
            schema_info: Dictionary containing schema information.
                        If None, uses default sample schema.
        """
        if schema_info is None:
            schema_info = self._get_default_schema()

        self.schema_info = schema_info

    def get_schema_context(self) -> str:
        """
        Get formatted schema context string for prompts.

        Returns:
            Formatted schema description string
        """
        context_parts = []

        if "description" in self.schema_info:
            context_parts.append(f"Database: {self.schema_info['description']}")

        if "tables" in self.schema_info:
            context_parts.append("\nTables and columns:")
            for table in self.schema_info["tables"]:
                table_name = table.get("name", "unknown")
                table_desc = table.get("description", "")
                
                table_line = f"\n{table_name}"
                if table_desc:
                    table_line += f" ({table_desc})"
                table_line += ":"
                
                context_parts.append(table_line)

                columns = table.get("columns", [])
                for col in columns:
                    col_name = col.get("name", "unknown")
                    col_type = col.get("type", "")
                    col_desc = col.get("description", "")
                    
                    col_line = f"  - {col_name}"
                    if col_type:
                        col_line += f" ({col_type})"
                    if col_desc:
                        col_line += f": {col_desc}"
                    
                    context_parts.append(col_line)

                # Add relationships if present
                relationships = table.get("relationships", [])
                if relationships:
                    for rel in relationships:
                        rel_type = rel.get("type", "")
                        target_table = rel.get("table", "")
                        foreign_key = rel.get("foreign_key", "")
                        target_key = rel.get("target_key", "")
                        
                        if rel_type and target_table:
                            rel_line = f"  -> {rel_type} {target_table}"
                            if foreign_key and target_key:
                                rel_line += f" ({foreign_key} -> {target_key})"
                            context_parts.append(rel_line)

        # Add important notes
        if "notes" in self.schema_info:
            context_parts.append("\nImportant notes:")
            for note in self.schema_info["notes"]:
                context_parts.append(f"- {note}")

        return "\n".join(context_parts)

    def _get_default_schema(self) -> Dict:
        """
        Get default sample schema for equipment/asset management.
        
        TODO: Update this with the actual Sargon Partners database schema.
        Replace the tables, columns, and relationships below with the real schema
        from your database. You can use update_schema() method or modify this method.

        Returns:
            Dictionary with schema information
        """
        return {
            "description": "Equipment and asset management database",
            "tables": [
                {
                    "name": "equipment",
                    "description": "Main equipment table with asset information",
                    "columns": [
                        {
                            "name": "id",
                            "type": "VARCHAR(50)",
                            "description": "Unique equipment identifier (e.g., 'EQ-001')",
                        },
                        {
                            "name": "tenant_id",
                            "type": "VARCHAR(50)",
                            "description": "Tenant identifier for multi-tenancy isolation (REQUIRED in all queries)",
                        },
                        {
                            "name": "name",
                            "type": "VARCHAR(255)",
                            "description": "Equipment name (e.g., 'Excavator A')",
                        },
                        {
                            "name": "location",
                            "type": "VARCHAR(255)",
                            "description": "Current location (e.g., 'Site A', 'Site B')",
                        },
                        {
                            "name": "status",
                            "type": "VARCHAR(50)",
                            "description": "Equipment status ('Active', 'Maintenance', 'Available', 'Inactive')",
                        },
                        {
                            "name": "days_active",
                            "type": "INTEGER",
                            "description": "Number of days the equipment has been active",
                        },
                        {
                            "name": "deployed_at",
                            "type": "TIMESTAMP",
                            "description": "Timestamp when equipment was deployed",
                        },
                        {
                            "name": "created_at",
                            "type": "TIMESTAMP",
                            "description": "Record creation timestamp",
                        },
                    ],
                    "relationships": [],
                },
                {
                    "name": "jobs",
                    "description": "Job/project information",
                    "columns": [
                        {
                            "name": "id",
                            "type": "VARCHAR(50)",
                            "description": "Unique job identifier",
                        },
                        {
                            "name": "tenant_id",
                            "type": "VARCHAR(50)",
                            "description": "Tenant identifier (REQUIRED in all queries)",
                        },
                        {
                            "name": "name",
                            "type": "VARCHAR(255)",
                            "description": "Job name",
                        },
                        {
                            "name": "status",
                            "type": "VARCHAR(50)",
                            "description": "Job status",
                        },
                    ],
                },
                {
                    "name": "equipment_assignments",
                    "description": "Assigns equipment to jobs",
                    "columns": [
                        {
                            "name": "equipment_id",
                            "type": "VARCHAR(50)",
                            "description": "Reference to equipment.id",
                        },
                        {
                            "name": "job_id",
                            "type": "VARCHAR(50)",
                            "description": "Reference to jobs.id",
                        },
                        {
                            "name": "tenant_id",
                            "type": "VARCHAR(50)",
                            "description": "Tenant identifier (REQUIRED in all queries)",
                        },
                        {
                            "name": "assigned_at",
                            "type": "TIMESTAMP",
                            "description": "Assignment timestamp",
                        },
                    ],
                    "relationships": [
                        {
                            "type": "JOIN",
                            "table": "equipment",
                            "foreign_key": "equipment_id",
                            "target_key": "id",
                        },
                        {
                            "type": "JOIN",
                            "table": "jobs",
                            "foreign_key": "job_id",
                            "target_key": "id",
                        },
                    ],
                },
            ],
            "notes": [
                "ALL queries MUST include WHERE tenant_id = '<tenant_id>' for multi-tenant isolation",
                "Use proper SQL syntax and optimize for performance",
                "Join tables when querying across relationships",
                "Filter by status values: 'Active', 'Maintenance', 'Available', 'Inactive'",
            ],
        }

    def update_schema(self, schema_info: Dict):
        """
        Update schema information.

        Args:
            schema_info: New schema information dictionary
        """
        self.schema_info = schema_info



