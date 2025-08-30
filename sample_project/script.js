// Note-taking app JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const noteForm = document.getElementById('note-form');
    const noteInput = document.getElementById('note-input');
    const noteList = document.getElementById('note-list');
    
    // Load existing notes (simulated)
    loadNotes();
    
    // Add note event
    noteForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const noteText = noteInput.value.trim();
        if (noteText) {
            addNote(noteText);
            noteInput.value = '';
        }
    });
    
    function addNote(text) {
        const li = document.createElement('li');
        li.className = 'nt-note-item note';  // Using both classes
        li.textContent = text;
        
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'nt-btn';
        deleteBtn.textContent = 'Delete';
        deleteBtn.onclick = function() {
            noteList.removeChild(li);
        };
        
        li.appendChild(deleteBtn);
        noteList.appendChild(li);
    }
    
    function loadNotes() {
        // Simulated loading of notes
        const sampleNotes = ['First note', 'Second note'];
        sampleNotes.forEach(note => addNote(note));
    }
});