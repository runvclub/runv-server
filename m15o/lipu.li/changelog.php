<?php
require 'includes/app.php';

$u = get_param("u");
$pages = $App->getPage()->getChangelog($u);
$site_user = $App->getUser()->getFromUsername($u) or page_not_found();
?>

<?php include 'includes/site_header.php'; ?>

<main>
    <h1>Changelog</h1>

    <p><a href="feed.php?u=<?=$site_user['name']?>">Subscribe via RSS</a></p>

    <ul>
        <?php foreach ($pages as $page): ?>
            <li><time><?=to_date($page['updated_at'])?></time> <?=site_link($page['name'], $page['slug'])?></li>
        <?php endforeach; ?>
    </ul>

</main>

<?php include 'includes/site_footer.php'; ?>
