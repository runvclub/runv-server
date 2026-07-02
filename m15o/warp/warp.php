<?php
$url = $_GET['url'] ?? 'nex://nex.nightfall.city';
$page = "";

function is_directory($url) {
    return str_ends_with($url, '/');
}
function url($base, $path) {
    if (!$base) return;

    if (substr($path, 0, 6) === "nex://") {
        return $path;
    }

    $parsed = parse_url($base);
    $parsed_path = $parsed['path'] ?? '';

    $res = [];
    if ($parsed_path != '/' && $parsed_path != '') {
        $res = explode('/', trim($parsed_path, '/'));
    }
    $segments = explode('/', trim($path));

    $i = count($segments);
    if ($i > 1 && $segments[0] == '') {
        array_shift($segments);
        $res = $segments;
    } else {
        foreach ($segments as $key => $segment) {
            if ($segment == '..') {
                array_pop($res);
                if ($key == $i - 1) $res[] = '';
            } elseif ($segment !== '.') {
                $res[] = $segment;
            }
        }
    }

    array_unshift($res, "nex://".$parsed['host']);
    return implode('/', $res);
}
function parse_line($url, $line) {
    if (substr($line, 0, 3 ) === "=> ") {
        $l = substr(trim($line), 3);
        $u = explode(" ", $l)[0];
        $p = url($url, $u);
        $desc = implode(" ", array_slice(explode(" ", $l), 1));
        return "=> <a href=\"?url=$p\">$u</a> $desc" . PHP_EOL;
    } else {
        return htmlentities($line);
    }
}

if ($url) {
    $parsed_url = parse_url($url);
    $parsed_path = $parsed_url['path'] ?? '';
    if ($parsed_path == '') {
        $url .= "/";
    }
    if ($parsed_url['scheme'] !== 'nex') {
        $page = "unsupported protocol";
    } else {
        $fp = fsockopen($parsed_url['host'], 1900, $errno, $errstr, 30);
        if (!$fp) {
            $page = "$errstr ($errno)";
        } else {
            fwrite($fp, $parsed_path . PHP_EOL);
            switch (strtolower(pathinfo($parsed_path)['extension'] ?? '')) {
                case 'jpg': case 'jpeg':
                    header("Content-Type: image/jpeg");
                    fpassthru($fp);
                    fclose($fp);
                    exit;
                default:
                    while (!feof($fp)) {
                        if (is_directory($url)) {
                            $page .= parse_line($url, fgets($fp));
                        } else {
                            $page .= htmlentities(fgets($fp));
                        }
                    }
                    fclose($fp);
            }
        }
    }
}
?>
<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <title>warp</title>
    </head>
<body>
    <form>
        <input type="text" id="url" name="url" style="width: 60ch;" value="<?=$url?>">
        <input type="submit" value="go">
        <a href="?url=<?=url($url, "..")?>">up</a>
    </form>
    <hr>
    <pre><?=$page?></pre>
</body>
</html>