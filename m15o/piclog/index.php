<?php
require 'includes/app.php';

$page = get_page();
$res = $App->getImage()->getAll($page);
$images = $res['rows'];
$next_page = $res['next_page'];
?>

<?php include 'includes/header.php'; ?>
<h1>piclog</h1>
<?php if (is_visitor($user)): ?>
    <p class="is-visitor">You account is pending activation. You will be notified by email when activated.</p>
<?php endif ?>
<p>Hi! Here you can share your JPEG pictures with your friends. You can customize the CSS of your profile, and even add
    a little widget to your site! The pictures are heavily compressed to keep the file
    size small.</p>
<p class="rss"><a href="feed.php">Subscribe via RSS</a></p>

<?php foreach ($images as $image): ?>
    <article>
        <header>
            <h2 class="title"><a href="<?= image_path($image["id"]) ?>"><?= $image["filename"] ?></a></h2>
            <div class="meta">
                <a href="profile.php?id=<?= $image['user_id'] ?>" class="author"><?= $image['name'] ?></a>
                <time><?= timeAgo($image["published_at"]) ?></time>
            </div>
        </header>
        <img src="<?= file_path($image["user_id"], $image["filename"]) ?>"/>
        <p class=" description"><?= $image["description"] ?></p>
    </article>
<?php endforeach; ?>

<div class="pagination">
    <?php if ($next_page): ?>
        <a href="index.php?p=<?= $page + 1 ?>">Next page</a>
    <?php endif; ?>

    <?php if ($page > 1): ?>
        <a href="index.php?p=<?= $page - 1 ?>">Previous page</a>
    <?php endif; ?>
</div>

<?php include 'includes/footer.php'; ?>
