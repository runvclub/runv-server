<?php

require 'includes/app.php';

$App->getSession()->logout();
header('Location: .');
