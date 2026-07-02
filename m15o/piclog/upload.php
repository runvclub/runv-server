<?php
require 'includes/app.php';

is_member($user) or redirect("login.php");

function resize_image_gd($orig_path, $new_path, $max_width, $max_height)
{
    $image_data = getimagesize($orig_path);
    $orig_width = $image_data[0];
    $orig_height = $image_data[1];
    $media_type = $image_data['mime'];
    $new_width = ($orig_width > $max_width) ? $max_width : $orig_width;
    $new_height = ($orig_height > $max_height) ? $max_height : $orig_height;
    $orig_ratio = $orig_width / $orig_height;

    if (($new_width >= $max_width) || ($new_height >= $max_height)) {
        if ($orig_width > $orig_height) {
            $new_height = (int)($new_width / $orig_ratio);
        } else {
            $new_width = (int)($new_height * $orig_ratio);
        }
    }

    switch ($media_type) {
        case 'image/jpeg':
            $orig = imagecreatefromjpeg($orig_path);
            break;
        default:
            exit;
    }

    $new = imagecreatetruecolor($new_width, $new_height);

    imagecopyresampled($new, $orig, 0, 0, 0, 0, $new_width, $new_height, $orig_width, $orig_height);

    switch ($media_type) {
        case 'image/jpeg':
            $result = imagejpeg($new, $new_path, 5);
            break;
    }

    return $result;
}

$message = '';
$resized = false;
$errors = [];
$allowed_types = ['image/jpeg'];
$max_size = 524288; // 512 kb

if ($_SERVER['REQUEST_METHOD'] == 'POST') {
    $error = ($_FILES['image']['error'] === 1) ? 'too big' : '';

    if ($_FILES['image']['error'] === 0) {
        // check media type
        if (!in_array(mime_content_type($_FILES['image']['tmp_name']), $allowed_types)) {
            $errors [] = 'Wrong type';
        }

        // check form
        $_FILES['image']['size'] <= $max_size or $errors [] = ' File too big (512kB max)';
        Validate::isFilename($_FILES['image']['name']) or $errors [] = 'Wrong file name';
        Validate::isAvailableFilename($user['id'], $_FILES['image']['name']) or $errors [] = 'File already exists';

        if (!count($errors)) {
            $temp = $_FILES['image']['tmp_name'];
            $path = file_path($user['id'], $_FILES['image']['name']);
            $resized = resize_image_gd($temp, $path, 400, 400);
        }
    }

    if (!$resized) {
        $message = 'File could not be uploaded';
    } else {
        $id = $App->getImage()->create([
            "filename" => $_FILES['image']['name'],
            "description" => $_POST['description'],
            "user_id" => $user['id']
        ]);
        redirect('image.php?id=' . $id);
    }
}
?>

<?php include 'includes/header.php'; ?>

<h1>Upload image</h1>

<?php form_errors($errors) ?>
<?= $message ?>

<form action="<?= $_SERVER['PHP_SELF'] ?>" method="post" enctype="multipart/form-data">
    <?php include 'includes/csrf.php' ?>
    <label for="name">Image:</label>
    <input type="file" id="image" name="image" accept="image/jpeg">

    <label for="description">Description:</label>
    <textarea name="description" id="description" class="form-control" required></textarea>

    <input type="submit" value="Submit"/>
</form>

<?php include 'includes/footer.php'; ?>
