<?php
require 'includes/app.php';

is_admin($User) or redirect("login.php");
?>

<?php include 'includes/header.php'; ?>

<h1>Admin</h1>

<ul>
    <li><a href="activate.php">Activate new users</a></li>
    <li><a href="users.php">Manage users</a>
</ul>

<?php include 'includes/footer.php'; ?>
