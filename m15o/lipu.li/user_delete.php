<?php
require 'includes/app.php';

is_admin($User) or page_not_found();

$u = get_param('u');
$user = $App->getUser()->getFromUsername($u) or page_not_found();

$errors = [];

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $App->getUser()->deleteUser($user['name']);
    redirect("users.php");
}

?>

<?php include 'includes/header.php'; ?>

<h1>Delete user</h1>

<?php form_errors($errors) ?>

<p>Are you sure you want to delete <?=$user['name']?>?</p>

<form action="<?= $_SERVER['REQUEST_URI'] ?>" method="post">
    <?php include 'includes/csrf.php' ?>
    <input type="submit" value="Confirm"/>
</form>

<?php include 'includes/footer.php'; ?>
