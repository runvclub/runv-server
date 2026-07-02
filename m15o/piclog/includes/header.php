<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>piclog</title>
    <link rel="stylesheet" href="style.css">
    <link type="application/atom+xml" rel="alternate" href="feed.php">
</head>
<body>
<header class="main-header">
    <a href="index.php"><img src="logo.png"></a>
    <nav>
        <a href="index.php">home</a>
        <?php if (is_member($user)): ?>
            <a href="upload.php">upload</a>
            <a href="widget.php">widget</a>
            <a href="profile.php?id=<?= $user['id'] ?>">profile</a>
        <?php endif; ?>
        <?php if ($user): ?>
            <a href="settings.php">settings</a>
            <a href="logout.php">logout</a>
            <?php if (is_admin($user)): ?>
                <a href="admin.php">admin</a>
            <?php endif; ?>
        <?php else: ?>
            <a href="register.php">register</a>
            <a href="login.php">login</a>
        <?php endif; ?>
    </nav>
</header>
<main>
    <?php if ($flash = $App->getSession()->getFlash()): ?>
    <p class="flash"><?= $flash ?></p>
<?php endif; ?>