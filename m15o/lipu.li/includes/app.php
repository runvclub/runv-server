<?php

require 'config.php';

spl_autoload_register(function ($class) {
    require "classes/$class.php";
});

$App = new App();
$sess_id = $App->getSession()->id;
$User = $sess_id ? $App->getUser()->get($sess_id) : null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $App->getSession()->verifyCSRF($_POST['csrf']) or page_not_found();
}

function is_member($user)
{
    return $user && $user['role'] >= 1;
}

function is_admin($user)
{
    return $user && $user['role'] > 2;
}

function is_site_admin($admin)
{
    return is_member($GLOBALS['User']) && $admin['id'] === $GLOBALS['User']['id'];
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

function get_param($param)
{
    return filter_input(INPUT_GET, $param, FILTER_SANITIZE_SPECIAL_CHARS);
}

function timeAgo($dateString)
{
    $date = new DateTime($dateString);
    $now = new DateTime();
    $interval = $date->diff($now);

    if ($interval->y > 0) {
        $output = $interval->y . 'y';
    } elseif ($interval->m > 0) {
        $output = $interval->m . 'm';
    } elseif ($interval->d > 0) {
        $output = $interval->d . 'd';
    } elseif ($interval->h > 0) {
        $output = $interval->h . 'h';
    } elseif ($interval->i > 0) {
        $output = $interval->i . 'm';
    } else {
        $output = $interval->s . 's';
    }

    return $output;
}

function site_url($name, $page = null)
{
    $qs = "u=$name";
    $page && $qs .= "&p=$page";
    return URL . "/?$qs";
}

function site_link($name, $page = null, $value = null)
{
    $label = $value ?: ($page ?: $name);
    return '<a href="' . site_url($name, $page) . '">' . $label . '</a>';
}

function edit_link($page)
{
    return "<a href=\"page_update.php?p=$page\">Edit</a>";
}

function delete_link($page)
{
    return "<a href=\"page_delete.php?p=$page\">Delete</a>";
}

function gmi($text)
{
    $res = '';
    $mode = 0;
    $tok = strtok($text, PHP_EOL);

    while ($tok !== false) {
        if ($mode === 2) { // pre
            if (str_starts_with($tok, "```")) {
                $res .= '</pre>';
                $mode = 0;
            } else {
                $res .= $tok;
            }
        } else {
            if ($mode === 1) { // list
                if (str_starts_with($tok, "* ")) {
                    $res .= '<li>' . substr($tok, 2) . '</li>';
                    $tok = strtok(PHP_EOL);
                    continue;
                } else {
                    $res .= '</ul>';
                    $mode = 0;
                }
            }

            if (str_starts_with($tok, "# ")) {
                $res .= '<h1>' . substr($tok, 2) . '</h1>';
            } else if (str_starts_with($tok, "## ")) {
                $res .= '<h2>' . substr($tok, 2) . '</h2>';
            } else if (str_starts_with($tok, "### ")) {
                $res .= '<h3>' . substr($tok, 3) . '</h3>';
            } else if (str_starts_with($tok, "> ")) {
                $res .= '<blockquote>' . substr($tok, 2) . '</blockquote>';
            } else if (str_starts_with($tok, "* ")) {
                $res .= '<ul>';
                $res .= '<li>' . substr($tok, 2) . '</li>';
                $mode = 1;
            } else if (str_starts_with($tok, '```')) {
                $res .= '<pre>';
                $mode = 2;
            } else if (str_starts_with($tok, '=> ')) {
                $parts = explode(' ', substr($tok, 3), 2);
                $value = count($parts) > 1 ? $parts[1] : $parts[0];
                $res .= "<a href=\"$parts[0]\" class=\"link\">$value</a><br>";
            } else {
                $res .= '<p>' . $tok . '</p>';
            }
        }
        $tok = strtok(PHP_EOL);
    }

    if ($mode === 1) {
        $res .= '</ul>';
    }

    return $res;
}

define('LINK_REGEXP', '/\[\[([a-z0-9_-]+)\]\]/');

function content_to_html($content, $user)
{
    return preg_replace_callback(LINK_REGEXP, function ($match) use ($user) {
        $slug = $match[1];
        return site_link($user['name'], $slug);
    }, gmi($content));
}
