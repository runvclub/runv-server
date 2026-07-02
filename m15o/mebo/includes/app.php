<?php

require 'config.php';

spl_autoload_register(function ($class) {
    require "classes/$class.php";
});

$BBS = new BBS();
$user = $BBS->getSession()->id ? $BBS->getUser()->get($BBS->getSession()->id) : null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $BBS->getSession()->verifyCSRF($_POST['csrf']) or page_not_found();
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

function thread_url($id, $reply_id = null)
{
    $url = "thread_read.php?id=$id";

    if (isset($reply_id)) {
        $url .= "&last=$reply_id";
    }

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

function text($string)
{
    $txt = htmlentities($string);
    $txt = str_replace(array("\r\n", "\r", "\n"), "\n", $txt);
    $txt = preg_replace(
        "/\n?```\n(.*?)\n```/s",
        '<pre>$1</pre>',
        $txt
    );
    $txt = preg_replace(
        '/^\s*&gt;\s*(.*)$/m',
        '<span class="quote">$0</span>',
        $txt
    );
    $txt = str_replace("\n", "<br>", $txt);
    $txt = preg_replace(
        '#\bhttps?://[^,\s()<>]+(?:\([\w\d]+\)|([^,[:punct:]\s]|/))#',
        '<a href="$0">$0</a>',
        $txt
    );
    return $txt;
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

function get_name($user)
{
    return $user['role'] === 0 ? "[suspended]" : $user['name'];
}
