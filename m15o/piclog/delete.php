<?php
require 'includes/app.php';

is_member($user) or redirect("login.php");

$errors = [];
$form = $App->getImage()->get(get_id()) or page_not_found();

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if ($form['user_id'] === $user['id'] || is_admin($user)) {
        if ($App->getImage()->delete($form['id'], $form['user_id'])) {
            $App->getSession()->setFlash("Image deleted");
            redirect("index.php");
        } else {
            $errors[]="Can't delete image";
        }
    } else {
        page_not_found();
    }
}
?>

<?php include 'includes/header.php'; ?>

<h1>Delete image</h1>

<?php form_errors($errors) ?>

<p>Are you sure you want to delete "<?=htmlspecialchars($form['filename'])?>"?</p>

<form action="<?= $_SERVER['REQUEST_URI'] ?>" method="post" class="editor">
    <?php include 'includes/csrf.php' ?>
    <p><input type="submit" value="Confirm"/></p>
</form>

<?php include 'includes/footer.php'; ?>
