<?php

class Token
{
    private $db;

    public function __construct($db)
    {
        $this->db = $db;
    }

    public function getUserId($token)
    {
        $sql = "SELECT user_id FROM tokens WHERE token=?";
        return $this->db->runSQL($sql, [$token])->fetchColumn();
    }

    public function create($id)
    {
        $sql = "INSERT into tokens (token, user_id) VALUES (?, ?)";
        $token = bin2hex(random_bytes(64));
        $this->db->runSQL($sql, [$token, $id]);
        return $token;
    }
}
