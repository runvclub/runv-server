<?php
require 'includes/app.php';

header('Content-Type: application/xml');
$res = $App->getImage()->getAll(1);
$images = $res['rows'];
?>
<rss version="2.0">
    <channel>
        <title>piclog</title>
        <description>A little place to upload and share your pictures.</description>
        <link><?= URL ?></link>
        <?php foreach ($images as $image): ?>
            <item>
                <title><?= $image['name'] ?> uploaded <?= $image['filename'] ?></title>
                <pubDate><?= date(DATE_RSS, strtotime($image['published_at'])) ?></pubDate>
                <guid><?= URL . '/image.php?id=' . $image['id'] ?></guid>
                <link><?= URL . '/image.php?id=' . $image['id'] ?></link>
            </item>
        <?php endforeach; ?>
    </channel>
</rss>
