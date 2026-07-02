<?php

class Session
{
    public $id;

    public function __construct()
    {
        session_start();
        $this->id = $_SESSION['id'] ?? 0;
        if ($this->getCSRF() === '') {
            $_SESSION['csrf'] = bin2hex(random_bytes(64));
        }
    }

    public function getCSRF()
    {
        return $_SESSION['csrf'] ?? '';
    }

    public function verifyCSRF($csrf)
    {
        if (!$this->getCSRF() || !$csrf) {
            return false;
        }

        return hash_equals($this->getCSRF(), $csrf);
    }

    public function login($id, $remember)
    {
        session_regenerate_id();
        $this->id = $_SESSION['id'] = $id;
        if ($remember) {
            $param = session_get_cookie_params();
            setcookie(
                session_name(),
                session_id(),
                time() + 60 * 60 * 24 * 30,
                $param['path'],
                $param['domain'],
                $param['secure'],
                $param['httponly']
            );
        }
    }

    public function logout()
    {
        $_SESSION = [];
        $param = session_get_cookie_params();
        setcookie(
            session_name(),
            '',
            time() - 2400,
            $param['path'],
            $param['domain'],
            $param['secure'],
            $param['httponly']
        );
        session_destroy();
    }

    public function setFlash($msg)
    {
        $_SESSION['flash'] = $msg;
    }

    public function getFlash()
    {
        if (!isset($_SESSION['flash'])) {
            return '';
        }
        $msg = $_SESSION['flash'];
        unset($_SESSION['flash']);
        return $msg;
    }
}
