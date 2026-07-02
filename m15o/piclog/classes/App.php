<?php

class App
{
    private $db;
    private $image;
    private $user;
    private $token;
    private $session;
    private $email;

    public function __construct()
    {
        $this->db = new Database();
        $this->session = $session = new Session();
    }

    public function getImage()
    {
        if ($this->image === null) {
            $this->image = new Image($this->db);
        }
        return $this->image;
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
