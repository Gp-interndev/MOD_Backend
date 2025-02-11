<?php
header('Content-Type: application/json');

// Check if a file is uploaded via form-data
if (!isset($_FILES['file']) || $_FILES['file']['error'] != UPLOAD_ERR_OK) {
    echo json_encode([
        'success' => false,
        'message' => 'No file uploaded or there was an error with the upload.'
    ]);
    exit;
}

// Define the upload directory
$upload_dir = __DIR__ . '/uploads/';
if (!is_dir($upload_dir)) {
    mkdir($upload_dir, 0777, true); // Create the directory with write permissions
}

// Get the destination path
$destination_path = $upload_dir . $_FILES['file']['name'];

// Move the uploaded file to the destination
if (!move_uploaded_file($_FILES['file']['tmp_name'], $destination_path)) {
    echo json_encode([
        'success' => false,
        'message' => 'Failed to save the uploaded file.'
    ]);
    exit;
}

// Command to execute the Python script with the uploaded file path
$command = escapeshellcmd("python distance.py " . escapeshellarg($destination_path));
$output = shell_exec($command);

if ($output === null) {
    // Handle Python script execution failure
    echo json_encode([
        'success' => false,
        'message' => 'Error executing Python script.'
    ]);
} else {
    // Output the JSON result from the Python script
    echo $output;
}
?>
