<?php

class Image
{
    private $db;

    public function __construct($db)
    {
        $this->db = $db;
    }

    public function getAll($page)
    {
        $sql = "SELECT
                    images.id, filename, description, user_id, users.name, published_at
                 FROM images
                 JOIN users ON images.user_id = users.id
                 ORDER BY published_at DESC
                 LIMIT ? OFFSET ?;";
        $res = $this->db->runSQL($sql, [PER_PAGE + 1, PER_PAGE * ($page - 1)])->fetchAll();
        return [
            "rows" => array_slice($res, 0, PER_PAGE),
            "next_page" => count($res) === PER_PAGE + 1
        ];
    }

    public function getFromUser($id, $page)
    {
        $sql = "SELECT
                    images.id, filename, description, user_id, users.name, published_at
                 FROM images
                 JOIN users ON images.user_id = users.id
                 WHERE users.id = ?
                 ORDER BY published_at DESC
                 LIMIT ? OFFSET ?;";
        $res = $this->db->runSQL($sql, [$id, PER_PAGE + 1, PER_PAGE * ($page - 1)])->fetchAll();
        return [
            "rows" => array_slice($res, 0, PER_PAGE),
            "next_page" => count($res) === PER_PAGE + 1
        ];
    }

    public function get($id)
    {
        $sql = "SELECT
                    images.id, filename, description, user_id, users.name, published_at
                 FROM images
                 JOIN users ON images.user_id = users.id
                 WHERE images.id = ?;";
        return $this->db->runSQL($sql, [$id])->fetch();
    }

    public function create($image)
    {
        $sql = "INSERT INTO images(user_id, filename, description)
                    VALUES (:user_id, :filename, :description);";
        $this->db->runSQL($sql, $image);
        return $this->db->lastInsertId();
    }

    public function delete($image_id, $user_id)
    {
        $this->db->beginTransaction();

        $sql = "SELECT filename
                FROM images
                WHERE id = ?;";
        $filename = $this->db->runSQL($sql, [$image_id])->fetchColumn();

        if (!$filename) {
            $this->db->rollback();
            return false;
        }

        if (!unlink(file_path($user_id, $filename))) {
            $this->db->rollback();
            return false;
        }

        $sql = "DELETE FROM images WHERE id = ?;";
        $this->db->runSQL($sql, [$image_id]);
        $this->db->commit();

        return true;
    }

    public function update($id, $user_id, $old_filename, $filename, $description)
    {
        if (!rename(file_path($user_id, $old_filename), file_path($user_id, $filename))) {
            return false;
        }
        $sql = "UPDATE images
                SET filename   = ?,
                    description = ?
                WHERE id = ? AND user_id = ?;";
        $this->db->runSQL($sql, [$filename, $description, $id, $user_id])->fetch();
        return true;
    }
}
