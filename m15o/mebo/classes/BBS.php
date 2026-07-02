<?php

class BBS
{
    private $db;
    private $thread;
    private $reply;
    private $user;
    private $token;
    private $session;
    private $email;

    public function __construct()
    {
        $this->db = new Database();
        $this->session = $session = new Session();
    }

    public function getThread()
    {
        if ($this->thread === null) {
            $this->thread = new Thread($this->db);
        }
        return $this->thread;
    }

    public function getUser()
    {
        if ($this->user === null) {
            $this->user = new User($this->db);
        }
        return $this->user;
    }

    public function getReply()
    {
        if ($this->reply === null) {
            $this->reply = new Reply($this->db);
        }
        return $this->reply;
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
