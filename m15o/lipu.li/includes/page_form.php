<?php form_errors($errors) ?>

<form action="<?= $_SERVER['PHP_SELF'] ?>" method="post" enctype="multipart/form-data">
    <?php include 'includes/csrf.php' ?>

    <label for="title">Title:</label>
    <input id="title" type="text" name="name" autocomplete="off" value="<?= $form['name'] ?>" required
           class="form-control"/>

    <label for="content">Content:</label>
    <textarea id="content" name="content" class="form-control" required><?= $form['content'] ?></textarea>

    <input type="submit" value="Submit"/>
</form>