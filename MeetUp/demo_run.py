# demo_run.py
"""
Demo script showing how to use the MeetUp! Python modules

This demonstrates:
1. Friend Matching Service - Core business logic
2. Message Controller - REST API endpoints (Flask version)
"""

print("=" * 70)
print("MeetUp! Social Networking App - Python Demo")
print("=" * 70)
print()

# ============================================================================
# PART 1: Friend Matching Service Demo
# ============================================================================

print("PART 1: Friend Matching Service")
print("-" * 70)
print()

from friend_matching_service import (
    FriendMatchingService, 
    Schedule, 
    FriendSuggestion
)
from datetime import datetime

# Mock repositories for demo
class MockScheduleRepository:
    def get_schedule_by_user(self, user_id):
        # Return demo schedule for Alice (user 1)
        if user_id == 1:
            return Schedule(
                user_id=1,
                classes=[
                    {
                        'course': 'CS101',
                        'building': 'Science Hall',
                        'day': 'Monday',
                        'start_time': '09:00',
                        'end_time': '10:15'
                    },
                    {
                        'course': 'MATH201',
                        'building': 'Math Building',
                        'day': 'Monday',
                        'start_time': '11:00',
                        'end_time': '12:15'
                    }
                ],
                walking_paths=[
                    [(40.7128, -74.0060), (40.7129, -74.0061), (40.7130, -74.0062)]
                ]
            )
        return None
    
    def get_schedules_by_university(self, university_id, exclude_user_ids):
        # Return demo schedules for Bob and Charlie
        return [
            Schedule(
                user_id=2,  # Bob - has overlap with Alice
                classes=[
                    {
                        'course': 'CS101',  # Shared with Alice!
                        'building': 'Science Hall',
                        'day': 'Monday',
                        'start_time': '09:00',
                        'end_time': '10:15'
                    },
                    {
                        'course': 'ENG202',
                        'building': 'English Hall',
                        'day': 'Monday',
                        'start_time': '10:30',  # Close to Alice's next class
                        'end_time': '11:45'
                    }
                ],
                walking_paths=[
                    [(40.7128, -74.0060), (40.7129, -74.0061)]  # Similar path
                ]
            ),
            Schedule(
                user_id=3,  # Charlie - minimal overlap
                classes=[
                    {
                        'course': 'PHYS101',
                        'building': 'Physics Building',
                        'day': 'Tuesday',
                        'start_time': '14:00',
                        'end_time': '15:15'
                    }
                ],
                walking_paths=[
                    [(41.8781, -87.6298)]  # Different location (Chicago)
                ]
            )
        ]

class MockConnectionRepository:
    def get_connections(self, user_id):
        return []  # No existing connections
    
    def get_blocked_users(self, user_id):
        return []  # No blocked users
    
    def get_connection_between(self, user1_id, user2_id):
        return None  # No existing connection
    
    def is_blocked(self, user1_id, user2_id):
        return False
    
    def create_connection(self, user1_id, user2_id, status, suggested_at):
        return {
            'id': 1,
            'user1_id': user1_id,
            'user2_id': user2_id,
            'status': status,
            'suggested_at': suggested_at
        }

# Initialize service with mock repositories
schedule_repo = MockScheduleRepository()
connection_repo = MockConnectionRepository()
friend_service = FriendMatchingService(schedule_repo, connection_repo)

print("Scenario: Alice wants friend suggestions")
print()

# Generate friend suggestions for Alice (user 1)
print("Generating friend suggestions for Alice (User ID: 1)...")
suggestions = friend_service.generate_suggestions(user_id=1, limit=10)

print(f"Found {len(suggestions)} suggestions:")
print()

for i, suggestion in enumerate(suggestions, 1):
    print(f"Suggestion #{i}:")
    print(f"  User ID: {suggestion.suggested_user_id}")
    print(f"  Match Score: {suggestion.score:.2f}")
    print(f"  Shared Classes: {', '.join(suggestion.shared_classes) if suggestion.shared_classes else 'None'}")
    print(f"  Path Overlap: {suggestion.path_overlap_percent:.1f}%")
    print(f"  Time Proximity: {suggestion.time_proximity_minutes} minutes" if suggestion.time_proximity_minutes > 0 else "  Time Proximity: Not applicable")
    print()

# Demo: Create connection request
print("Alice wants to connect with Bob (User ID: 2)")
connection = friend_service.create_connection_request(
    requesting_user_id=1,
    target_user_id=2
)
print(f"✓ Connection request created! Status: {connection['status']}")
print()

# Demo: Accept connection
print("Bob accepts Alice's connection request")
accepted = friend_service.accept_connection(
    connection_id=connection['id'],
    accepting_user_id=2
)
print(f"✓ Connection accepted! Status: {accepted['status']}")
print()

print("=" * 70)
print()

# ============================================================================
# PART 2: Message Controller Demo
# ============================================================================

print("PART 2: Message Controller (Flask REST API)")
print("-" * 70)
print()

print("The Message Controller is a Flask web application that provides")
print("REST API endpoints for messaging functionality.")
print()

print("To run the Message Controller:")
print()
print("1. Install Flask:")
print("   pip install flask")
print()
print("2. Run the controller:")
print("   python message_controller_python.py")
print()
print("3. The API will be available at: http://localhost:5000")
print()

print("Available API Endpoints:")
print()
print("  POST   /api/messages")
print("         Send a message to a friend")
print("         Body: {recipient_id, content, message_type}")
print()
print("  GET    /api/messages/conversation/<user_id>")
print("         Get message history with a specific user")
print()
print("  GET    /api/messages/conversations")
print("         Get list of all conversations")
print()
print("  PUT    /api/messages/<message_id>/read")
print("         Mark a message as read")
print()
print("  DELETE /api/messages/<message_id>")
print("         Delete a message")
print()
print("  GET    /api/messages/unread/count")
print("         Get count of unread messages")
print()

print("=" * 70)
print()

print("Example API Request (using curl):")
print()
print("curl -X POST http://localhost:5000/api/messages \\")
print("  -H 'Content-Type: application/json' \\")
print("  -H 'Authorization: Bearer <your-jwt-token>' \\")
print("  -d '{")
print('    "recipient_id": 2,')
print('    "content": "Hey! Want to study together?",')
print('    "message_type": "text"')
print("  }'")
print()

print("=" * 70)
print()

# ============================================================================
# PART 3: Running the Tests
# ============================================================================

print("PART 3: Running Unit Tests")
print("-" * 70)
print()

print("To run the unit tests for Friend Matching Service:")
print()
print("1. Install pytest:")
print("   pip install pytest")
print()
print("2. Run the tests:")
print("   pytest test_friend_matching_service.py -v")
print()
print("The tests will verify:")
print("  ✓ Friend suggestion generation")
print("  ✓ Schedule overlap calculation")
print("  ✓ Path overlap calculation")
print("  ✓ Connection request creation")
print("  ✓ Connection acceptance")
print("  ✓ User blocking")
print("  ✓ And more...")
print()

print("=" * 70)
print()

print("SUMMARY")
print("-" * 70)
print()
print("✓ Friend Matching Service - Fully functional Python code")
print("✓ Message Controller - Flask REST API (Python)")
print("✓ Unit Tests - pytest test suite")
print()
print("All code is 100% Python and can be run directly!")
print()
print("=" * 70)
