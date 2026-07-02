<?php
require 'includes/app.php';

is_member($user) or redirect("login.php");

$errors = [];
$form = $user;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $form['name']  = $_POST['name'];
    $form['email'] = $_POST['email'];

    Validate::isName($form['name'])   or $errors[] = "Name must be 2-20 letters using [A-z0-9\_]";
    Validate::isEmail($form['email']) or $errors[] = "Email format not recognized";

    if (!count($errors)) {
        if ($BBS->getUser()->update($form, $errors)) {
            $BBS->getSession()->setFlash("Account updated");
        }
    }
}
?>

<?php include 'includes/header.php'; ?>
<h1>Edit account</h1>

<?php form_errors($errors) ?>

<form action="<?= $_SERVER['PHP_SELF'] ?>" method="post">
    <?php include 'includes/csrf.php' ?>
    <div class="form-group">
        <label for="name">Name:</label>
        <input type="text" id="name" name="name" autocomplete="off" value="<?=$form['name']?>" class="form-control" required/>
    </div>

    <div class="form-group">
        <label for="email">Email:</label>
        <input type="email" id="email" name="email" autocomplete="off" value="<?=$form['email']?>" class="form-control" required/>
    </div>

    <input type="submit" value="Update"/></td>
    <p><a href="password-update.php">Update password</a></p>
</form>

<?php include 'includes/footer.php'; ?>
