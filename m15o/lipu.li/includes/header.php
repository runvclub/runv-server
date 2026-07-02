<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>lipu li</title>
    <link rel="stylesheet" href="style.css">
    <link type="application/atom+xml" rel="alternate" href="feed.php">
</head>
<body>

<?php if ($flash = $App->getSession()->getFlash()): ?>
<p class="flash"><?= $flash ?></p>
<?php endif; ?>