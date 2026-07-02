<?php
require 'includes/app.php';

$errors = [];
$email = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $email    = $_POST['email'];
    $password = $_POST['password'];
    $remember = $_POST['remember'] ?? false;

    Validate::isEmail($email)       or $errors[] = "Wrong email";
    Validate::isPassword($password) or $errors[] = "Wrong password";

    if (!count($errors)) {
        if ($member = $App->getUser()->login($email, $password, $errors)) {
            $App->getSession()->login($member['id'], $remember);
            redirect('index.php');
        }
    }
}
?>
<?php include 'includes/header.php'; ?>

<h1>Login</h1>

<?php form_errors($errors) ?>

<?php include 'includes/login_form.php' ?>

<?php include 'includes/footer.php'; ?>
