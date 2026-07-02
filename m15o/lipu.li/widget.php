<?php
require 'includes/app.php';
?>

<?php include 'includes/header.php'; ?>
<h1>Widget</h1>
<p>Add the following snippet to your site to show your latest picture. Feel free to customize how it looks like!</p>
<textarea
        style="width: 100%;"><a href="<?= URL ?>/profile.php?id=<?= $User['id']; ?>"><img src="<?= URL ?>/latest.php?id=<?= $User['id']; ?>"></a></textarea>
<p><a href="<?= URL ?>/profile.php?id=<?= $User['id']; ?>"><img src="<?= URL ?>/latest.php?id=<?= $User['id']; ?>"></a>
</p>

<?php include 'includes/footer.php'; ?>
