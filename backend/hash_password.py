# Makes a password hash for the administrators table (UC16, done by the team).
# Run:  python hash_password.py   then paste the output into the INSERT.
import getpass
from werkzeug.security import generate_password_hash

print(generate_password_hash(getpass.getpass("Password: "), method="pbkdf2:sha256"))
