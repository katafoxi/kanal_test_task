# Step 1: import the module
from googleAPI.credential import *

# Step 2: Instance `GoogleCredential()` class
gc = GoogleCredential()

# Step 3: Get credential
# `credential_path` is the place where 'credentials.json' is stored.
# There will be a prompt web page that will download the 'token.pickle'
# into `credential_path`.
creds = gc.credential(credential_path='',
                      credential_scopes=['https://www.googleapis.com/auth/spreadsheets'])

