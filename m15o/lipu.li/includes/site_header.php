<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title><?=$site_user['name']?> :: <?=$p??'home'?></title>
    <link rel="stylesheet" href="style.css">
    <link type="application/xml" rel="alternate" href="feed.php?u=<?=$site_user['name']?>">
    <style>
        <?=$site_user['style']?>
    </style>
</head>
<body>

<header>
    <nav>
        <?=site_link($site_user['name'], null, "Home")?>
        <a href="pages.php?u=<?=$site_user['name']?>">Pages</a>
        <a href="changelog.php?u=<?=$site_user['name']?>">Changelog</a>
    </nav>
</header>

<?php if ($flash = $App->getSession()->getFlash()): ?>
<p class="flash"><?= $flash ?></p>
<?php endif; ?>

