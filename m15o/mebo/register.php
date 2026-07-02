<?php
require 'includes/app.php';

$errors = [];
$form = [
    'name'  => '',
    'email' => '',
    'cover' => '',
];

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $form['name']  = $_POST['name'];
    $form['email'] = $_POST['email'];
    $form['cover'] = trim($_POST['cover']);
    $password      = $_POST['password'];

    Validate::isName($form['name'])   or $errors[] = "Name must be 2-20 letters using [A-z0-9\_]";
    Validate::isEmail($form['email']) or $errors[] = "Email format not recognized";
    Validate::isPassword($password)   or $errors[] = "Password must be 6 or more characters";
    !empty($form['cover'])   or $errors[] = "Tell us a few words about you";

    if ($password != $_POST['repeat']) {
        $errors[] = "Passwords don't match";
    }

    if (!count($errors)) {
        $id = $BBS->getUser()->create([
            "name"     => $form['name'],
            "email"    => $form['email'],
            "cover"    => $form['cover'],
            "password" => $password,
        ], $errors);
        if ($id !== false) {
            $BBS->getSession()->login($id);
            $BBS->getSession()->setFlash("Thanks for registering! You will be able to start posting as soon as your account gets activated!");
            redirect("index.php");
        }
    }
}
?>

<?php include 'includes/header.php'; ?>
<h1>Register</h1>

<?php form_errors($errors ?? '') ?>

<form action="<?= $_SERVER['PHP_SELF'] ?>" method="post">
    <?php include 'includes/csrf.php' ?>
    <label for="name">Name:</label>
    <input type="text" id="name" name="name" autocomplete="off" value="<?=$form['name']?>" class="form-control" required/>

    <label for="email">Email:</label>
    <input type="email" id="email" name="email" autocomplete="off" value="<?=$form['email']?>" class="form-control" required/>

    <label for="password">Password:</label>
    <input type="password" id="password" name="password" class="form-control" required/>

    <label for="repeat">Repeat:</label>
    <input type="password" id="repeat" name="repeat" class="form-control" required/>

    <label for="cover">About:</label>
    <textarea name="cover" id="cover" class="form-control" required"><?=$form['cover']?></textarea>

    <input type="submit" value="Register"/>
</form>

<?php include 'includes/footer.php'; ?>
