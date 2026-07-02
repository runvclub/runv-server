<?php
require 'includes/app.php';

header('Content-Type: application/xml');
$id = get_id();
$profile = $App->getUser()->get($id) or page_not_found();
$images = $App->getImage()->getFromUser($id, 1);
?>
    <rss version="2.0">
        <channel>
            <title><?= $profile['name'] ?></title>
            <description>piclog feed</description>
            <link><?= URL . '/profile.php?id=' . $profile['id'] ?></link>
            <?php foreach ($images as $image): ?>
                <item>
                    <title><?= $image['filename'] ?></title>
                    <pubDate><?= date(DATE_RSS, strtotime($image['published_at'])) ?></pubDate>
                    <guid><?= URL . '/image.php?id=' . $image['id'] ?></guid>
                    <link><?= URL . '/image.php?id=' . $image['id'] ?></link>
                </item>
            <?php endforeach; ?>
        </channel>
    </rss>
<?php
