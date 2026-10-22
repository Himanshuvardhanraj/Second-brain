"""One-time local admin promotion. Never expose this through the API."""
import os
from supabase import create_client

client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SECRET_KEY"])
client.auth.admin.update_user_by_id(
    os.environ["MY_SUPABASE_USER_ID"],
    {"app_metadata": {"role": "admin"}},
)
print("Admin role assigned.")
