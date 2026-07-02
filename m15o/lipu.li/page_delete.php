<?php
require 'includes/app.php';

is_member($User) or redirect("login.php");
$p = get_param("p");
$site_user = $User;
$errors = [];
$form = $App->getPage()->get($User['id'], $p) or page_not_found();

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $App->getPage()->delete($User['id'], $p);
    $App->getSession()->setFlash("Page deleted");
    redirect("index.php");
}
?>

<?php include 'includes/site_header.php'; ?>

<main>
    <h1>Delete page</h1>

    <?php form_errors($errors) ?>

    <p>Are you sure you want to delete "<?= htmlspecialchars($form['slug']) ?>"?</p>

    <form action="<?= $_SERVER['REQUEST_URI'] ?>" method="post">
        <?php include 'includes/csrf.php' ?>
        <input type="submit" value="Confirm"/>
    </form>
</main>

<?php include 'includes/site_footer.php'; ?>
