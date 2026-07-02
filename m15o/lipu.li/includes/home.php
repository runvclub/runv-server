<?php include 'site_header.php'; ?>

<main>
<?php if ($content): ?>
    <?= $content ?>
<?php else: ?>
    <h1><?= $site_user['name'] ?>'s site</h1>
    <p>Welcome to your site! Use the edit button to edit this page.</p>
<?php endif; ?>
<?php if ($is_admin): ?>
    <nav class="page-admin">
        <a href="home_update.php">Edit</a>
    </nav>
<?php endif; ?>
</main>

<?php include 'site_footer.php'; ?>