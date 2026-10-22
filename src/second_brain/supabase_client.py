import os

from dotenv import load_dotenv
from supabase import create_client, Client


load_dotenv()


SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SECRET_KEY = os.environ["SUPABASE_SECRET_KEY"]


supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_SECRET_KEY
)

# Keep Auth session state isolated from the service-role database client.
# Supabase's Python client mutates its auth headers after sign-in; sharing one
# client would make later database queries run as the end user.
supabase_auth: Client = create_client(
    SUPABASE_URL,
    SUPABASE_SECRET_KEY
)
