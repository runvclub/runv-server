<?php
require 'includes/app.php';

is_member($User) or redirect("login.php");
$p = get_param("p");
$errors = [];
$site_user = $User;
$form = $App->getPage()->get($User['id'], $p) or page_not_found();

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $form['content'] = $_POST['content'];

    if (!count($errors)) {
        $App->getPage()->update($User['id'], $p, $form['content']);
    }
}
?>

<?php include 'includes/site_header.php'; ?>

<main>
    <h1>Editing <?= site_link($site_user['name'], $form['slug']) ?></h1>

    <?php form_errors($errors) ?>

    <form action="<?= $_SERVER['REQUEST_URI'] ?>" method="post" enctype="multipart/form-data">
        <?php include 'includes/csrf.php' ?>

        <textarea id="content" name="content" class="form-control" required><?= $form['content'] ?></textarea>

        <input type="submit" value="Submit"/>
    </form>

    <nav>
        <?= delete_link($p) ?>
    </nav>
</main>

<?php include 'includes/site_footer.php'; ?>
