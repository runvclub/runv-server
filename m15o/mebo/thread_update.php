<?php
require 'includes/app.php';

is_member($user) or redirect("login.php");

$errors = [];
$form = $BBS->getThread()->get(get_id()) or page_not_found();

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $form['title']   = trim($_POST['title']);
    $form['content'] = trim($_POST['content']);
    $form['sticky'] = isset($_POST['sticky']) ? 1 : 0;

    Validate::isTitle($form['title']) or $errors[] = "Title must be 3 or more characters";
    !empty($form['content']) or $errors[] = "Content cannot be empty";

    if (!count($errors)) {
        if ($form['user_id'] === $user['id'] || is_admin($user)) {
            $BBS->getThread()->update($form['id'], $form['title'], $form['content'], $form['sticky']);
            redirect(thread_url($form['id']));
        }
    }
}
?>

<?php include 'includes/header.php'; ?>

<h1>Edit thread</h1>

<?php include 'includes/thread_form.php' ?>

<?php include 'includes/footer.php'; ?>
