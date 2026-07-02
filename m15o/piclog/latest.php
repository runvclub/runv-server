<?php
include 'includes/app.php';

$id = get_id();
$images = $App->getImage()->getFromUser($id, 1);
if (!count($images)) {
    http_response_code(404);
    exit;
}
$filename = file_path($id, $images['rows'][0]['filename']);

header("Content-Type: image/jpeg");
header("Content-Length: " . filesize($filename));

$fp = fopen($filename, 'rb');

fpassthru($fp);
