<?php
// Simulate WordPress-like includes and enqueue by handle
require_once __DIR__ . '/inc/register.php';
wp_enqueue_style('other-h');
?>
<?php
// Note-taking app PHP (simple backend simulation)

$notes = isset($_POST['notes']) ? json_decode($_POST['notes'], true) : [];

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['action'])) {
    if ($_POST['action'] === 'save') {
        // Simulate saving notes
        file_put_contents('notes.json', json_encode($notes));
        echo json_encode(['status' => 'success']);
        exit;
    }
}

// HTML output
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Note-Taking App (PHP)</title>
</head>
<body>
    <div id="main-container">
        <div class="nt-header">
            <h1>My Notes (PHP Version)</h1>
        </div>
        
        <form class="nt-form" method="post" id="note-form">
            <input type="text" class="nt-input" name="new_note" placeholder="Enter a note...">
            <button type="submit" class="nt-btn">Add Note</button>
        </form>
        
        <ul class="nt-note-list">
            <?php
            // Display sample notes
            $sampleNotes = ['PHP Note 1', 'PHP Note 2'];
            foreach ($sampleNotes as $note) {
                echo "<li class='nt-note-item note'>$note</li>";
            }
            ?>
        </ul>
    </div>
    
    <script src="script.js"></script>
</body>
</html>