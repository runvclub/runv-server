<?php
require 'includes/app.php';

$threads = $BBS->getThread()->getAll();

function url($thread)
{
    return thread_url($thread['id'], $thread['last_reply_id']);
}
?>

<?php include 'includes/header.php'; ?>

<h1><?=NAME?></h1>

<?php if ($user && is_member($user)): ?>
    <a href="thread_create.php">New thread</a>
<?php endif; ?>

<ul class="threads">
    <?php foreach($threads as $thread): ?>
				<li>
            <?php if ($thread['sticky']): ?><span>[sticky]</span><?php endif; ?>
            <a href="<?=url($thread)?>"><?=$thread['title']?></a>
				</li>
    <?php endforeach; ?>
</ul>

<?php include 'includes/footer.php'; ?>
