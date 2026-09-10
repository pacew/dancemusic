from bottle import get, post, request, response, run, HTTPResponse
import time
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import init_db, create_event, create_tune, mark_event_deleted, mark_tune_deleted

# Initialize database
db_conn = init_db()

@get('/sync/state')
def get_state():
    """Return synchronization state"""
    return {
        "last_updated": int(time.time()),
        "status": "synchronized"
    }

@post('/sync/events/<event_id>')
def update_event(event_id):
    """Handle JSON push for Events with LWW conflict resolution"""
    payload = request.json
    if not payload:
        return HTTPResponse(status=400, body="Invalid JSON")
    
    try:
        # Extract event data
        name = payload.get('name')
        date = payload.get('date')
        setlist_id = payload.get('setlist_id')
        updated_at = payload.get('updated_at')
        deleted_at = payload.get('deleted_at')
        
        # Handle tombstone (deleted record)
        if deleted_at is not None:
            mark_event_deleted(db_conn, event_id)
            return {"status": "deleted"}
        
        # Create or update event - LWW resolution happens at DB level
        create_event(db_conn, name, date, setlist_id)
        return {"status": "merged"}
        
    except Exception as e:
        return HTTPResponse(status=500, body=f"Error processing event: {str(e)}")

@post('/sync/tunes')
def sync_tunes():
    """Handle JSON push for Tunes with LWW conflict resolution"""
    payload = request.json
    if not payload:
        return HTTPResponse(status=400, body="Invalid JSON")
    
    try:
        # Extract tune data
        title = payload.get('title')
        artist = payload.get('artist')
        media_hash = payload.get('media_hash')
        updated_at = payload.get('updated_at')
        deleted_at = payload.get('deleted_at')
        
        # Handle tombstone (deleted record)
        if deleted_at is not None:
            tune_id = payload.get('id')
            if tune_id:
                mark_tune_deleted(db_conn, tune_id)
                return {"status": "deleted"}
            else:
                return HTTPResponse(status=400, body="Missing tune ID for deletion")
        
        # Create or update tune - LWW resolution happens at DB level
        tune_id = create_tune(db_conn, title, artist, media_hash)
        return {"status": "merged", "id": tune_id}
        
    except Exception as e:
        return HTTPResponse(status=500, body=f"Error processing tune: {str(e)}")

if __name__ == '__main__':
    run(host='127.0.0.1', port=8080)
