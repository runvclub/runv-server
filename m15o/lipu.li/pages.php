<?php
require 'includes/app.php';

$u = get_param("u");
$pages = $App->getPage()->getAll($u);
$site_user = $App->getUser()->getFromUsername($u) or page_not_found();
?>

<?php include 'includes/site_header.php'; ?>

<main>
    <h1>Pages</h1>

    <ul>
        <?php foreach ($pages as $page): ?>
            <li><?= site_link($site_user['name'], $page['slug']) ?></li>
        <?php endforeach; ?>
    </ul>

</main>

<?php include 'includes/site_footer.php'; ?>
