<?php
require 'includes/app.php';

is_member($user) or redirect("login.php");

$errors = [];
$form = [
    "title" => '',
    "content" => '',
    "sticky" => false,
];

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $form['title']  = $_POST['title'];
    $form['content'] = $_POST['content'];
    $form['sticky'] = isset($_POST['sticky']) ? 1 : 0;

    $title = trim($form['title']);
    $content = trim($form['content']);

    Validate::isTitle($title) or $errors[] = "Title must be 3 or more characters";
    !empty($content) or $errors[] = "Content cannot be empty";

    if (!count($errors)) {
        $id = $BBS->getThread()->create([
                        "title" => $title,
                        "content" => $content,
                        "user_id" => $user['id'],
                        "sticky" => $form['sticky']
                ]);
        redirect(thread_url($id));
    }
}
?>

<?php include 'includes/header.php'; ?>

<h1>New thread</h1>

<?php include 'includes/thread_form.php' ?>

<?php include 'includes/footer.php'; ?>
