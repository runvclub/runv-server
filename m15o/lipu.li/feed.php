<?php
require 'includes/app.php';

$name = "lipu.li";
$description = "Updates";
$link = URL;

if ($u = get_param("u")) {
    $site_user = $App->getUser()->getFromUsername($u) or page_not_found();
    $name = $site_user['name'];
    $description = $name . "'s updates";
    $link = site_url($name);
    $pages = $App->getPage()->getChangelog($u);
} else {
    $pages = $App->getPage()->getActivity();
}

header('Content-Type: application/xml');
?>
<rss version="2.0">
    <channel>
        <title><?= $name ?></title>
        <description><?= $description ?></description>
        <link><?= $link ?></link>
        <?php foreach ($pages as $page): ?>
            <item>
                <title><?= $page['slug'] ?></title>
                <pubDate><?= date(DATE_RSS, strtotime($page['updated_at'])) ?></pubDate>
                <guid><?= htmlspecialchars(site_url($page['name'], $page['slug'])) ?></guid>
                <link><?= htmlspecialchars(site_url($page['name'], $page['slug'])) ?></link>
            </item>
        <?php endforeach; ?>
    </channel>
</rss>
