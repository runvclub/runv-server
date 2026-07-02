<?php

require 'config.php';

spl_autoload_register(function ($class) {
    require "classes/$class.php";
});

$App = new App();
$user = $App->getSession()->id ? $App->getUser()->get($App->getSession()->id) : null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $App->getSession()->verifyCSRF($_POST['csrf']) or page_not_found();
}

function is_visitor($user)
{
    return $user && $user['role'] === 1;
}

function is_member($user)
{
    return $user && $user['role'] > 1;
}

function is_admin($user)
{
    return $user && $user['role'] > 2;
}

function image_url($id)
{
    $url = "image.php?id=$id";

    return $url;
}

function redirect($page)
{
    header("Location: $page");
    exit;
}

function page_not_found()
{
    http_response_code(404);
    echo "not found";
    exit;
}

function to_date($str)
{
    return date("Y-m-d", strtotime($str));
}

function form_errors($errors)
{
    if (!$errors) {
        return;
    }

    echo '<ul class="form-error">';

    foreach ($errors as $error) {
        echo '<li>' . $error;
    }

    echo '</ul>';
}

function get_id()
{
    if (!($id = filter_input(INPUT_GET, 'id', FILTER_VALIDATE_INT))) {
        page_not_found();
    }

    return $id;
}

function get_page()
{
    if (!($page = filter_input(INPUT_GET, 'p', FILTER_VALIDATE_INT))) {
        return 1;
    }

    return $page;
}

function file_path($id, $filename)
{
    return 'uploads/' . $id . '/' . $filename;
}

function image_path($id)
{
    return 'image.php?id=' . $id;
}

function get_name($user)
{
    return $user['role'] === 0 ? "[suspended]" : $user['name'];
}

function timeAgo($dateString)
{
    $date = new DateTime($dateString);
    $now = new DateTime();
    $interval = $date->diff($now);

    if ($interval->y > 0) {
        $output = $interval->y . ($interval->y > 1 ? ' years ago' : ' year ago');
    } elseif ($interval->m > 0) {
        $output = $interval->m . ($interval->m > 1 ? ' months ago' : ' month ago');
    } elseif ($interval->d > 0) {
        $output = $interval->d . ($interval->d > 1 ? ' days ago' : ' day ago');
    } elseif ($interval->h > 0) {
        $output = $interval->h . ($interval->h > 1 ? ' hours ago' : ' hour ago');
    } elseif ($interval->i > 0) {
        $output = $interval->i . ($interval->i > 1 ? ' minutes ago' : ' minute ago');
    } else {
        $output = 'Just now';
    }

    return $output;
}