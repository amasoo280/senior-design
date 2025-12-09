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
        Get Sargon Partners database schema for equipment and asset tracking.
        
        This schema represents the actual Sargon Partners database structure
        with equipment locations, job instances, tags, beacons, and employee data.

        Returns:
            Dictionary with schema information
        """
        return {
            "description": "Sargon Partners equipment and asset tracking database",
            "tenant_id_column": "accountId",
            "tables": [
                {
                    "name": "EquipmentLocation",
                    "description": "Current location and state of an equipment asset",
                    "columns": [
                        {"name": "dcuUUID", "type": "VARCHAR(36)", "description": "Equipment or asset UUID"},
                        {"name": "accountId", "type": "VARCHAR(50)", "description": "Tenant account identifier (REQUIRED in all queries)"},
                        {"name": "employeeUUID", "type": "VARCHAR(36)", "description": "Employee interacting with equipment"},
                        {"name": "locationName", "type": "VARCHAR(255)", "description": "Location name"},
                        {"name": "locationType", "type": "VARCHAR(50)", "description": "Type of location"},
                        {"name": "startTimestamp", "type": "TIMESTAMP", "description": "Start time of this location event"},
                        {"name": "endTimestamp", "type": "TIMESTAMP", "description": "End time of this location event"},
                        {"name": "notes", "type": "TEXT", "description": "Optional notes for this location record"},
                    ],
                    "relationships": [],
                },
                {
                    "name": "EquipmentLocationHistory",
                    "description": "Historical events and movements for equipment assets",
                    "columns": [
                        {"name": "dcuUUID", "type": "VARCHAR(36)", "description": "Asset UUID"},
                        {"name": "accountId", "type": "VARCHAR(50)", "description": "Tenant account (REQUIRED in all queries)"},
                        {"name": "employeeUUID", "type": "VARCHAR(36)", "description": "Employee linked to the event"},
                        {"name": "locationUUID", "type": "VARCHAR(36)", "description": "Location identifier"},
                        {"name": "transferUUID", "type": "VARCHAR(36)", "description": "Transfer identifier"},
                        {"name": "scanType", "type": "VARCHAR(50)", "description": "Scan type for the movement"},
                        {"name": "prevState", "type": "VARCHAR(50)", "description": "Previous state before movement"},
                        {"name": "subLocation", "type": "VARCHAR(255)", "description": "Sub-location info when available"},
                    ],
                    "relationships": [],
                },
                {
                    "name": "JOBINSTANCE",
                    "description": "A job assigned to an employee with timestamps and status",
                    "columns": [
                        {"name": "jobUUID", "type": "VARCHAR(36)", "description": "Unique identifier for the job"},
                        {"name": "jobName", "type": "VARCHAR(255)", "description": "Name of the job"},
                        {"name": "jobStartTimestamp", "type": "TIMESTAMP", "description": "Time job started"},
                        {"name": "jobCompleteTimestamp", "type": "TIMESTAMP", "description": "Time job completed"},
                        {"name": "completionType", "type": "VARCHAR(50)", "description": "Completion type (success/failure/etc.)"},
                        {"name": "employeeUUID", "type": "VARCHAR(36)", "description": "Employee assigned to job"},
                        {"name": "accountId", "type": "VARCHAR(50)", "description": "Tenant account (REQUIRED in all queries)"},
                    ],
                    "relationships": [
                        {"type": "JOIN", "table": "EMPLOYEE", "foreign_key": "employeeUUID", "target_key": "employeeUUID"},
                    ],
                },
                {
                    "name": "TAG",
                    "description": "Master record for a tag attached to an asset",
                    "columns": [
                        {"name": "tagUUID", "type": "VARCHAR(36)", "description": "Identifier for the tag"},
                        {"name": "accountId", "type": "VARCHAR(50)", "description": "Tenant account (REQUIRED in all queries)"},
                        {"name": "description", "type": "VARCHAR(255)", "description": "Description of tag"},
                        {"name": "serialNumber", "type": "VARCHAR(100)", "description": "Serial number of the tag"},
                        {"name": "assetUUID", "type": "VARCHAR(36)", "description": "Asset this tag is attached to"},
                        {"name": "latestLocationName", "type": "VARCHAR(255)", "description": "Most recent recorded location"},
                        {"name": "latestLocationTimestamp", "type": "TIMESTAMP", "description": "When the tag was last located"},
                        {"name": "latestLatitude", "type": "DECIMAL(10,8)", "description": "Last reported latitude"},
                        {"name": "latestLongitude", "type": "DECIMAL(11,8)", "description": "Last reported longitude"},
                    ],
                    "relationships": [],
                },
                {
                    "name": "TAGJOBINSTANCE",
                    "description": "Link table between tags and job instances",
                    "columns": [
                        {"name": "tagJobInstUUID", "type": "VARCHAR(36)", "description": "Primary key for link"},
                        {"name": "tagUUID", "type": "VARCHAR(36)", "description": "Tag identifier"},
                        {"name": "jobUUID", "type": "VARCHAR(36)", "description": "Job identifier"},
                        {"name": "detected", "type": "BOOLEAN", "description": "Whether tag was detected for this job"},
                        {"name": "syncTimestamp", "type": "TIMESTAMP", "description": "Time this record was synced"},
                    ],
                    "relationships": [
                        {"type": "JOIN", "table": "TAG", "foreign_key": "tagUUID", "target_key": "tagUUID"},
                        {"type": "JOIN", "table": "JOBINSTANCE", "foreign_key": "jobUUID", "target_key": "jobUUID"},
                    ],
                },
                {
                    "name": "DATAEVENT",
                    "description": "Event logs for tags or equipment",
                    "columns": [
                        {"name": "dcuUUID", "type": "VARCHAR(36)", "description": "Equipment or tag UUID"},
                        {"name": "accountId", "type": "VARCHAR(50)", "description": "Tenant account (REQUIRED in all queries)"},
                        {"name": "eventType", "type": "VARCHAR(50)", "description": "Type of event"},
                        {"name": "prevValue", "type": "VARCHAR(255)", "description": "Previous value before event"},
                        {"name": "postValue", "type": "VARCHAR(255)", "description": "Value after event"},
                        {"name": "syncTimestamp", "type": "TIMESTAMP", "description": "Timestamp of event sync"},
                    ],
                    "relationships": [],
                },
                {
                    "name": "BeaconScan",
                    "description": "Raw beacon scan data from readers",
                    "columns": [
                        {"name": "beaconId", "type": "VARCHAR(100)", "description": "Beacon ID"},
                        {"name": "readerId", "type": "VARCHAR(100)", "description": "Reader that scanned this beacon"},
                        {"name": "scanTime", "type": "TIMESTAMP", "description": "Timestamp of scan"},
                        {"name": "latitude", "type": "DECIMAL(10,8)", "description": "Latitude of scan location"},
                        {"name": "longitude", "type": "DECIMAL(11,8)", "description": "Longitude of scan location"},
                        {"name": "batteryLevel", "type": "INTEGER", "description": "Battery level of beacon"},
                    ],
                    "relationships": [],
                },
                {
                    "name": "BeaconCurrentStatus",
                    "description": "Latest status information for each beacon",
                    "columns": [
                        {"name": "beaconId", "type": "VARCHAR(100)", "description": "Beacon ID"},
                        {"name": "readerId", "type": "VARCHAR(100)", "description": "Reader reporting this status"},
                        {"name": "scanTime", "type": "TIMESTAMP", "description": "Time of last scan"},
                        {"name": "latitude", "type": "DECIMAL(10,8)", "description": "Last latitude"},
                        {"name": "longitude", "type": "DECIMAL(11,8)", "description": "Last longitude"},
                        {"name": "batteryLevel", "type": "INTEGER", "description": "Current battery level"},
                        {"name": "speed", "type": "DECIMAL(10,2)", "description": "Speed if applicable"},
                    ],
                    "relationships": [],
                },
                {
                    "name": "TYPE",
                    "description": "Lookup table containing types or categories for assets or tags",
                    "columns": [
                        {"name": "dcuUUID", "type": "VARCHAR(36)", "description": "UUID of the item this type applies to"},
                        {"name": "name", "type": "VARCHAR(255)", "description": "Human-readable type name"},
                        {"name": "imageData", "type": "BLOB", "description": "Associated image or metadata"},
                    ],
                    "relationships": [],
                },
                {
                    "name": "SUBLOCATION",
                    "description": "Sub-areas within a location for more granular tracking",
                    "columns": [
                        {"name": "dcuUUID", "type": "VARCHAR(36)", "description": "UUID of parent location or asset"},
                        {"name": "accountId", "type": "VARCHAR(50)", "description": "Tenant ID (REQUIRED in all queries)"},
                        {"name": "sublocationName", "type": "VARCHAR(255)", "description": "Name of the sublocation"},
                        {"name": "syncTimestamp", "type": "TIMESTAMP", "description": "When last updated"},
                    ],
                    "relationships": [],
                },
                {
                    "name": "EMPLOYEE",
                    "description": "Employee data including login, device, and company info",
                    "columns": [
                        {"name": "employeeUUID", "type": "VARCHAR(36)", "description": "Primary identifier for employee"},
                        {"name": "name", "type": "VARCHAR(255)", "description": "Employee full name"},
                        {"name": "companyId", "type": "VARCHAR(50)", "description": "Company the employee belongs to"},
                        {"name": "deviceId", "type": "VARCHAR(100)", "description": "Linked device ID"},
                        {"name": "accountId", "type": "VARCHAR(50)", "description": "Tenant account for multi-tenancy (REQUIRED in all queries)"},
                    ],
                    "relationships": [],
                },
                {
                    "name": "ITVUSER",
                    "description": "User accounts, permissions, and account metadata",
                    "columns": [
                        {"name": "email", "type": "VARCHAR(255)", "description": "User email address"},
                        {"name": "apikey", "type": "VARCHAR(255)", "description": "API key for the user"},
                        {"name": "accountType", "type": "VARCHAR(50)", "description": "Type of account"},
                        {"name": "accountId", "type": "VARCHAR(50)", "description": "Tenant account (REQUIRED in all queries)"},
                        {"name": "customerStatus", "type": "VARCHAR(50)", "description": "Status of customer account"},
                    ],
                    "relationships": [],
                },
            ],
            "notes": [
                "ALL queries MUST include WHERE accountId = '<accountId>' for multi-tenant isolation",
                "The tenant ID column is 'accountId', not 'tenant_id'",
                "Use proper SQL syntax and optimize for performance",
                "Join tables when querying across relationships (e.g., JOBINSTANCE with EMPLOYEE)",
                "UUID columns are typically VARCHAR(36) format",
                "Timestamp columns use TIMESTAMP type",
                "Be careful with table name casing - some tables are uppercase (JOBINSTANCE, TAG, etc.)",
            ],
        }

    def update_schema(self, schema_info: Dict):
        """
        Update schema information.

        Args:
            schema_info: New schema information dictionary
        """
        self.schema_info = schema_info



