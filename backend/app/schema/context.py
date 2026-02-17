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
        parts.append("")
        parts.append("DISPLAY RULES:")
        parts.append("- Use serialNumber or description as the primary asset identifier in output")
        parts.append("- Do NOT display cloudUUID or accountId in SELECT output columns")
        parts.append("- If cloudUUID is needed for JOINs, use it internally but do NOT include in final SELECT")
        parts.append("- Alias serialNumber AS asset_number when identifying assets")

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
                        "cloudUUID VARCHAR(40) PRIMARY KEY  -- internal ID, do NOT display to users",
                        "accountId VARCHAR(40)  -- internal, do NOT display to users",
                        "description TEXT  -- user-facing asset description",
                        "serialNumber TEXT  -- user-facing asset identifier, alias as asset_number",
                        "type TEXT",
                        "isDeleted TINYINT",
                        "latestLocationName TEXT",
                        "latestLocationUUID VARCHAR(40)  -- internal, use for JOINs only",
                        "latestLocationTimestamp BIGINT",
                        "latestLocationLatitude DOUBLE",
                        "latestLocationLongitude DOUBLE",
                        "tagAddTimestamp BIGINT",
                        "syncTimestamp BIGINT",
                    ],
                    "notes": [
                        "Use serialNumber or description as the asset identifier in output",
                        "cloudUUID is the internal unique identifier - DO NOT show in results",
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
                        "cloudUUID VARCHAR(40) PRIMARY KEY  -- internal ID, do NOT display",
                        "accountId VARCHAR(40)  -- internal, do NOT display",
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
                        "cloudUUID VARCHAR(40)  -- internal ID, do NOT display",
                        "accountId VARCHAR(40)  -- internal, do NOT display",
                        "locationUUID VARCHAR(40)  -- internal, use for JOINs only",
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
                        "cloudUUID VARCHAR(40) PRIMARY KEY  -- internal ID, do NOT display",
                        "jobUUID VARCHAR(40)",
                        "jobName TEXT",
                        "employeeUUID VARCHAR(40)",
                        "jobStartTimestamp BIGINT",
                        "jobCompleteTimestamp BIGINT",
                        "syncTimestamp BIGINT",
                        "isDeleted TINYINT",
                        "accountId VARCHAR(40)  -- internal, do NOT display",
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
                        "cloudUUID VARCHAR(40) PRIMARY KEY  -- internal ID, do NOT display",
                        "name TEXT",
                        "login VARCHAR(128)",
                        "deviceId VARCHAR(40)",
                        "employeeLevel INT",
                        "accountId VARCHAR(40)  -- internal, do NOT display",
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
                        "cloudUUID VARCHAR(40)  -- internal ID, do NOT display",
                        "accountId VARCHAR(40)  -- internal, do NOT display",
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
