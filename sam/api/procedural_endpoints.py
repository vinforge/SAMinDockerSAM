"""
Secure API Endpoints for Procedural Memory
==========================================

Provides Flask/FastAPI endpoints for procedural memory CRUD operations
with SAM security integration and comprehensive error handling.

Author: SAM Development Team
Version: 2.0.0
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from flask import Blueprint, request, jsonify
from functools import wraps

logger = logging.getLogger(__name__)

# Create Blueprint for procedural memory endpoints
procedural_bp = Blueprint('procedural', __name__, url_prefix='/api/procedural')

def require_unlock(f):
    """Security decorator to ensure SAM is unlocked before accessing procedures."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Check if SAM security is available and unlocked
            from security import get_security_manager
            security_manager = get_security_manager()
            
            if not security_manager.is_unlocked():
                return jsonify({
                    'success': False,
                    'error': 'SAM is locked. Please unlock to access procedural memory.',
                    'error_code': 'SECURITY_LOCKED'
                }), 403
                
        except ImportError:
            # Security not available - allow access (development mode)
            logger.warning("Security module not available - allowing procedural access")
        except Exception as e:
            logger.error(f"Security check failed: {e}")
            return jsonify({
                'success': False,
                'error': 'Security verification failed',
                'error_code': 'SECURITY_ERROR'
            }), 500
        
        return f(*args, **kwargs)
    return decorated_function

def get_procedural_store():
    """Get the procedural memory store instance."""
    try:
        from sam.memory.procedural_memory import get_procedural_memory_store
        return get_procedural_memory_store()
    except Exception as e:
        logger.error(f"Failed to get procedural store: {e}")
        return None

@procedural_bp.route('/procedures', methods=['GET'])
@require_unlock
def get_all_procedures():
    """Get all procedures with optional filtering."""
    try:
        store = get_procedural_store()
        if not store:
            return jsonify({
                'success': False,
                'error': 'Procedural memory store not available'
            }), 500
        
        # Get query parameters for filtering
        category = request.args.get('category')
        difficulty = request.args.get('difficulty_level')
        tags = request.args.getlist('tags')
        
        procedures = store.get_all_procedures()
        
        # Apply filters if provided
        if category or difficulty or tags:
            filtered_procedures = []
            for proc in procedures:
                if category and proc.category != category:
                    continue
                if difficulty and proc.difficulty_level != difficulty:
                    continue
                if tags and not set(tags).intersection(set(proc.tags)):
                    continue
                filtered_procedures.append(proc)
            procedures = filtered_procedures
        
        # Convert to dict format
        procedures_data = [proc.dict() for proc in procedures]
        
        return jsonify({
            'success': True,
            'procedures': procedures_data,
            'total': len(procedures_data)
        })
        
    except Exception as e:
        logger.error(f"Failed to get procedures: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@procedural_bp.route('/procedures/<procedure_id>', methods=['GET'])
@require_unlock
def get_procedure(procedure_id: str):
    """Get a specific procedure by ID."""
    try:
        store = get_procedural_store()
        if not store:
            return jsonify({
                'success': False,
                'error': 'Procedural memory store not available'
            }), 500
        
        procedure = store.get_procedure(procedure_id)
        if not procedure:
            return jsonify({
                'success': False,
                'error': 'Procedure not found'
            }), 404
        
        return jsonify({
            'success': True,
            'procedure': procedure.dict()
        })
        
    except Exception as e:
        logger.error(f"Failed to get procedure {procedure_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@procedural_bp.route('/procedures', methods=['POST'])
@require_unlock
def create_procedure():
    """Create a new procedure."""
    try:
        store = get_procedural_store()
        if not store:
            return jsonify({
                'success': False,
                'error': 'Procedural memory store not available'
            }), 500
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Validate required fields
        required_fields = ['name', 'description', 'steps']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Import and create procedure
        from sam.memory.procedural_memory import Procedure, ProcedureStep
        
        # Process steps
        steps = []
        for i, step_data in enumerate(data['steps']):
            step_data['step_number'] = i + 1
            steps.append(ProcedureStep(**step_data))
        
        # Create procedure
        procedure_data = data.copy()
        procedure_data['steps'] = steps
        procedure = Procedure(**procedure_data)
        
        # Add to store
        success = store.add_procedure(procedure)
        if not success:
            return jsonify({
                'success': False,
                'error': 'Failed to save procedure'
            }), 500
        
        return jsonify({
            'success': True,
            'procedure': procedure.dict(),
            'message': f'Procedure "{procedure.name}" created successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Failed to create procedure: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@procedural_bp.route('/procedures/<procedure_id>', methods=['PUT'])
@require_unlock
def update_procedure(procedure_id: str):
    """Update an existing procedure."""
    try:
        store = get_procedural_store()
        if not store:
            return jsonify({
                'success': False,
                'error': 'Procedural memory store not available'
            }), 500
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Check if procedure exists
        existing_procedure = store.get_procedure(procedure_id)
        if not existing_procedure:
            return jsonify({
                'success': False,
                'error': 'Procedure not found'
            }), 404
        
        # Process steps if provided
        if 'steps' in data:
            from sam.memory.procedural_memory import ProcedureStep
            steps = []
            for i, step_data in enumerate(data['steps']):
                step_data['step_number'] = i + 1
                steps.append(ProcedureStep(**step_data))
            data['steps'] = steps
        
        # Update procedure
        success = store.update_procedure(procedure_id, data)
        if not success:
            return jsonify({
                'success': False,
                'error': 'Failed to update procedure'
            }), 500
        
        # Get updated procedure
        updated_procedure = store.get_procedure(procedure_id)
        
        return jsonify({
            'success': True,
            'procedure': updated_procedure.dict(),
            'message': f'Procedure "{updated_procedure.name}" updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Failed to update procedure {procedure_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@procedural_bp.route('/procedures/<procedure_id>', methods=['DELETE'])
@require_unlock
def delete_procedure(procedure_id: str):
    """Delete a procedure."""
    try:
        store = get_procedural_store()
        if not store:
            return jsonify({
                'success': False,
                'error': 'Procedural memory store not available'
            }), 500
        
        # Check if procedure exists
        procedure = store.get_procedure(procedure_id)
        if not procedure:
            return jsonify({
                'success': False,
                'error': 'Procedure not found'
            }), 404
        
        procedure_name = procedure.name
        
        # Delete procedure
        success = store.delete_procedure(procedure_id)
        if not success:
            return jsonify({
                'success': False,
                'error': 'Failed to delete procedure'
            }), 500
        
        return jsonify({
            'success': True,
            'message': f'Procedure "{procedure_name}" deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Failed to delete procedure {procedure_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@procedural_bp.route('/search', methods=['GET'])
@require_unlock
def search_procedures():
    """Search procedures with advanced filtering."""
    try:
        store = get_procedural_store()
        if not store:
            return jsonify({
                'success': False,
                'error': 'Procedural memory store not available'
            }), 500
        
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({
                'success': False,
                'error': 'Search query is required'
            }), 400
        
        # Get filters
        filters = {}
        if request.args.get('category'):
            filters['category'] = request.args.get('category')
        if request.args.get('difficulty_level'):
            filters['difficulty_level'] = request.args.get('difficulty_level')
        if request.args.getlist('tags'):
            filters['tags'] = request.args.getlist('tags')
        
        # Perform search
        results = store.search_procedures(query, filters)
        
        # Format results
        search_results = []
        for procedure, score in results:
            result = procedure.dict()
            result['relevance_score'] = round(score, 3)
            search_results.append(result)
        
        return jsonify({
            'success': True,
            'query': query,
            'results': search_results,
            'total': len(search_results)
        })
        
    except Exception as e:
        logger.error(f"Failed to search procedures: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@procedural_bp.route('/procedures/<procedure_id>/execute', methods=['POST'])
@require_unlock
def record_execution(procedure_id: str):
    """Record that a procedure was executed."""
    try:
        store = get_procedural_store()
        if not store:
            return jsonify({
                'success': False,
                'error': 'Procedural memory store not available'
            }), 500
        
        success = store.record_procedure_execution(procedure_id)
        if not success:
            return jsonify({
                'success': False,
                'error': 'Failed to record execution or procedure not found'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Procedure execution recorded'
        })
        
    except Exception as e:
        logger.error(f"Failed to record execution for {procedure_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@procedural_bp.route('/stats', methods=['GET'])
@require_unlock
def get_stats():
    """Get procedural memory statistics."""
    try:
        store = get_procedural_store()
        if not store:
            return jsonify({
                'success': False,
                'error': 'Procedural memory store not available'
            }), 500
        
        stats = store.get_procedure_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
