<?php include 'site_header.php'; ?>

<main>
    <?php if ($page): ?>
        <?= $content ?>
    <?php else: ?>
        <h1>Not found</h1>
        <?php if ($is_admin): ?>
            <p>Create page for <?= $p ?>?</p>
            <form action="page_create.php" method="post" enctype="multipart/form-data">
                <?php include 'includes/csrf.php' ?>

                <input id="title" type="hidden" name="name" autocomplete="off" value="<?= $p ?>"
                       class="form-control"/>

                <input type="submit" value="Create"/>
            </form>
        <?php endif; ?>
    <?php endif; ?>

    <?php if (count($related)): ?>
        <nav>
            <span>backlinks: </span>
            <?php foreach ($related as $r): ?>
                <?= site_link($site_user['name'], $r['slug']) ?>
            <?php endforeach; ?>
        </nav>
    <?php endif; ?>

    <?php if ($page && $is_admin): ?>
        <nav>
            <?= edit_link($p) ?>
            <?= delete_link($p) ?>
        </nav>
    <?php endif; ?>
</main>

<?php include 'site_footer.php'; ?>
