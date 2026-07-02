<?php

class Reply
{
    private $db;

    public function __construct($db)
    {
        $this->db = $db;
    }

    public function get($id)
    {
        $sql = "SELECT replies.*, users.name FROM replies
                 JOIN users ON replies.user_id = users.id
                 WHERE replies.id=?;";
        return $this->db->runSQL($sql, [$id])->fetch();
    }

    public function getAll($id)
    {
        $sql = "SELECT replies.*, users.name, users.role FROM replies
                JOIN users ON replies.user_id = users.id WHERE thread_id=?
                ORDER BY published_at;";
        return $this->db->runSQL($sql, [$id])->fetchAll();
    }

    public function create($reply)
    {
        $this->db->beginTransaction();

        $sql = "INSERT INTO replies(content, user_id, thread_id)
                    VALUES (:content, :user_id, :thread_id);";
        $this->db->runSQL($sql, $reply);
        $id = $this->db->lastInsertId();

        $sql = "UPDATE threads SET updated_at = now() WHERE id=?";
        $this->db->runSQL($sql, [$reply['thread_id']]);

        $this->db->commit();
        return $id;
    }

    public function update($id, $content)
    {
        $sql = "UPDATE replies SET content = ? WHERE id = ?;";
        $this->db->runSQL($sql, [$content, $id]);
        return true;
    }

    public function delete($id)
    {
        $sql = "DELETE FROM replies WHERE id = ?;";
        $this->db->runSQL($sql, [$id]);
        return true;
    }
}
