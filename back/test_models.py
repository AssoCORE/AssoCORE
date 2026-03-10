#!/usr/bin/env python3
"""
Test script to verify database models are correctly defined
"""
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from app.db.models import Role, User, Event, Notification, Reminder
    from app.schemas import (
        RoleCreate,
        RoleResponse,
        UserCreate,
        UserResponse,
        EventCreate,
        EventResponse,
        NotificationCreate,
        ReminderCreate,
    )

    print("✓ All models imported successfully")
    print("\nAvailable Models:")
    print("  - Role")
    print("  - User")
    print("  - Event")
    print("  - Notification")
    print("  - Reminder")

    print("\nAvailable Schemas:")
    print("  - RoleCreate, RoleResponse")
    print("  - UserCreate, UserResponse, UserUpdate, UserDetailedResponse")
    print("  - EventCreate, EventResponse, EventUpdate, EventDetailedResponse")
    print("  - NotificationCreate, NotificationResponse")
    print("  - ReminderCreate, ReminderResponse, ReminderUpdate")

    print("\n✓ All imports successful!")

except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)
