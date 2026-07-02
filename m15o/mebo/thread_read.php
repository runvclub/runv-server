<?php
require 'includes/app.php';

$id = get_id();
$errors = [];
$form = [
    "thread_id" => $id,
    "content" => '',
];

function is_author($user, $thread)
{
    return is_member($user) && $user['id'] == $thread['user_id'];
}

if ($_SERVER['REQUEST_METHOD'] == 'POST') {
    $form['content'] = trim($_POST['content']);
    $form['user_id'] = $user['id'];

    !empty($form['content']) or $errors[] = $dict['form.error.reply'];

    if (!count($errors)) {
        $reply_id = $BBS->getReply()->create($form);
        redirect(thread_url($id, $reply_id));
    }
}
$thread  = $BBS->getThread()->get($id) or page_not_found();
$replies = $BBS->getReply()->getAll($id);
?>

<?php include 'includes/header.php'; ?>

<h1><?=htmlspecialchars($thread['title'])?></h1>
<article>
    <header>
        <?=get_name($thread)?>
        <a href=""><time><?=to_date($thread['published_at']) ?></time></a>
        <?php if (is_author($user, $thread) || is_admin($user)): ?>
            <a href="thread_update.php?id=<?=$thread['id']?>">edit</a>
            <a href="thread_delete.php?id=<?=$thread['id']?>">delete</a>
        <?php endif; ?>
    </header>
    <div class="text"><?=text($thread['content'])?></div>
</article>

<?php foreach($replies as $reply): ?>
    <article id="<?= $reply['id']?>">
        <header>
            <?=get_name($reply)?>
            <a href="#<?=$reply['id'] ?>"><time><?=to_date($reply['published_at']) ?></time></a>
            <?php if (is_author($user, $reply) || is_admin($user)): ?>
                <a href="reply_update.php?id=<?=$reply['id']?>">edit</a>
                <a href="reply_delete.php?id=<?=$reply['id']?>">delete</a>
            <?php endif; ?>
        </header>
        <div class="text"><?=text($reply['content'])?></div>
    </article>
<?php endforeach; ?>

<?php if(is_member($user)): ?>
    <?php require 'includes/reply_form.php'; ?>
<?php endif; ?>

<?php include 'includes/footer.php'; ?>
