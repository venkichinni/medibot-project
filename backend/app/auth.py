# Demo users for the MediBot project.
# Each user has a password and a role used for RBAC filtering.
DEMO_USERS = {
    "dr.mehta": {"password": "doctor", "role": "doctor"},
    "nurse.priya": {"password": "nurse", "role": "nurse"},
    "billing.ravi": {"password": "billing", "role": "billing_executive"},
    "tech.anand": {"password": "technician", "role": "technician"},
    "admin.sys": {"password": "admin", "role": "admin"},
}


def authenticate_user(username: str, password: str):
    """
    Validate demo username and password.
    Returns user role and a simple demo token if login is successful.
    """
    user = DEMO_USERS.get(username)  # Look up the user by username

    if not user:  # If username does not exist, login fails
        return None

    if user["password"] != password:  # If password does not match, login fails
        return None

    return {
        "username": username,  # Logged-in user's username
        "role": user["role"],  # Role used later for RBAC filtering
        "token": f"demo-token-{username}",  # Simple demo token for frontend/backend flow
    }