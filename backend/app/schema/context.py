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
        parts.append("- Do NOT display accountId or ANY column whose name contains 'uuid' (case-insensitive)")
        parts.append("- UUID-style columns may be used internally for JOINs, but must NOT appear in visible SELECT output")
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
        Schema aligned exactly with the production database.
        Sensitive columns (passwords, pins, auth IDs, UUIDs) are excluded.
        """
        return {
            "tables": [

                # -------------------------------------------------
                # TAG
                # -------------------------------------------------
                {
                    "name": "TAG",
                    "columns": [
                        "cloudUUID VARCHAR(40) PRIMARY KEY  -- internal ID, do NOT display",
                        "accountId VARCHAR(40)  -- internal, do NOT display",
                        "description TEXT  -- user-facing asset description",
                        "serialNumber TEXT  -- asset serial number, alias as asset_number",
                        "assetNumber VARCHAR(512)  -- alternate asset identifier",
                        "rfid VARCHAR(32)  -- RFID tag number",
                        "barcode TEXT",
                        "type TEXT  -- equipment category",
                        "make TEXT",
                        "model TEXT",
                        "year TEXT",
                        "manufacturer TEXT",
                        "engineModel TEXT",
                        "vinNumber TEXT",
                        "licenseNumber TEXT",
                        "cost TEXT",
                        "rentalCost TEXT  -- rental cost per day",
                        "rentalCostTwo TEXT",
                        "equipmentMonthlyCost TEXT",
                        "equipmentMonthlyPayment TEXT",
                        "equipmentAPR TEXT",
                        "equipmentPayOffDate TEXT",
                        "datePurchased TEXT",
                        "purchasedDate TEXT",
                        "purchasedFrom TEXT",
                        "warrantyTerm TEXT",
                        "expirationTimestamp BIGINT  -- expiration date (milliseconds)",
                        "depreciationMethod TEXT",
                        "hours INT  -- current hours on equipment",
                        "baseHours INT",
                        "miles INT  -- current mileage",
                        "baseMiles INT",
                        "location TEXT  -- assigned location label",
                        "crew TEXT",
                        "notes TEXT",
                        "custom1 TEXT",
                        "custom2 TEXT",
                        "misc TEXT",
                        "maintenanceScheduleName TEXT",
                        "meterId TEXT",
                        "latestLocationName TEXT  -- most recent location name",
                        "latestLocationTimestamp BIGINT  -- milliseconds",
                        "latestLocationLatitude DOUBLE",
                        "latestLocationLongitude DOUBLE",
                        "latestLocationUUID VARCHAR(40)  -- internal, use for JOINs only",
                        "sublocation TEXT",
                        "tagAddTimestamp BIGINT  -- when tag was added (milliseconds)",
                        "syncTimestamp BIGINT",
                        "isDeleted TINYINT",
                    ],
                    "notes": [
                        "Use serialNumber or description as the primary asset identifier in output",
                        "latestLocationTimestamp is milliseconds since epoch",
                        "DO NOT display cloudUUID, accountId, or any UUID column",
                    ],
                },

                # -------------------------------------------------
                # EquipmentLocation  (jobs / dispatch jobs)
                # -------------------------------------------------
                {
                    "name": "EquipmentLocation",
                    "columns": [
                        "cloudUUID VARCHAR(40) PRIMARY KEY  -- internal ID, do NOT display",
                        "accountId VARCHAR(40)  -- internal, do NOT display",
                        "locationName TEXT",
                        "locationType INT  -- 0=Warehouse, 1=Truck, 2=Job",
                        "startTimestamp BIGINT  -- milliseconds",
                        "endTimestamp BIGINT  -- milliseconds, 0 if still open",
                        "jobNumber VARCHAR(50)",
                        "workOrderNumber VARCHAR(50)",
                        "dispatchStreetAddress TEXT",
                        "dispatchLatitude DOUBLE",
                        "dispatchLongitude DOUBLE",
                        "allocatedSignerName TEXT",
                        "allocatedSignatureDate BIGINT  -- milliseconds",
                        "pickedUpSignerName TEXT",
                        "pickedUpSignatureDate BIGINT  -- milliseconds",
                        "pastDueTime BIGINT  -- milliseconds",
                        "hasPastDueReminder TINYINT  -- 0=no, 1=yes",
                        "billed TINYINT  -- 0=no, 1=yes",
                        "notes TEXT",
                        "syncTimestamp BIGINT",
                        "isDeleted TINYINT",
                    ],
                    "notes": [
                        "locationType: 0=Warehouse, 1=Truck, 2=Job/dispatch",
                        "endTimestamp=0 means the job is still open/active",
                        "DO NOT display cloudUUID, accountId, employeeOpenUUID, employeeCloseUUID",
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
                        "tagUUID VARCHAR(40)  -- internal, use for JOINs only",
                        "locationUUID VARCHAR(40)  -- internal, use for JOINs only",
                        "locationName TEXT",
                        "employeeName TEXT",
                        "transferTime BIGINT  -- when transfer occurred (milliseconds)",
                        "syncTimestamp BIGINT",
                        "scanType TINYINT  -- 0=RFID, 1=Barcode, 2=Manual",
                        "sublocation TEXT",
                        "isDeleted SMALLINT",
                    ],
                    "notes": [
                        "Historical movement log for each asset",
                        "Use transferTime for chronological queries (milliseconds)",
                        "scanType: 0=RFID, 1=Barcode, 2=Manual",
                        "Join to TAG: TAG.latestLocationUUID = EquipmentLocationHistory.locationUUID",
                        "DO NOT display cloudUUID, accountId, tagUUID, locationUUID, employeeUUID",
                    ],
                },

                # -------------------------------------------------
                # JOBINSTANCE
                # -------------------------------------------------
                {
                    "name": "JOBINSTANCE",
                    "columns": [
                        "cloudUUID VARCHAR(40) PRIMARY KEY  -- internal ID, do NOT display",
                        "jobUUID VARCHAR(40)  -- internal, use for JOINs only",
                        "jobName TEXT",
                        "jobScanTimestamp BIGINT  -- when job was run (milliseconds)",
                        "jobComplete TINYINT(1)  -- 0=incomplete, 1=complete",
                        "employeeName TEXT",
                        "syncTimestamp BIGINT",
                        "isDeleted TINYINT(1)",
                        "accountId VARCHAR(40)  -- internal, do NOT display",
                    ],
                    "notes": [
                        "jobComplete is a flag (0/1), NOT a timestamp",
                        "jobScanTimestamp is milliseconds since epoch",
                        "DO NOT use jobStartTimestamp or jobCompleteTimestamp (do not exist)",
                        "DO NOT display cloudUUID, accountId, jobUUID, employeeUUID",
                    ],
                },

                # -------------------------------------------------
                # TAGJOBINSTANCE  (which tags were in each job)
                # -------------------------------------------------
                {
                    "name": "TAGJOBINSTANCE",
                    "columns": [
                        "cloudUUID VARCHAR(40) PRIMARY KEY  -- internal ID, do NOT display",
                        "jobUUID VARCHAR(40)  -- internal, use to JOIN to JOBINSTANCE",
                        "tagName TEXT  -- asset name/description",
                        "tagRFID VARCHAR(32)  -- RFID of the tag",
                        "detected TINYINT(1)  -- 0=not detected, 1=detected in job scan",
                        "extraTag TINYINT(1)  -- 0=expected, 1=found in wrong job",
                        "otherJobUUID VARCHAR(40)  -- internal, job this tag belongs to if extraTag=1",
                        "scanType TINYINT",
                        "syncTimestamp BIGINT",
                        "accountId VARCHAR(40)  -- internal, do NOT display",
                    ],
                    "notes": [
                        "Links assets (tags) to job scan instances",
                        "detected=1 means the tag was successfully scanned in the job",
                        "extraTag=1 means the tag was scanned but belongs to a different job",
                        "Join to JOBINSTANCE: TAGJOBINSTANCE.jobUUID = JOBINSTANCE.jobUUID",
                        "DO NOT display cloudUUID, accountId, jobUUID, otherJobUUID",
                    ],
                },

                # -------------------------------------------------
                # EMPLOYEE
                # -------------------------------------------------
                {
                    "name": "EMPLOYEE",
                    "columns": [
                        "cloudUUID VARCHAR(40) PRIMARY KEY  -- internal ID, do NOT display",
                        "name TEXT  -- employee full name",
                        "companyId TEXT  -- employee company ID used for scanning",
                        "employeeLevel INT  -- access level",
                        "barCodeEnabled TINYINT(1)  -- 0=no, 1=yes",
                        "manualScanEnabled TINYINT  -- 0=no, 1=yes",
                        "syncTimestamp BIGINT",
                        "isDeleted TINYINT(1)",
                        "accountId VARCHAR(40)  -- internal, do NOT display",
                    ],
                    "notes": [
                        "DO NOT display cloudUUID, accountId, login, password, pin, auth0UserId, deviceId",
                    ],
                },

                # -------------------------------------------------
                # SUBLOCATION
                # -------------------------------------------------
                {
                    "name": "SUBLOCATION",
                    "columns": [
                        "cloudUUID VARCHAR(50)  -- internal ID, do NOT display",
                        "accountId VARCHAR(50)  -- internal, do NOT display",
                        "sublocation TEXT  -- sublocation name",
                        "syncTimestamp BIGINT",
                        "isDeleted TINYINT",
                    ],
                    "notes": [
                        "List of defined sublocations within locations",
                    ],
                },

                # -------------------------------------------------
                # TYPE  (equipment categories)
                # -------------------------------------------------
                {
                    "name": "TYPE",
                    "columns": [
                        "cloudUUID VARCHAR(40)  -- internal ID, do NOT display",
                        "accountId VARCHAR(40)  -- internal, do NOT display",
                        "name TEXT  -- equipment type/category name",
                        "syncTimestamp BIGINT",
                        "isDeleted TINYINT",
                    ],
                    "notes": [
                        "Lookup table for equipment type/category names",
                        "DO NOT display cloudUUID, accountId",
                    ],
                },

                # -------------------------------------------------
                # DATAEVENT  (audit log)
                # -------------------------------------------------
                {
                    "name": "DATAEVENT",
                    "columns": [
                        "cloudUUID VARCHAR(40)  -- internal ID, do NOT display",
                        "accountId VARCHAR(40)  -- internal, do NOT display",
                        "eventType INT",
                        "preValue TEXT",
                        "postValue TEXT",
                        "eventTime BIGINT  -- milliseconds",
                        "syncTimestamp BIGINT",
                        "user TEXT",
                    ],
                    "notes": [
                        "Audit log of data changes",
                        "Use eventTime for time filtering (milliseconds)",
                        "DO NOT use prevValue (does not exist, correct column is preValue)",
                    ],
                },
            ]
        }

    def update_schema(self, schema_info: Dict):
        """Replace schema info dynamically if needed."""
        self.schema_info = schema_info
