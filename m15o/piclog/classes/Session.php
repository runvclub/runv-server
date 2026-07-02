<?php

class Session
{
    public $id;

    public function __construct()
    {
        session_start();
        $this->id = $_SESSION['id'] ?? 0;

        if ($_SERVER['REQUEST_METHOD'] === 'GET') {
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

    public function login($id)
    {
        session_regenerate_id();
        $this->id = $_SESSION['id'] = $id;
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
