<?php

class Validate
{
    public static function isName($str)
    {
        return filter_var($str, FILTER_VALIDATE_REGEXP, [
            'options' => [
                'regexp' => '/^[A-z0-9]{2,20}$/',
            ]
        ]);
    }

    public static function isPassword($str)
    {
        return mb_strlen($str) > 5;
    }

    public static function isEmail($str)
    {
        return filter_var($str, FILTER_VALIDATE_EMAIL);
    }

    public static function isAvailableFilename($id, $filename) {
        clearstatcache();
        return !file_exists(file_path($id, $filename));
    }

    public static function isFilename($str)
    {
        // check extension
        if (!in_array(strtolower(pathinfo($str, PATHINFO_EXTENSION)), ['jpeg', 'jpg', 'png', 'gif'])) {
            return false;
        }

        // check basename
        if (!preg_match('/^[A-z0-9_()-]+$/', pathinfo($str, PATHINFO_FILENAME))) {
            return false;
        }

        return true;
    }

    public static function isAcceptableHTML($str) {
        $allowedTags = '<img><a><div><table><tbody><caption><strike><tr><td><th><br><p><b><strong><i><u><em><span><sup><sub><time><ol><ul><li><blockquote><del><mark><pre><code><hr><h1><h2><h3><h4><h5><h6><big><small><font><center><blink><marquee><details><summary><section><aside><style><picture>';
        $stripped = strip_tags($str, $allowedTags);
        return $stripped == $str;
    }
}
