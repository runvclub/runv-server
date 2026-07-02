<?php
require 'includes/app.php';

$User or redirect("login.php");
$site_user = $User;
$errors = [];
$form = $User;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $form['name'] = $_POST['name'];
    $form['email'] = $_POST['email'];
    $form['style'] = $_POST['style'];

    Validate::isName($form['name']) or $errors[] = "Name must be 2-20 letters using [A-z0-9\_]";
    Validate::isEmail($form['email']) or $errors[] = "Email format not recognized";
    Validate::isAcceptableHTML($form['style']) or $errors [] = "Style has a forbidden HTML tag";

    if (!count($errors)) {
        if ($App->getUser()->update($form, $errors)) {
            $App->getSession()->setFlash("Settings updated");
            $site_user['style'] = $form['style'];
        }
    }
}
?>

<?php include 'includes/site_header.php'; ?>

<main>
    <h1>Settings</h1>

    <?php form_errors($errors) ?>

    <form action="<?= $_SERVER['PHP_SELF'] ?>" method="post">
        <?php include 'includes/csrf.php' ?>
        <div class="form-group">
            <label for="name">Name:</label>
            <input type="text" id="name" name="name" autocomplete="off" value="<?= $form['name'] ?>"
                   class="form-control"
                   required/>
        </div>

        <div class="form-group">
            <label for="email">Email:</label>
            <input type="email" id="email" name="email" autocomplete="off" value="<?= $form['email'] ?>"
                   class="form-control" required/>
        </div>

        <label for="style">Style:</label>
        <textarea name="style" id="style" class="form-control" required"><?= $form['style'] ?></textarea>

        <input type="submit" value="Update"/></td>
    </form>

    <p><a href="password-update.php">Update password</a></p>
</main>

<?php include 'includes/site_footer.php'; ?>
