<?php

require 'includes/app.php';

$GLOBALS['App']->getSession()->logout();
header('Location: .');
