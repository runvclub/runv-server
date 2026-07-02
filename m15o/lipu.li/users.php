<?php
require 'includes/app.php';

is_admin($User) or page_not_found();

$errors = [];

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $id = filter_input(INPUT_POST, 'id', FILTER_VALIDATE_INT) or page_not_found();
    $role = filter_input(INPUT_POST, 'role', FILTER_VALIDATE_INT);

    $selected = $GLOBALS['App']->getUser()->get($id);

    if (!$selected) {
        $errors[] = "Can't find user";
    } else {
        $App->getUser()->setRole($id, $role);
    }
}

$users = $GLOBALS['App']->getUser()->getAll();
?>

<?php include 'includes/header.php'; ?>

<h1>Roles</h1>

<?php form_errors($errors) ?>

<table>
    <?php foreach ($users as $user): ?>
        <?php if ($User['id'] !== $user['id']): ?>
            <tr>
                <form action="<?= $_SERVER['PHP_SELF'] ?>" method="post">
                    <?php include 'includes/csrf.php' ?>
                    <td><?= site_link($user['name']) ?></td>
                    <td>
                        <select name="role">
                            <option value="0" <?= ($user['role'] === 0) ? "selected" : "" ?>>suspended</option>
                            <option value="1" <?= ($user['role'] === 1) ? "selected" : "" ?>>unreviewed</option>
                            <option value="2" <?= ($user['role'] === 2) ? "selected" : "" ?>>reviewed</option>
                            <option value="3" <?= ($user['role'] === 3) ? "selected" : "" ?>>admin</option>
                        </select>
                        <input type="hidden" name="id" value="<?= $user['id'] ?>"/>
                        <input type="submit" value="save"/>
                    </td>
                    <td>
                        <a href="user_delete.php?u=<?= $user['name'] ?>">Delete</a>
                    </td>
                </form>
            </tr>
        <?php endif; ?>
    <?php endforeach; ?>
</table>

<?php include 'includes/footer.php'; ?>
