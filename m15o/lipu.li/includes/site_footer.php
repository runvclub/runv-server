<?php if (is_site_admin($site_user)): ?>
    <footer>
        <nav>
            <a href="page_create.php">Add page</a>
            <a href="settings.php">Settings</a>
            <a href="manual.php">Manual</a>
            <a href="activity.php">Explore</a>
            <?php if (is_admin($User)): ?>
                <a href="admin.php">Admin</a>
            <?php endif; ?>
            <a href="logout.php">Logout</a>
        </nav>
    </footer>
<?php endif; ?>

</body>
</html>
