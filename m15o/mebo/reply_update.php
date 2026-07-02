<?php
require 'includes/app.php';

is_member($user) or redirect("login.php");

$errors = [];
$form = $BBS->getReply()->get(get_id()) or page_not_found();

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $form['content'] = $_POST['content'];
    $content = trim($form['content']);

    !empty($content) or $errors[] = "Reply can't be empty";

    if (!count($errors)) {
        if ($form['user_id'] === $user['id'] || is_admin($user)) {
            $BBS->getReply()->update($form['id'], $content);
            $BBS->getSession()->setFlash("Reply updated!");
            redirect(thread_url($form['thread_id']));
        }
    }
}
?>

<?php include 'includes/header.php'; ?>

<h1>Edit reply</h1>

<?php require 'includes/reply_form.php'; ?>

<?php include 'includes/footer.php'; ?>
