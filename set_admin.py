"""
GLOBAL EDU - Administrator Credentials Utility
Usage:
    py set_admin.py                 # View current admin info
    py set_admin.py <new_password>  # Set a custom admin password
"""

import sys
import os
import database as db

if __name__ == '__main__':
    # Initialize DB if needed
    db.init_db(seed=False)

    if len(sys.argv) > 1:
        new_pw = sys.argv[1].strip()
        new_user = sys.argv[2].strip() if len(sys.argv) > 2 else 'admin'
        username, password = db.set_admin_password(username=new_user, password=new_pw)
        print("=" * 60)
        print("  Administrator credentials updated successfully!")
        print(f"  Username: {username}")
        print(f"  Password: {password}")
        print("  Saved to: instance/.admin_credentials.txt")
        print("=" * 60)
    else:
        info = db.get_admin_credentials_info()
        if info:
            print("=" * 60)
            print("  Current Local Development Administrator Credentials:")
            print(f"  Username: {info['username']}")
            print(f"  Password: {info['password']}")
            print("  Saved in: instance/.admin_credentials.txt")
            print("=" * 60)
            print("Tip: To change the password, run:")
            print("  py set_admin.py <your_new_password>")
        else:
            # Generate and set one
            u, p = db.set_admin_password(username='admin')
            print("=" * 60)
            print("  Generated New Administrator Credentials:")
            print(f"  Username: {u}")
            print(f"  Password: {p}")
            print("  Saved to: instance/.admin_credentials.txt")
            print("=" * 60)
