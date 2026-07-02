<?php include 'header.php'; ?>

<main>
    <h1>Your personal wiki</h1>

    <p>
        lipu li is a little wiki engine that lets you manage your pages online. When a page references another page,
        lipu li generates a backlink.
    </p>

    <?php include 'login_form.php' ?>

    <p>
        <a href="manual.php" class="link">Manual</a><br>
        <a href="activity.php" class="link">Explore</a><br>
        <a href="https://hg.sr.ht/~m15o/lipu.li" class="link">Source</a>
    </p>
</main>

<?php include 'footer.php'; ?>
