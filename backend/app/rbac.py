# Maps each user role to the document collections they are allowed to access.
# This is used by the API and retrieval layer to know what data a role can see.
ROLE_COLLECTIONS = {
    "doctor": ["general", "clinical", "nursing"],
    "nurse": ["general", "nursing"],
    "billing_executive": ["general", "billing"],
    "technician": ["general", "equipment"],
    "admin": ["general", "clinical", "nursing", "billing", "equipment"],
}


# Maps each document collection to the roles that are allowed to access it.
# During ingestion, these roles will be stored as metadata on every document chunk.
COLLECTION_ACCESS_ROLES = {
    "general": ["doctor", "nurse", "billing_executive", "technician", "admin"],
    "clinical": ["doctor", "admin"],
    "nursing": ["nurse", "doctor", "admin"],
    "billing": ["billing_executive", "admin"],
    "equipment": ["technician", "admin"],
}


# Only these roles are allowed to ask analytical/database questions using SQL RAG.
SQL_ROLES = ["billing_executive", "admin"]


def get_collections_for_role(role: str) -> list[str]:
    """
    Return the list of document collections accessible to a given role.
    Used by the /collections/{role} API endpoint and frontend role display.
    """
    return ROLE_COLLECTIONS.get(role, [])


def can_use_sql(role: str) -> bool:
    """
    Check whether a role is allowed to use SQL RAG.
    SQL RAG is restricted because it can expose operational database insights.
    """
    return role in SQL_ROLES