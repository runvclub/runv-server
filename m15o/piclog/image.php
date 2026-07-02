<?php
require 'includes/app.php';

function is_author($user, $image)
{
    return is_member($user) && $user['id'] == $image['user_id'];
}

$id = get_id();
$image = $App->getImage()->get($id);
?>

<?php include 'includes/header.php'; ?>
<header>
    <h1 class="title"><?= $image["filename"] ?></h1>
    <div class="meta">
        <a href="profile.php?id=<?= $image['user_id'] ?>"><?= $image['name'] ?></a>
        <time><?= timeAgo($image["published_at"]) ?></time>
    </div>
</header>

<img src="<?= file_path($image["user_id"], $image["filename"]) ?>"/>

<p class="description"><?= $image["description"] ?></p>

<?php if (is_author($user, $image) || is_admin($user)): ?>
    <nav>
        <a href="update.php?id=<?= $image["id"] ?>">edit</a> <a href="delete.php?id=<?= $image["id"] ?>">delete</a>
    </nav>
<?php endif; ?>

<?php include 'includes/footer.php'; ?>

