<?php

class User
{
    private $db;

    public function __construct($db)
    {
        $this->db = $db;
    }

    public function get($id)
    {
        $sql = "SELECT * FROM users WHERE id=?;";
        return $this->db->runSQL($sql, [$id])->fetch();
    }

    public function getIdFromEmail($email)
    {
        $sql = "SELECT id FROM users WHERE email=?";
        return $this->db->runSQL($sql, [$email])->fetchColumn();
    }

    public function getAll()
    {
        $sql = "select * from users;";
        return $this->db->runSQL($sql)->fetchAll();
    }

    public function getAllInactive()
    {
        $sql = "select * from users where role=1";
        return $this->db->runSQL($sql)->fetchAll();
    }

    public function create($user, &$errors)
    {
        $this->db->beginTransaction();

        $sql = "SELECT name FROM users where name=:name";
        $name_used = $this->db->runSQL($sql, [$user['name']])->fetch();

        if ($name_used) {
            $errors[] = "Name already used";
            $this->db->rollback();
            return false;
        }

        $sql = "SELECT COUNT(*) FROM users;";
        $user['role'] = $this->db->runSQL($sql)->fetchColumn() ? 1 : 3;

        $user['hash'] = password_hash($user['password'], PASSWORD_BCRYPT);
        unset($user['password']);

        try {
            $sql = "INSERT INTO users(name, email, hash, role, cover) VALUES (:name, :email, :hash, :role, :cover)";
            $this->db->runSQL($sql, $user);
            $id = (int)$this->db->lastInsertId();
            if (!mkdir('uploads/' . $id)) {
                $errors[] = "Can't create image folder";
                $this->db->rollback();
                return false;
            }
            $this->db->commit();
            return $id;
        } catch(PDOException $e) {
            if ($e->errorInfo[1] === 1062) {
                $errors[] = "Email already used";
                $this->db->rollback();
                return false;
            }
            throw $e;
        }
    }

    public function updatePassword($id, $password)
    {
        $sql = "UPDATE users SET hash=? WHERE id=?";
        $this->db->runSQL($sql, [
            password_hash($password, PASSWORD_BCRYPT),
            $id,
        ]);
        return true;
    }

    public function login($email, $password, &$errors)
    {
        $sql = "SELECT id, hash FROM users WHERE email=?";
        $new = $this->db->runSQL($sql, [$email])->fetch();
        if (!$new) {
            $errors[] = 'User not found';
            return false;
        }

        if (!password_verify($password, $new['hash'])) {
            $errors[] = "Wrong password";
            return false;
        }

        return $new;
    }

    public function setRole($id, $role)
    {
        $sql = "update users set role=? where id=?";
        return $this->db->runSQL($sql, [$role, $id])->rowCount();
    }

    public function update($user, &$errors)
    {
        $this->db->beginTransaction();

        $sql = "select name from users where name=? and id<>?";
        $name_used = $this->db->runSQL($sql, [$user['name'], $user['id']])->fetch();

        if ($name_used) {
            $errors[] = "Name already used";
            $this->db->rollback();
            return false;
        }

        try {
            $sql = "update users set name=?, email=?, cover=? where id=?";
            $this->db->runSQL($sql, [$user['name'], $user['email'], $user['cover'], $user['id']])->fetch();
            $this->db->commit();
            return true;
        } catch (PDOException $e) {
            if ($e->errorInfo[1] === 1062) {
                $errors[] = "Email already used";
                $this->db->rollback();
                return false;
            }
            throw $e;
        }
    }
}
