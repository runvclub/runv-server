<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title><?=NAME?></title>
        <link rel="stylesheet" href="style.css">
        <link type="application/atom+xml" rel="alternate" href="feed.php">
    </head>
    <body>
        <header>
            <a href="." class="logo"><?=NAME?></>
                <nav>
                    <a href="feed.php">feed</a>
                    <?php if ($user): ?>
                        <a href="account-update.php"><?=$user['name']?></a>
                        <a href="logout.php">logout</a>
												<?php if (is_admin($user)): ?>
														<a href="admin.php">admin</a>
												<?php endif; ?>
                    <?php else: ?>
                        <a href="register.php">register</a>
                        <a href="login.php">login</a>
                    <?php endif; ?>
                </nav>
        </header>
        <?php if (is_visitor($user)): ?>
            <div class="is-visitor">
                You account is pending activation. You will be notified by email when activated.
            </div>
        <?php endif ?>
        <?php if ($flash = $BBS->getSession()->getFlash()): ?>
            <p class="flash"><?=$flash?></p>
        <?php endif; ?>

        <main>
