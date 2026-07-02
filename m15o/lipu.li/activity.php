<?php
require 'includes/app.php';
$pages = $App->getPage()->getActivity();
?>

<?php include 'includes/header.php'; ?>

<main>
    <h1>Activity</h1>

    <p><a href="feed.php">Subscribe via RSS</a></p>

    <ul>
        <?php foreach ($pages as $page): ?>
            <li>
                <time><?= to_date($page['updated_at']) ?></time>
                <?= site_link($page['name']) ?> - <?= site_link($page['name'], $page['slug']) ?>
            </li>
        <?php endforeach; ?>
    </ul>
</main>
