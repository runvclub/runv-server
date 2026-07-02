<?php
require 'includes/app.php';

$id = get_id();
$page = get_page();
$profile = $App->getUser()->get($id) or page_not_found();
$res = $App->getImage()->getFromUser($id, $page);
$images = $res['rows'];
$next_page = $res['next_page'];
?>

<?php include 'includes/header.php'; ?>
<h1><?= $profile['name'] ?></h1>

<p class="about"><?= $profile['cover'] ?></p>
<p class="rss"><a href="user-feed.php?id=<?= $profile['id'] ?>">Subscribe via RSS</a></p>

<?php foreach ($images as $image): ?>
    <article>
        <header>
            <h2 class="title"><a href="<?= image_path($image["id"]) ?>"><?= $image["filename"] ?></a></h2>
            <div class="meta">
                <time><?= timeAgo($image["published_at"]) ?></time>
            </div>
        </header>

        <img src="<?= file_path($image["user_id"], $image["filename"]) ?>"/>
        <p class=" description"><?= $image["description"] ?></p>
    </article>
<?php endforeach; ?>

<div class="pagination">
    <?php if ($next_page): ?>
        <a href="profile.php?id=<?= $id ?>&p=<?= $page + 1 ?>">Next page</a>
    <?php endif; ?>

    <?php if ($page > 1): ?>
        <a href="profile.php?id=<?= $id ?>&p=<?= $page - 1 ?>">Previous page</a>
    <?php endif; ?>
</div>

<?php include 'includes/footer.php'; ?>

