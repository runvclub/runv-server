<?php

class App
{
    private $db;
    private $page;
    private $user;
    private $token;
    private $session;
    private $email;

    public function __construct()
    {
        $this->db = new Database();
        $this->session = $session = new Session();
    }

    public function getPage()
    {
        if ($this->page === null) {
            $this->page = new Page($this->db);
        }
        return $this->page;
    }

    public function getUser()
    {
        if ($this->user === null) {
            $this->user = new User($this->db);
        }
        return $this->user;
    }

    public function getToken()
    {
        if ($this->token === null) {
            $this->token = new Token($this->db);
        }
        return $this->token;
    }

    public function getEmail()
    {
        if ($this->email === null) {
            $this->email = new Email();
        }
        return $this->email;
    }

    public function getSession()
    {
        return $this->session;
    }
}
