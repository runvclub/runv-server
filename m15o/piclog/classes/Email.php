<?php

use PHPMailer\PHPMailer\PHPMailer;

require 'vendor/PHPMailer/src/PHPMailer.php';
require 'vendor/PHPMailer/src/SMTP.php';
require 'vendor/PHPMailer/src/Exception.php';

class Email
{
    private $mail;

    public function __construct()
    {
        $this->mail = new PHPMailer(true);
        $this->mail->isSMTP();
        $this->mail->Host = SMTP_SERVER;
        $this->mail->SMTPAuth = true;
        $this->mail->Username = SMTP_USERNAME;
        $this->mail->Password = SMTP_PASSWORD;
        $this->mail->SMTPSecure = PHPMailer::ENCRYPTION_SMTPS;
        $this->mail->Port = 465;
        $this->mail->CharSet = 'UTF-8';
        $this->mail->isHTML(false);
    }

    public function send($to, $subject, $message)
    {
        $this->mail->setFrom(FROM_EMAIL);
        $this->mail->addAddress($to);
        $this->mail->Subject = $subject;
        $this->mail->Body = $message;
        $this->mail->send();
    }
}
