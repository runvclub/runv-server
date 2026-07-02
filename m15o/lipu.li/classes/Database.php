<?php

class Database extends PDO
{
    public function __construct()
    {
        parent::__construct("mysql:host=".DB_HOST.";dbname=".DB_NAME, DB_USER, DB_PASSWORD, [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES => false,
        ]);
    }

    public function runSQL($sql, $arguments = null)
    {
        if (!$arguments) {
            return $this->query($sql);
        }

        $stmt = $this->prepare($sql);
        $stmt->execute($arguments);
        return $stmt;
    }
}
