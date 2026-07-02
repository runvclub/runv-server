<?php
require 'includes/app.php';

$u = get_param("u");
$p = get_param("p");
$site_user = $App->getUser()->getFromUsername($u);
$is_admin = is_site_admin($site_user);

if ($p) {
    $page = $App->getPage()->get($site_user['id'], $p);
    $related = $App->getPage()->related($site_user['id'], $p);
    if ($page) {
        $content = content_to_html($page['content'], $site_user);
    }
    include 'includes/page.php';
} else if ($u) {
    $content = content_to_html($site_user['home'], $site_user);
    include 'includes/home.php';
} else if (is_member($User)) {
    redirect(site_url($User["name"]));
} else {
    include 'includes/index.php';
}
