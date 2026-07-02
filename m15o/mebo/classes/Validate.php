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

    public static function isTitle($str)
    {
        return mb_strlen($str) > 2;
    }
}
