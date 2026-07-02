<?php
require 'includes/app.php';

is_member($user) or redirect("login.php");

$errors = [];

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $password = $_POST['password'];
    $repeat   = $_POST['repeat'];

    Validate::isPassword($password) or $errors[] = "Password must be 6 or more characters";

    if ($password != $repeat) {
        $errors[] = "Passwords don't match";
    }

    if (!count($errors)) {
        $App->getUser()->updatePassword($user['id'], $password);
        $App->getSession()->setFlash("Password updated");
    }
}
?>

<?php include 'includes/header.php'; ?>
<h1>Edit password</h1>

<?php form_errors($errors) ?>

<form action="<?= $_SERVER['PHP_SELF'] ?>" method="post">
    <?php include 'includes/csrf.php' ?>

		<label for="password">New password:</label>
    <input type="password" id="password" name="password" class="form-control"required/>

    <label for="repeat">Repeat:</label>
    <input type="password" id="repeat" name="repeat" class="form-control" required/>

    <input type="submit" value="Update"/>
</form>

<?php include 'includes/footer.php'; ?>
