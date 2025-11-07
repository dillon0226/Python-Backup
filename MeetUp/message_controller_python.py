# message_controller.py (Python/Flask version)

from flask import Blueprint, request, jsonify
from functools import wraps
import logging
from typing import Dict, Any

# Initialize logger
logger = logging.getLogger(__name__)

# Create Blueprint for message routes
message_bp = Blueprint('messages', __name__, url_prefix='/api/messages')

# Mock MessageService - in real implementation, import actual service
class MessageService:
    def __init__(self):
        pass
    
    def send_message(self, data: Dict) -> Dict:
        """Send a message (mock implementation)"""
        # Real implementation would save to database
        return {
            'id': 123,
            'created_at': '2025-01-15T10:30:00Z'
        }
    
    def get_conversation(self, params: Dict) -> list:
        """Get conversation history (mock implementation)"""
        return []
    
    def get_user_conversations(self, user_id: int) -> list:
        """Get all conversations for user (mock implementation)"""
        return []
    
    def mark_as_read(self, message_id: int, user_id: int):
        """Mark message as read (mock implementation)"""
        pass
    
    def delete_message(self, message_id: int, user_id: int):
        """Delete message (mock implementation)"""
        pass
    
    def get_unread_count(self, user_id: int) -> int:
        """Get unread message count (mock implementation)"""
        return 0

# Initialize service
message_service = MessageService()


# Authentication decorator (mock implementation)
def auth_required(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # In real implementation, verify JWT token
        # For now, mock user data
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({
                'success': False,
                'error': 'Authentication required'
            }), 401
        
        # Mock user extraction from JWT
        request.user = {'id': 1, 'email': 'test@university.edu'}
        return f(*args, **kwargs)
    return decorated_function


def validate_request(required_fields: Dict[str, type]) -> Dict[str, Any]:
    """Validate request data"""
    data = request.get_json()
    if not data:
        return {'error': 'Request body is required'}
    
    errors = []
    for field, field_type in required_fields.items():
        if field not in data:
            errors.append(f'{field} is required')
        elif not isinstance(data[field], field_type):
            errors.append(f'{field} must be {field_type.__name__}')
    
    if errors:
        return {'error': errors}
    
    return {'data': data}


@message_bp.route('/', methods=['POST'])
@auth_required
def send_message():
    """
    POST /api/messages
    Send a message to a connected friend
    """
    try:
        # Get request data
        data = request.get_json()
        
        # Validate required fields
        required_fields = {
            'recipient_id': int,
            'content': str,
            'message_type': str
        }
        
        validation = validate_request(required_fields)
        if 'error' in validation:
            return jsonify({
                'success': False,
                'errors': validation['error']
            }), 400
        
        data = validation['data']
        sender_id = request.user['id']
        
        # Validate content
        content = data['content'].strip()
        if not content:
            return jsonify({
                'success': False,
                'error': 'Message content cannot be empty'
            }), 400
        
        if len(content) > 5000:
            return jsonify({
                'success': False,
                'error': 'Message too long (max 5000 characters)'
            }), 400
        
        # Validate message type
        valid_types = ['text', 'emoji', 'gif', 'jpeg', 'multimedia', 'link']
        if data['message_type'] not in valid_types:
            return jsonify({
                'success': False,
                'error': f'Invalid message type. Must be one of: {", ".join(valid_types)}'
            }), 400
        
        # Prevent sending to self
        if sender_id == data['recipient_id']:
            return jsonify({
                'success': False,
                'error': 'Cannot send message to yourself'
            }), 400
        
        # Send message through service
        message = message_service.send_message({
            'sender_id': sender_id,
            'recipient_id': data['recipient_id'],
            'content': content,
            'message_type': data['message_type'],
            'metadata': data.get('metadata', {})
        })
        
        logger.info(f"Message sent: {sender_id} -> {data['recipient_id']}, "
                   f"type: {data['message_type']}")
        
        return jsonify({
            'success': True,
            'data': {
                'message_id': message['id'],
                'timestamp': message['created_at'],
                'status': 'delivered'
            }
        }), 201
        
    except ValueError as e:
        if 'not connected' in str(e).lower():
            return jsonify({
                'success': False,
                'error': 'You can only send messages to connected friends'
            }), 403
        elif 'blocked' in str(e).lower():
            return jsonify({
                'success': False,
                'error': 'Cannot send message to this user'
            }), 403
        else:
            raise
            
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to send message. Please try again.'
        }), 500


@message_bp.route('/conversation/<int:user_id>', methods=['GET'])
@auth_required
def get_conversation(user_id: int):
    """
    GET /api/messages/conversation/<user_id>
    Get message history with a specific user
    """
    try:
        current_user_id = request.user['id']
        
        # Get query parameters
        limit = request.args.get('limit', default=50, type=int)
        before_id = request.args.get('before_id', default=None, type=int)
        
        # Get messages from service
        messages = message_service.get_conversation({
            'user1_id': current_user_id,
            'user2_id': user_id,
            'limit': limit,
            'before_id': before_id
        })
        
        return jsonify({
            'success': True,
            'data': {
                'messages': messages,
                'count': len(messages),
                'has_more': len(messages) == limit
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving conversation: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve messages'
        }), 500


@message_bp.route('/conversations', methods=['GET'])
@auth_required
def get_conversations():
    """
    GET /api/messages/conversations
    Get list of all conversations for current user
    """
    try:
        user_id = request.user['id']
        
        # Get all conversations
        conversations = message_service.get_user_conversations(user_id)
        
        return jsonify({
            'success': True,
            'data': {
                'conversations': conversations,
                'count': len(conversations)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving conversations: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve conversations'
        }), 500


@message_bp.route('/<int:message_id>/read', methods=['PUT'])
@auth_required
def mark_message_read(message_id: int):
    """
    PUT /api/messages/<message_id>/read
    Mark a message as read
    """
    try:
        user_id = request.user['id']
        
        # Mark as read
        message_service.mark_as_read(message_id, user_id)
        
        return jsonify({
            'success': True,
            'message': 'Message marked as read'
        }), 200
        
    except ValueError as e:
        if 'not found' in str(e).lower() or 'not authorized' in str(e).lower():
            return jsonify({
                'success': False,
                'error': 'Message not found'
            }), 404
        else:
            raise
            
    except Exception as e:
        logger.error(f"Error marking message as read: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to mark message as read'
        }), 500


@message_bp.route('/<int:message_id>', methods=['DELETE'])
@auth_required
def delete_message(message_id: int):
    """
    DELETE /api/messages/<message_id>
    Delete a message (soft delete)
    """
    try:
        user_id = request.user['id']
        
        # Delete message (sender only)
        message_service.delete_message(message_id, user_id)
        
        logger.info(f"Message deleted: {message_id} by user {user_id}")
        
        return jsonify({
            'success': True,
            'message': 'Message deleted successfully'
        }), 200
        
    except ValueError as e:
        if 'not found' in str(e).lower() or 'not authorized' in str(e).lower():
            return jsonify({
                'success': False,
                'error': 'Cannot delete this message'
            }), 403
        else:
            raise
            
    except Exception as e:
        logger.error(f"Error deleting message: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to delete message'
        }), 500


@message_bp.route('/unread/count', methods=['GET'])
@auth_required
def get_unread_count():
    """
    GET /api/messages/unread/count
    Get count of unread messages
    """
    try:
        user_id = request.user['id']
        
        count = message_service.get_unread_count(user_id)
        
        return jsonify({
            'success': True,
            'data': {
                'unread_count': count
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting unread count: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get unread count'
        }), 500


# Flask app setup (for running standalone)
if __name__ == '__main__':
    from flask import Flask
    
    app = Flask(__name__)
    app.register_blueprint(message_bp)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Message Controller is running!")
    print("Available endpoints:")
    print("  POST   /api/messages")
    print("  GET    /api/messages/conversation/<user_id>")
    print("  GET    /api/messages/conversations")
    print("  PUT    /api/messages/<message_id>/read")
    print("  DELETE /api/messages/<message_id>")
    print("  GET    /api/messages/unread/count")
    
    app.run(debug=True, port=5000)
