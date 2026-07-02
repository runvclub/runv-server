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

    public static function isPage($str)
    {
        return preg_match('/^[a-z0-9_-]+$/', $str);
    }

    public static function isAcceptableHTML($str) {
        $allowedTags = '<a><em>';
        $stripped = strip_tags($str, $allowedTags);
        return $stripped == $str;
    }
}
