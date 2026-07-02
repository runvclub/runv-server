<?php

require 'includes/app.php';

$BBS->getSession()->logout();
header('Location: .');
