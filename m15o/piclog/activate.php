<?php
require 'includes/app.php';

is_admin($user) or redirect("login.php");

$errors = [];

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $id = filter_input(INPUT_POST, 'id', FILTER_VALIDATE_INT) or page_not_found();

    $selected = $App->getUser()->get($id);

    if (!$selected) {
        $errors[] = "Can't find user";
    } else {
        if ($App->getUser()->setRole($id, 2)) {
            $subject = "piclog - Welcome!";
            $message = "Hello $selected[name]! Your account has been activated. You can now post messages on " . URL . ".\n\nTalk to you soon!";
            $App->getEmail()->send($selected['email'], $subject, $message);
        }
    }
}

$users = $App->getUser()->getAllInactive();
?>

<?php include 'includes/header.php'; ?>

<h1>Activate</h1>

<?php form_errors($errors) ?>

<table>
    <?php foreach ($users as $user): ?>
        <tr>
            <td><?= $user['name'] ?></td>
            <td><?= $user['cover'] ?></td>
            <td>
                <form action="<?= $_SERVER['PHP_SELF'] ?>" method="post">
                    <?php include 'includes/csrf.php' ?>
                    <input type="hidden" name="id" value="<?= $user['id'] ?>"/>
                    <input type="submit" value="activate"/>
                </form>
            </td>
        </tr>
    <?php endforeach; ?>
</table>

<?php include 'includes/footer.php'; ?>
