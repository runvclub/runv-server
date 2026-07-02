<?php
require 'includes/app.php';

is_admin($User) or redirect("login.php");

$errors = [];

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $id = filter_input(INPUT_POST, 'id', FILTER_VALIDATE_INT) or page_not_found();

    $selected = $GLOBALS['App']->getUser()->get($id);

    if (!$selected) {
        $errors[] = "Can't find user";
    } else {
        $App->getUser()->setRole($id, 2);
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
            <td><?=site_link($user['name'])?></td>
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
