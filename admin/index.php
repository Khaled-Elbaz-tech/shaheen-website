<?php
session_start();
$CONFIG_FILE = __DIR__ . '/config.json';
// Default password: admin123 (change in config.json after first login)
$default_config = ['password_hash' => password_hash('admin123', PASSWORD_DEFAULT)];
if (!file_exists($CONFIG_FILE)) file_put_contents($CONFIG_FILE, json_encode($default_config));
$config = json_decode(file_get_contents($CONFIG_FILE), true);

$ROOT = dirname(__DIR__);
$CONTENT = $ROOT . '/content.json';

if (isset($_GET['logout'])) { session_destroy(); header('Location: index.php'); exit; }
if (isset($_POST['password'])) {
    if (password_verify($_POST['password'], $config['password_hash'])) { $_SESSION['admin'] = true; }
    else $error = 'Wrong password';
    header('Location: index.php'); exit;
}
if (!isset($_SESSION['admin'])) {
    echo '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Admin Login</title>';
    echo '<style>body{font-family:Arial;background:#0a0a0a;color:#fff;display:grid;place-items:center;min-height:100vh;margin:0}form{background:#1a1a1a;padding:40px;border-radius:8px}input{padding:12px;margin:10px 0;width:250px;background:#2a2a2a;border:1px solid #444;color:#fff}button{padding:12px 30px;background:#fff;color:#000;border:0;cursor:pointer;font-weight:bold}</style></head><body>';
    echo '<form method="post"><h2>Shaheen Admin</h2><input type="password" name="password" placeholder="Password" autofocus><br><button>Login</button></form></body></html>';
    exit;
}

// Handle save
$message = '';
if (isset($_POST['save_project'])) {
    $data = json_decode(file_get_contents($CONTENT), true);
    foreach ($data['groups'] as &$g) {
        if ($g['id'] === $_POST['project_id']) {
            $g['title'] = $_POST['title'];
            $g['location'] = $_POST['location'];
            $g['category'] = $_POST['category'];
            $g['body'] = $_POST['body'];
            break;
        }
    }
    file_put_contents($CONTENT, json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
    // Rebuild the site (Windows/XAMPP uses `python`, Linux uses `python3`)
    $py = (PHP_OS_FAMILY === 'Windows') ? 'python' : 'python3';
    $cmd = (PHP_OS_FAMILY === 'Windows')
        ? 'cd /d "' . $ROOT . '" && ' . $py . ' build.py 2>&1'
        : 'cd ' . escapeshellarg($ROOT) . ' && ' . $py . ' build.py 2>&1';
    $out = shell_exec($cmd);
    $message = 'Saved & rebuilt!';
}
if (isset($_POST['change_pw']) && $_POST['new_pw']) {
    $config['password_hash'] = password_hash($_POST['new_pw'], PASSWORD_DEFAULT);
    file_put_contents($CONFIG_FILE, json_encode($config));
    $message = 'Password changed!';
}

$data = json_decode(file_get_contents($CONTENT), true);
$edit_id = $_GET['edit'] ?? null;
$edit_project = null;
foreach ($data['groups'] as $g) if ($g['id'] === $edit_id) $edit_project = $g;
?>
<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Shaheen Admin</title>
<style>
*{box-sizing:border-box}body{font-family:Arial;background:#f5f4f0;margin:0;color:#1a1a1a}
header{background:#0a0a0a;color:#fff;padding:20px 40px;display:flex;justify-content:space-between;align-items:center}
header a{color:#fff;text-decoration:none;margin-left:20px}
main{max-width:1000px;margin:0 auto;padding:40px 20px}
.msg{background:#d4edda;padding:15px;border-radius:4px;margin-bottom:20px}
table{width:100%;border-collapse:collapse;background:#fff}
th,td{padding:12px;text-align:left;border-bottom:1px solid #ddd}
th{background:#0a0a0a;color:#fff}
a.btn{display:inline-block;padding:8px 16px;background:#0a0a0a;color:#fff;text-decoration:none;border-radius:4px}
form.edit{background:#fff;padding:30px;border-radius:8px}
form.edit label{display:block;margin:15px 0 5px;font-weight:bold}
form.edit input,form.edit textarea{width:100%;padding:12px;border:1px solid #ddd;border-radius:4px;font-size:14px}
form.edit textarea{height:150px}
form.edit button{margin-top:20px;padding:14px 40px;background:#0a0a0a;color:#fff;border:0;cursor:pointer;font-size:16px;border-radius:4px}
.pw-form{background:#fff;padding:20px;border-radius:8px;margin-top:30px}
</style></head><body>
<header><h1>Shaheen Website Admin</h1><div><a href="../dist/index.html" target="_blank">View Site</a><a href="?logout=1">Logout</a></div></header>
<main>
<?php if($message) echo "<div class='msg'>$message</div>"; ?>
<?php if($edit_project): ?>
<h2>Edit: <?=htmlspecialchars($edit_project['title'])?></h2>
<form class="edit" method="post">
<input type="hidden" name="project_id" value="<?=htmlspecialchars($edit_project['id'])?>">
<label>Title</label><input name="title" value="<?=htmlspecialchars($edit_project['title'])?>">
<label>Location</label><input name="location" value="<?=htmlspecialchars($edit_project['location'])?>">
<label>Category</label><input name="category" value="<?=htmlspecialchars($edit_project['category'])?>">
<label>Description</label><textarea name="body"><?=htmlspecialchars($edit_project['body'])?></textarea>
<button name="save_project" value="1">Save & Rebuild Site</button>
<a class="btn" href="index.php" style="margin-left:10px;background:#666">Cancel</a>
</form>
<?php else: ?>
<h2>Projects (<?=count($data['groups'])?>)</h2>
<table><tr><th>#</th><th>Title</th><th>Location</th><th>Category</th><th></th></tr>
<?php foreach($data['groups'] as $g): ?>
<tr><td><?=$g['number']?></td><td><?=htmlspecialchars($g['title'])?></td><td><?=htmlspecialchars($g['location'])?></td><td><?=htmlspecialchars($g['category'])?></td><td><a class="btn" href="?edit=<?=urlencode($g['id'])?>">Edit</a></td></tr>
<?php endforeach; ?>
</table>
<div class="pw-form"><h3>Change Password</h3><form method="post"><input type="password" name="new_pw" placeholder="New password" style="padding:10px;width:250px"><button name="change_pw" value="1" style="padding:10px 20px;background:#0a0a0a;color:#fff;border:0;cursor:pointer">Change</button></form></div>
<?php endif; ?>
</main></body></html>
