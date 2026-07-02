<?php

require 'includes/app.php';

$errors = [];

$title = NAME . ' - Recover password';

function get_body($token)
{
    return "Use this link: " . URL . "/password-reset.php?t=$token";
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $email = $_POST['email'];
    Validate::isEmail($email) or $errors[] = "Please provide a valide email address";

    if (!count($errors)) {
        $id = $BBS->getUser()->getIdFromEmail($email);
        if ($id) {
            $token = $BBS->getToken()->create($id);
            $BBS->getEmail()->send($email, $title, get_body($token));
        }
        $BBS->getSession()->setFlash("If your email is registered, we will send an email with instructions.");
    }
}
?>
<?php include 'includes/header.php'; ?>
<h1>Password lost</h1>

<?php form_errors($errors) ?>

<form action="<?= $_SERVER['PHP_SELF'] ?>" method="post">
    <?php include 'includes/csrf.php' ?>

    <label for="email">Email:</label>
    <input type="email" id="email" name="email" class="form-control" required/>

    <input type="submit" value="Submit"/>
</form>

<?php include 'includes/footer.php'; ?>
