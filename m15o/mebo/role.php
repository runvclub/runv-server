<?php
require 'includes/app.php';

is_admin($user) or redirect("login.php");

$errors = [];

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $id = filter_input(INPUT_POST, 'id', FILTER_VALIDATE_INT) or page_not_found();
    $role = filter_input(INPUT_POST, 'role', FILTER_VALIDATE_INT);

    $selected = $BBS->getUser()->get($id);

    if (!$selected) {
        $errors[] = "Can't find user";
    } else {
        $BBS->getUser()->setRole($id, $role);
    }
}

$users = $BBS->getUser()->getAll();
?>

<?php include 'includes/header.php'; ?>

<h1>Roles</h1>

<?php form_errors($errors) ?>

<table>
    <?php foreach ($users as $user): ?>
        <tr>
						<form action="<?=$_SERVER['PHP_SELF']?>" method="post">
                <?php include 'includes/csrf.php' ?>
								<td><?=$user['name']?></td>
								<td>
                    <select name="role">
                        <option value="0" <?= ($user['role'] === 0) ? "selected" : "" ?>>suspended</option>
                        <option value="1" <?= ($user['role'] === 1) ? "selected" : "" ?>>visitor</option>
                        <option value="2" <?= ($user['role'] === 2) ? "selected" : "" ?>>member</option>
                        <option value="3" <?= ($user['role'] === 3) ? "selected" : "" ?>>admin</option>
                    </select>
                    <input type="hidden" name="id" value="<?=$user['id']?>" />
                    <input type="submit" value="save"/>

								</td>
						</form>
        </tr>
    <?php endforeach; ?>
</table>

<?php include 'includes/footer.php'; ?>
