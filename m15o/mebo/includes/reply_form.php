<?php form_errors($errors) ?>

<form action="<?= $_SERVER['REQUEST_URI'] ?>" method="post">
    <?php include 'csrf.php' ?>

    <textarea id="reply" name="content" class="form-control" required><?=$form['content']?></textarea>

    <input type="submit" value="Reply"/>
</form>

