"""
Database schema context provider for NL→SQL generation.
Aligned with the actual Sargon Partners database schema.
"""

from typing import Dict, Optional


class SchemaContext:
    """Provides database schema context for SQL generation."""

    def __init__(self, schema_info: Optional[Dict] = None):
        if schema_info is None:
            schema_info = self._get_default_schema()

        self.schema_info = schema_info

    def get_schema_context(self) -> str:
        """Return formatted schema context string for the LLM prompt."""
        parts = []

        parts.append("Database: Sargon Partners asset tracking database")
        parts.append("Tenant isolation: ALL queries MUST filter by accountId")

        for table in self.schema_info["tables"]:
            parts.append(f"\nTABLE {table['name']}:")

            for col in table["columns"]:
                parts.append(f"  - {col}")

        return "\n".join(parts)

    def _get_default_schema(self) -> Dict:
        """
        Schema aligned with the real database ERD.
        Focused on correctness over completeness.
        """
        return {
            "tables": [
                {
                    "name": "TAG",
                    "columns": [
                        "cloudUUID VARCHAR(40) PRIMARY KEY",
                        "accountId VARCHAR(40)",
                        "description TEXT",
                        "rfid VARCHAR(32)",
                        "syncTimestamp BIGINT",
                        "type TEXT",
                        "cost TEXT",
                        "datePurchased TEXT",
                        "notes TEXT",
                        "rentalCost TEXT",
                        "integrationId VARCHAR(40)",
                        "barcode TEXT",
                        "rentalCostTwo TEXT",
                        "isDeleted TINYINT",
                        "iBeaconUUID VARCHAR(50)",
                        "iBeaconMajor INT",
                        "iBeaconMinor INT",
                        "latestLocationName TEXT",
                        "latestLocationTimestamp BIGINT",
                        "latestLocationUUID VARCHAR(40)",
                        "tagAddTimestamp BIGINT",
                        "latestLocationLatitude DOUBLE",
                        "latestLocationLongitude DOUBLE",
                        "sublocation TEXT",
                        "assetNumber VARCHAR(512)",
                        "serialNumber TEXT",
                        "model TEXT",
                        "manufacturer TEXT",
                    ],
                },
                {
                    "name": "EquipmentLocation",
                    "columns": [
                        "cloudUUID VARCHAR(40) PRIMARY KEY",
                        "accountId VARCHAR(40)",
                        "employeeCloseUUID VARCHAR(40)",
                        "employeeOpenUUID VARCHAR(40)",
                        "startTimestamp BIGINT",
                        "endTimestamp BIGINT",
                        "locationName TEXT",
                        "locationType INT",
                        "syncTimestamp BIGINT",
                        "notes TEXT",
                        "dispatchLatitude DOUBLE",
                        "dispatchLongitude DOUBLE",
                        "pickupLatitude DOUBLE",
                        "pickupLongitude DOUBLE",
                    ],
                },
                {
                    "name": "EquipmentLocationHistory",
                    "columns": [
                        "cloudUUID VARCHAR(40)",
                        "accountId VARCHAR(40)",
                        "locationName TEXT",
                        "locationUUID VARCHAR(40)",
                        "scanTimestamp BIGINT",
                        "transferUUID VARCHAR(40)",
                        "scanType TINYINT",
                        "sublocation TEXT",
                    ],
                },
                {
                    "name": "JOBINSTANCE",
                    "columns": [
                        "cloudUUID VARCHAR(40) PRIMARY KEY",
                        "jobName TEXT",
                        "jobUUID VARCHAR(40)",
                        "jobStartTimestamp BIGINT",
                        "jobCompleteTimestamp BIGINT",
                        "syncTimestamp BIGINT",
                        "isDeleted TINYINT",
                        "employeeName TEXT",
                        "employeeUUID VARCHAR(40)",
                        "accountId VARCHAR(40)",
                    ],
                },
                {
                    "name": "DATAEVENT",
                    "columns": [
                        "cloudUUID VARCHAR(40)",
                        "accountId VARCHAR(40)",
                        "syncTimestamp BIGINT",
                        "eventTime BIGINT",
                        "user TEXT",
                        "prevValue TEXT",
                        "postValue TEXT",
                        "eventType INT",
                    ],
                },
                {
                    "name": "EMPLOYEE",
                    "columns": [
                        "cloudUUID VARCHAR(40) PRIMARY KEY",
                        "name TEXT",
                        "company TEXT",
                        "pin TEXT",
                        "accountId VARCHAR(40)",
                        "deviceId VARCHAR(40)",
                        "login VARCHAR(128)",
                    ],
                },
                {
                    "name": "BeaconScan",
                    "columns": [
                        "cloudUUID VARCHAR(40)",
                        "beaconId VARCHAR(50)",
                        "scanTime BIGINT",
                        "latitude DOUBLE",
                        "longitude DOUBLE",
                        "batteryLevel INT",
                        "rssI INT",
                    ],
                },
                {
                    "name": "BeaconCurrentStatus",
                    "columns": [
                        "beaconId VARCHAR(50)",
                        "readerId VARCHAR(50)",
                        "scanTime BIGINT",
                        "latitude DOUBLE",
                        "longitude DOUBLE",
                        "batteryLevel INT",
                        "speed INT",
                    ],
                },
                {
                    "name": "SUBLOCATION",
                    "columns": [
                        "cloudUUID VARCHAR(50)",
                        "accountId VARCHAR(50)",
                        "sublocation TEXT",
                        "syncTimestamp BIGINT",
                        "isDeleted TINYINT",
                    ],
                },
                {
                    "name": "ITVUSER",
                    "columns": [
                        "email VARCHAR(128)",
                        "apiKey VARCHAR(40)",
                        "accountType INT",
                        "accountId VARCHAR(40)",
                        "companyName TEXT",
                        "timeZone VARCHAR(40)",
                        "isAccountActive TINYINT",
                    ],
                },
            ]
        }

    def update_schema(self, schema_info: Dict):
        """Replace schema info dynamically if needed."""
        self.schema_info = schema_info
