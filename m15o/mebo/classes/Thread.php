<?php

class Thread
{
    private $db;

    public function __construct($db)
    {
        $this->db = $db;
    }

    public function getAll()
    {
        $sql = "SELECT
                 t.title, t.updated_at, t.id, t.sticky,
                 (SELECT COUNT(thread_id)
                    FROM replies
                   WHERE replies.thread_id = t.id) AS replies,
                 (SELECT MAX(id)
                    FROM replies
                   WHERE replies.thread_id = t.id) AS last_reply_id
                 FROM threads AS t
                 ORDER BY
                   sticky DESC,
                   updated_at DESC;";
        return $this->db->runSQL($sql)->fetchAll();
    }

    public function get($id)
    {
        $sql = "SELECT threads.*, users.name, users.role FROM threads
                JOIN users ON threads.user_id = users.id WHERE threads.id=?;";
        return $this->db->runSQL($sql, [$id])->fetch();
    }

    public function update($id, $title, $content, $sticky)
    {
        $sql = "UPDATE threads
                SET title   = ?,
                    content = ?,
                    sticky  = ?
                WHERE id = ?;";
        $this->db->runSQL($sql, [$title, $content, $sticky, $id])->fetch();
        return true;
    }

    public function create($thread)
    {
        $sql = "INSERT INTO threads(user_id, title, content, sticky)
                    VALUES (:user_id, :title, :content, :sticky);";
        $this->db->runSQL($sql, $thread);
        return $this->db->lastInsertId();
    }

    public function delete($thread_id, $user_id, $is_admin)
    {
        $this->db->beginTransaction();

        $sql = "SELECT count(*)
                FROM replies
                WHERE thread_id = ? AND user_id <> ?";
        $replies = $this->db
                        ->runSQL($sql, [$thread_id, $user_id])->fetchColumn();

        if ($replies && !$is_admin) {
            $this->db->rollback();
            return false;
        }

        $sql = "DELETE FROM threads WHERE id = ?;";
        $this->db->runSQL($sql, [$thread_id]);
        $this->db->commit();

        return true;
    }
}
