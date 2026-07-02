<?php
require 'includes/app.php';

is_member($user) or redirect("login.php");

$errors = [];
$form = $App->getImage()->get(get_id()) or page_not_found();

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if ($form['user_id'] === $user['id'] || is_admin($user)) {
        $form['description'] = $_POST['description'];
        Validate::isFilename($_POST['filename']) or $errors [] = 'Wrong file name';
        if ($form['filename'] !== $_POST['filename']) {
            Validate::isAvailableFilename($user['id'], $_POST['filename']) or $errors [] = 'File already exists';
        }
        Validate::isAcceptableHTML($form['description']) or $errors [] = "Description has a forbidden HTML tag";

        if (!count($errors)) {
            $App->getImage()->update($form['id'], $form['user_id'], $form['filename'], $_POST['filename'], $form['description']);
            $App->getSession()->setFlash("Image updated");
            redirect("index.php");
        }
    }
}
?>

<?php include 'includes/header.php'; ?>

    <h1>Update image</h1>
<?= form_errors($errors) ?>
    <form action="<?= $_SERVER['REQUEST_URI'] ?>" method="post" enctype="multipart/form-data">
        <?php include 'includes/csrf.php' ?>
        <label for="name">Filename:</label>
        <input type="text" id="filename" name="filename" autocomplete="off" value="<?= $form['filename'] ?>"
               class="form-control" required/>

        <label for="description">Description:</label>
        <textarea name="description" id="description" class="form-control"
                  required"><?= $form['description'] ?></textarea>

        <input type="submit" value="Submit"/>
    </form>

<?php include 'includes/footer.php'; ?>