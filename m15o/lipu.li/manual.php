<?php include 'includes/app.php'; ?>
<?php include 'includes/header.php'; ?>

<h1>Manual</h1>

<h2>Write pages in gemtext and HTML</h2>

<pre>
# This is an h1 title
## this is an h2 title
### this is an h3 title
This is normal text!
> this is a quote
=> https://example.com this is a link
```
this is preformatted text
```
</pre>

<p>You can use HTML tags as well.</p>

<h2>Connect pages together with [[]]</h2>

<p>You can surround a word with [[]] to create a link to a page with a corresponding slug. Here's an example:</p>

<pre># coffee

A popular machine is the [[aeropress]].</pre>

<p>The page with the <code>aeropress</code> slug will now have a backlink to the coffee page.</p>

<?php include 'includes/footer.php'; ?>