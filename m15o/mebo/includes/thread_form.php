<?php form_errors($errors) ?>

<form action="<?= $_SERVER['REQUEST_URI'] ?>" method="post">
    <?php include 'csrf.php' ?>

    <label for="title">Title:</label>
    <input id="title" type="text" name="title" autocomplete="off" value="<?=$form['title']?>" required class="form-control" />

    <label for="content">Content:</label>
    <textarea id="content" name="content" class="form-control" required><?=$form['content']?></textarea>

    <?php if (is_admin($user)): ?>
				<div>
						<input type="checkbox" id="sticky" name="sticky" <?=$form['sticky'] ? 'checked' : ''?>>
						<label for="sticky">Sticky</label>
				</div>
    <?php endif; ?>

    <input type="submit" value="Publish"/>
</form>
