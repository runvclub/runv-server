<?php
require 'includes/app.php';

$user or redirect("login.php");

$errors = [];
$form = $user;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $form['name'] = $_POST['name'];
    $form['email'] = $_POST['email'];
    $form['cover'] = $_POST['cover'];

    Validate::isName($form['name']) or $errors[] = "Name must be 2-20 letters using [A-z0-9\_]";
    Validate::isEmail($form['email']) or $errors[] = "Email format not recognized";
    Validate::isAcceptableHTML($form['cover']) or $errors [] = "About has a forbidden HTML tag";
    !empty($form['cover']) or $errors[] = "Tell us a few words about you";

    if (!count($errors)) {
        if ($App->getUser()->update($form, $errors)) {
            $App->getSession()->setFlash("Settings updated");
        }
    }
}
?>

<?php include 'includes/header.php'; ?>
<h1>Settings</h1>

<?php form_errors($errors) ?>

<form action="<?= $_SERVER['PHP_SELF'] ?>" method="post">
    <?php include 'includes/csrf.php' ?>
    <div class="form-group">
        <label for="name">Name:</label>
        <input type="text" id="name" name="name" autocomplete="off" value="<?= $form['name'] ?>" class="form-control"
               required/>
    </div>

    <div class="form-group">
        <label for="email">Email:</label>
        <input type="email" id="email" name="email" autocomplete="off" value="<?= $form['email'] ?>"
               class="form-control" required/>
    </div>

    <label for="cover">About:</label>
    <textarea name="cover" id="cover" class="form-control" required"><?= $form['cover'] ?></textarea>

    <input type="submit" value="Update"/></td>
</form>

<p><a href="password-update.php">Update password</a></p>

<?php include 'includes/footer.php'; ?>
