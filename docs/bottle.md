# Bottle Framework API Contract

## Core Imports

from bottle import get, post, request, response, run, HTTPResponse

## Routing and URL Parameters

Use method-specific decorators. Path variables are enclosed in angle brackets.

@get('/sync/events')
def list_events():
return {"events": []}

@post('/sync/events/<event_id>')
def update_event(event_id):
pass

## Reading JSON Payloads

Extract parsed JSON dictionaries using the request.json property.

@post('/sync/tunes')
def sync_tunes():
payload = request.json
if not payload:
return HTTPResponse(status=400, body="Invalid JSON")

```
tune_id = payload.get('id')
return {"status": "merged"}

```

## Returning JSON

Return a standard Python dictionary. Bottle automatically serializes it to a JSON string and sets the Content-Type: application/json header.

@get('/sync/state')
def get_state():
return {
"last_updated": 1700000000,
"status": "synchronized"
}

## Error Handling

Return an HTTPResponse object to set specific status codes for client errors or conflicts.

if conflict_detected:
return HTTPResponse(status=409, body="Conflict detected")

## Initialization

To start the server block, use run().

if __name__ == '__main__':
  run(host='127.0.0.1', port=8080)
