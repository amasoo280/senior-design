"""
Database schema context provider for NL→SQL generation.

This schema is STRICTLY aligned with the actual Sargon Partners database
and intentionally conservative to prevent SQL hallucinations.
"""

from typing import Dict, Optional


class SchemaContext:
    """Provides database schema context for SQL generation."""

    def __init__(self, schema_info: Optional[Dict] = None):
        if schema_info is None:
            schema_info = self._get_default_schema()
        self.schema_info = schema_info

    def get_schema_context(self) -> str:
        """
        Return formatted schema context string for the LLM prompt.
        """
        parts = []

        parts.append("Database: Sargon Partners asset tracking database")
        parts.append("IMPORTANT: ALL queries MUST include WHERE accountId = '<accountId>'")
        parts.append("Timestamp columns are stored as BIGINT milliseconds unless noted.")

        for table in self.schema_info["tables"]:
            parts.append(f"\nTABLE {table['name']}:")

            for col in table["columns"]:
                parts.append(f"  - {col}")

            if "notes" in table:
                for note in table["notes"]:
                    parts.append(f"    NOTE: {note}")

        return "\n".join(parts)

    def _get_default_schema(self) -> Dict:
        """
        Schema aligned exactly with the production EER diagram.
        Only customer-relevant tables are included.
        """
        return {
            "tables": [

                # -------------------------------------------------
                # TAG
                # -------------------------------------------------
                {
                    "name": "TAG",
                    "columns": [
                        "cloudUUID VARCHAR(40) PRIMARY KEY",
                        "accountId VARCHAR(40)",
                        "description TEXT",
                        "serialNumber TEXT",
                        "type TEXT",
                        "isDeleted TINYINT",
                        "latestLocationName TEXT",
                        "latestLocationUUID VARCHAR(40)",
                        "latestLocationTimestamp BIGINT",
                        "latestLocationLatitude DOUBLE",
                        "latestLocationLongitude DOUBLE",
                        "tagAddTimestamp BIGINT",
                        "syncTimestamp BIGINT",
                    ],
                    "notes": [
                        "cloudUUID is the unique identifier for a tag",
                        "latestLocationTimestamp represents the most recent known location (milliseconds)",
                        "DO NOT use tagUUID (does not exist)",
                    ],
                },

                # -------------------------------------------------
                # EquipmentLocation
                # -------------------------------------------------
                {
                    "name": "EquipmentLocation",
                    "columns": [
                        "cloudUUID VARCHAR(40) PRIMARY KEY",
                        "accountId VARCHAR(40)",
                        "employeeOpenUUID VARCHAR(40)",
                        "employeeCloseUUID VARCHAR(40)",
                        "locationName TEXT",
                        "locationType INT",
                        "startTimestamp BIGINT",
                        "endTimestamp BIGINT",
                        "syncTimestamp BIGINT",
                        "notes TEXT",
                    ],
                    "notes": [
                        "Represents the CURRENT location/state of equipment",
                        "Use startTimestamp and endTimestamp for time-based queries",
                    ],
                },

                # -------------------------------------------------
                # EquipmentLocationHistory
                # -------------------------------------------------
                {
                    "name": "EquipmentLocationHistory",
                    "columns": [
                        "cloudUUID VARCHAR(40)",
                        "accountId VARCHAR(40)",
                        "locationUUID VARCHAR(40)",
                        "locationName TEXT",
                        "syncTimestamp BIGINT",
                        "transferUUID VARCHAR(40)",
                        "scanType TINYINT",
                        "sublocation TEXT",
                    ],
                    "notes": [
                        "Historical movement records for equipment",
                        "Use syncTimestamp for time filtering (milliseconds)",
                        "DO NOT use scanTimestamp (does not exist)",
                        "Common join: TAG.latestLocationUUID = EquipmentLocationHistory.locationUUID",
                    ],
                },

                # -------------------------------------------------
                # JOBINSTANCE
                # -------------------------------------------------
                {
                    "name": "JOBINSTANCE",
                    "columns": [
                        "cloudUUID VARCHAR(40) PRIMARY KEY",
                        "jobUUID VARCHAR(40)",
                        "jobName TEXT",
                        "employeeUUID VARCHAR(40)",
                        "jobStartTimestamp BIGINT",
                        "jobCompleteTimestamp BIGINT",
                        "syncTimestamp BIGINT",
                        "isDeleted TINYINT",
                        "accountId VARCHAR(40)",
                    ],
                    "notes": [
                        "Represents jobs assigned to employees",
                        "Use jobCompleteTimestamp and syncTimestamp for time-based queries",
                    ],
                },

                # -------------------------------------------------
                # EMPLOYEE
                # -------------------------------------------------
                {
                    "name": "EMPLOYEE",
                    "columns": [
                        "cloudUUID VARCHAR(40) PRIMARY KEY",
                        "name TEXT",
                        "login VARCHAR(128)",
                        "deviceId VARCHAR(40)",
                        "employeeLevel INT",
                        "accountId VARCHAR(40)",
                        "syncTimestamp BIGINT",
                    ],
                    "notes": [
                        "Employee identity and login information",
                        "DO NOT use company or pin unless explicitly joined elsewhere",
                    ],
                },

                # -------------------------------------------------
                # DATAEVENT
                # -------------------------------------------------
                {
                    "name": "DATAEVENT",
                    "columns": [
                        "cloudUUID VARCHAR(40)",
                        "accountId VARCHAR(40)",
                        "eventType INT",
                        "prevValue TEXT",
                        "postValue TEXT",
                        "eventTime BIGINT",
                        "syncTimestamp BIGINT",
                        "user TEXT",
                    ],
                    "notes": [
                        "Audit-style event records",
                        "Use eventTime or syncTimestamp for time filtering",
                    ],
                },
            ]
        }

    def update_schema(self, schema_info: Dict):
        """Replace schema info dynamically if needed."""
        self.schema_info = schema_info
