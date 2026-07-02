<?php
require 'includes/app.php';

$errors = [];
$form = [
    'name' => '',
    'email' => '',
    'key' => '',
];

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $form['name'] = $_POST['name'];
    $form['email'] = $_POST['email'];
    $form['key'] = $_POST['key'];
    $password = $_POST['password'];

    Validate::isName($form['name']) or $errors[] = "Name must be 2-20 letters using [A-z0-9\_]";
    Validate::isEmail($form['email']) or $errors[] = "Email format not recognized";
    Validate::isPassword($password) or $errors[] = "Password must be 6 or more characters";
    $form['key'] === KEY or $errors[] = "Invalid key";

    if ($password != $_POST['repeat']) {
        $errors[] = "Passwords don't match";
    }

    if (!count($errors)) {
        $id = $App->getUser()->create([
            "name" => $form['name'],
            "email" => $form['email'],
            "password" => $password,
        ], $errors);
        if ($id !== false) {
            $App->getSession()->login($id, true);
            redirect("index.php");
        }
    }
}
?>

<?php include 'includes/header.php'; ?>

<main>
    <h1>Register</h1>

    <?php form_errors($errors ?? '') ?>

    <form action="<?= $_SERVER['PHP_SELF'] ?>" method="post">
        <?php include 'includes/csrf.php' ?>
        <label for="name">Name:</label>
        <input type="text" id="name" name="name" autocomplete="off" value="<?= $form['name'] ?>" class="form-control"
               required/>

        <label for="email">Email (used to reset password):</label>
        <input type="email" id="email" name="email" autocomplete="off" value="<?= $form['email'] ?>"
               class="form-control"
               required/>

        <label for="password">Password:</label>
        <input type="password" id="password" name="password" class="form-control" required/>

        <label for="repeat">Repeat:</label>
        <input type="password" id="repeat" name="repeat" class="form-control" required/>

        <p><a target="_blank" href="<?= KEY_BUY_URL ?>">Buy a key</a> for instant access or <a href="<?= KEY_REQUEST_FORM_URL ?>">request a free key</a>.</p>

        <label for="name">Key:</label>
        <input type="text" id="key" name="key" autocomplete="off" value="<?= $form['key'] ?>" class="form-control"
               required/>

        <p>By clicking the following button you agree to the <a target="_blank" href="tos.php">terms of Service</a>.</p>
        <input type="submit" value="Register"/>
    </form>
</main>

<?php include 'includes/footer.php'; ?>
