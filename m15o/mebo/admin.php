<?php
require 'includes/app.php';

is_admin($user) or redirect("login.php");
?>

<?php include 'includes/header.php'; ?>

<h1>Admin</h1>

<ul>
		<li><a href="activate.php">Activate new users</a></li>
		<li><a href="role.php">Manage user roles</a>
</ul>

<?php include 'includes/footer.php'; ?>
