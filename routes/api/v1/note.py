from flask import Blueprint, request, jsonify
from models import load_notes, save_notes

note_bp = Blueprint('note', __name__)

@note_bp.route('/<app_id>', methods=['POST'])
def set_note(app_id):
    data = request.json
    note = data.get('note', '')
    notes = load_notes()
    if note:
        notes[app_id] = note
    else:
        notes.pop(app_id, None)
    save_notes(notes)
    return jsonify({'status': 'ok'})