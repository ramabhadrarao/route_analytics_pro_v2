import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('route_analysis.db')
cursor = conn.cursor()

# Define the update values and target route ID
route_id = 'af7c8826-2d03-4239-aceb-0c329bbf2064'
from_address = 'MEERUT DEPOT [1146]'
to_address = 'MOTI FILLING STATION [0041025372]'

# Perform the update
cursor.execute("""
    UPDATE routes
    SET from_address = ?, to_address = ?
    WHERE id = ?
""", (from_address, to_address, route_id))

# Commit changes and close the connection
conn.commit()
conn.close()

print("Route updated successfully.")
