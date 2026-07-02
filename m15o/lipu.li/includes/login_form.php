<form action="login.php" method="post">
    <?php include 'csrf.php' ?>

    <label for="form-name">Email:</label>
    <input type="email" name="email" value="" class="form-control"/>

    <label for="form-password">Password:</label>
    <input type="password" name="password" class="form-control" required/>

    <p>
        <input type="submit" value="Login"/>
        <input type="checkbox" id="remember" name="remember"> <label for="remember">Remember me</label>
    </p>

    <nav>
        <a href="password-lost.php">Password lost?</a> <a href="register.php">Register</a>
    </nav>
</form>