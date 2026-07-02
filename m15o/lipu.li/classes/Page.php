<?php

class Page
{
    private $db;

    public function __construct($db)
    {
        $this->db = $db;
    }

    public function getAll($name)
    {
        $sql = "SELECT
                 slug, content, name
                 FROM pages
                 LEFT JOIN users on pages.user_id = users.id
                 WHERE name=?
                 ORDER BY slug";
        return $this->db->runSQL($sql, [$name])->fetchAll();
    }

    public function getActivity()
    {
        $sql = "SELECT
                 slug, content, updated_at, user_id, name
                 FROM pages
                 LEFT JOIN users on pages.user_id = users.id
                 WHERE users.role > 1
                 ORDER BY updated_at desc
                 LIMIT 100";
        return $this->db->runSQL($sql)->fetchAll();
    }
    public function getChangelog($name)
    {
        $sql = "SELECT
                 slug, content, updated_at, name
                 FROM pages
                 LEFT JOIN users on pages.user_id = users.id
                 WHERE name=?
                 ORDER BY updated_at desc";
        return $this->db->runSQL($sql, [$name])->fetchAll();
    }

    public function get($id, $slug)
    {
        $sql = "SELECT user_id, slug, content FROM pages WHERE user_id=? AND slug=?;";
        return $this->db->runSQL($sql, [$id, $slug])->fetch();
    }

    public function related($id, $slug)
    {
        $sql = "SELECT * FROM pages WHERE content LIKE ? AND user_id=?;";
        return $this->db->runSQL($sql, ["%[[$slug]]%", $id])->fetchAll();
    }

    public function update($user_id, $slug, $content)
    {
        $sql = "UPDATE pages
                SET content   = ?
                WHERE user_id = ? AND slug = ?;";
        $this->db->runSQL($sql, [$content, $user_id, $slug])->fetch();
        return true;
    }

    public function create($user_id, $name, $content)
    {
        $sql = "INSERT INTO pages(user_id, slug, content)
                    VALUES (?, ?, ?);";
        $this->db->runSQL($sql, [$user_id, $name, $content]);
        return $this->db->lastInsertId();
    }

    public function delete($user_id, $slug)
    {
        $sql = "DELETE FROM pages WHERE user_id = ? AND slug = ?;";
        $this->db->runSQL($sql, [$user_id, $slug]);
    }
}