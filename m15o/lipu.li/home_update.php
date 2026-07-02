<?php
require 'includes/app.php';

is_member($GLOBALS['User']) or redirect("login.php");
$site_user = $GLOBALS['User'];
$pages = $GLOBALS['App']->getPage()->getAll($GLOBALS['User']['id']);
$errors = [];
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $GLOBALS['User']['home'] = $_POST['home'];

    // todo validation

    $GLOBALS['App']->getUser()->update($GLOBALS['User'], $errors);
}
?>
<?php include 'includes/site_header.php'; ?>

<main>
    <h1>Editing <?=site_link($site_user['name'], null, "home")?></h1>
    <?php form_errors($errors) ?>

    <form action="<?= $_SERVER['REQUEST_URI'] ?>" method="post" enctype="multipart/form-data">
        <?php include 'includes/csrf.php' ?>

        <textarea id="home" name="home" class="form-control" required><?= $GLOBALS['User']['home'] ?></textarea>

        <input type="submit" value="Submit"/>
    </form>

</main>

<?php include 'includes/site_footer.php'; ?>

