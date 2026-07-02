<?php
require 'includes/app.php';

is_member($GLOBALS['User']) or redirect("login.php");
$site_user = $User;
$errors = [];
$form = [
    "name" => '',
    "content" => ''
];

if ($_SERVER['REQUEST_METHOD'] == 'POST') {
    $form['name'] = $_POST['name'];

    $name = trim($form['name']);

    // todo: more validation
    Validate::isPage($name) or $errors[] = "Slug can only contain a-z0-9_-";

    if (!count($errors)) {
        $id = $App->getPage()->create($User['id'], $name, '');
        redirect("page_update.php?p=$name");
    }
}
?>

<?php include 'includes/site_header.php'; ?>

<main>
    <h1>Add page</h1>

    <?php form_errors($errors) ?>

    <form action="<?= $_SERVER['PHP_SELF'] ?>" method="post" enctype="multipart/form-data">
        <?php include 'includes/csrf.php' ?>

        <label for="title">Slug (can only contain lowercase letters, numbers, and -):</label>
        <input id="title" type="text" name="name" autocomplete="off" value="<?= $form['name'] ?>" required
               class="form-control"/>

        <input type="submit" value="Submit"/>
    </form>
</main>

<?php include 'includes/site_footer.php'; ?>
