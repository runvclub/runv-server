<?php
require 'includes/app.php';

header('Content-Type: application/xml');
$threads = $BBS->getThread()->getAll();

function url($thread)
{
    $url = "thread_read.php?id=$thread[id]";

    if (isset($thread['last_reply_id'])) {
        $url .= "#$thread[last_reply_id]";
    }

    return $url;
}
?>
<rss version="2.0">
    <channel>
        <title><?=NAME?></title>
        <link><?=URL?></link>
        <?php foreach($threads as $thread): ?>
            <item>
                <title><?=$thread['title']?></title>
                <pubDate><?=date(DATE_RSS, strtotime($thread['updated_at']))?></pubDate>
                <link><?=URL . '/' . url($thread)?></link>
            </item>
        <?php endforeach; ?>
    </channel>
</rss>
