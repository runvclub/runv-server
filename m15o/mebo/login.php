<?php
require 'includes/app.php';

$errors = [];
$email = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $email    = $_POST['email'];
    $password = $_POST['password'];

    Validate::isEmail($email)       or $errors[] = "Wrong email";
    Validate::isPassword($password) or $errors[] = "Wrong password";

    if (!count($errors)) {
        if ($member = $BBS->getUser()->login($email, $password, $errors)) {
            $BBS->getSession()->login($member['id']);
            redirect('index.php');
        }
    }
}
?>
<?php include 'includes/header.php'; ?>

<h1>Login</h1>

<?php form_errors($errors) ?>

<form action="<?= $_SERVER['PHP_SELF'] ?>" method="post">
    <?php include 'includes/csrf.php' ?>
    <label for="form-name">Email:</label>
    <input type="email" name="email" value="<?=$email?>" class="form-control" />

    <label for="form-password">Password:</label>
    <input type="password" name="password" class="form-control" required/>

    <input type="submit" value="Login"/>
    <p><a href="password-lost.php">Password lost?</a></p>
</form>

<?php include 'includes/footer.php'; ?>
