<?php
require 'includes/app.php';

is_member($user) or redirect("login.php");

$errors = [];
$reply = $BBS->getReply()->get(get_id()) or page_not_found();

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if ($reply['user_id'] === $user['id'] || is_admin($user)) {
        $BBS->getReply()->delete($reply['id'], $user['id']);
        $BBS->getSession()->setFlash("Reply deleted");
        redirect(thread_url($reply['thread_id']));
    }
}
?>

<?php include 'includes/header.php'; ?>

<h1>Delete reply</h1>

<?php form_errors($errors) ?>

<p>Are you sure you want to delete your reply?</p>

<form action="<?= $_SERVER['REQUEST_URI'] ?>" method="post" class="editor">
    <?php include 'includes/csrf.php' ?>
    <p><input type="submit" value="Confirm"/></p>
</form>

<?php include 'includes/footer.php'; ?>
