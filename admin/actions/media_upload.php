<?php
/** POST do=media_upload — validate, convert to WebP (GD/Imagick if available), store in ../dist/assets. */
declare(strict_types=1);

require_perm('media');
$u = current_user();

$f = $_FILES['image'] ?? null;
if (!$f || ($f['error'] ?? UPLOAD_ERR_NO_FILE) === UPLOAD_ERR_NO_FILE) {
    flash('error', 'Choose a file to upload.');
    redirect(admin_url('media'));
}
if ($f['error'] !== UPLOAD_ERR_OK) {
    flash('error', 'Upload failed (error code ' . (int)$f['error'] . ').');
    redirect(admin_url('media'));
}

$MAX = 10 * 1024 * 1024;
if ($f['size'] > $MAX) { flash('error', 'File is larger than the 10 MB limit.'); redirect(admin_url('media')); }
if ($f['size'] === 0) { flash('error', 'Empty file.'); redirect(admin_url('media')); }

// Real MIME check (never trust the extension).
$finfo = new finfo(FILEINFO_MIME_TYPE);
$mime = $finfo->file($f['tmp_name']);
$allowed = ['image/jpeg' => 'jpg', 'image/png' => 'png', 'image/webp' => 'webp'];
if (!isset($allowed[$mime])) {
    flash('error', 'Only JPG, PNG or WebP images are accepted (detected: ' . $mime . ').');
    redirect(admin_url('media'));
}
$size = @getimagesize($f['tmp_name']);
if ($size === false) { flash('error', 'File is not a valid image.'); redirect(admin_url('media')); }

$base = pathinfo(safe_filename($f['name']), PATHINFO_FILENAME);
$base = strtolower(preg_replace('#[^a-z0-9]+#', '-', $base));
$base = trim($base, '-');
if ($base === '') $base = 'image';
$key = $base; $i = 2;
while (file_exists(ASSETS_DIR . '/' . $key . '.webp')) { $key = $base . '-' . $i++; }
$dest = ASSETS_DIR . '/' . $key . '.webp';

$converted = false;
if ($mime !== 'image/webp' && extension_loaded('gd')) {
    $src = match ($mime) {
        'image/jpeg' => @imagecreatefromjpeg($f['tmp_name']),
        'image/png'  => @imagecreatefrompng($f['tmp_name']),
        default      => null,
    };
    if ($src) {
        // Downscale very large uploads to a sane web width.
        $w = imagesx($src); $h = imagesy($src);
        $maxW = 2200;
        if ($w > $maxW) {
            $nh = (int)round($h * $maxW / $w);
            $rs = imagecreatetruecolor($maxW, $nh);
            imagecopyresampled($rs, $src, 0, 0, 0, 0, $maxW, $nh, $w, $h);
            imagedestroy($src); $src = $rs;
        }
        $converted = @imagewebp($src, $dest, 85);
        imagedestroy($src);
    }
}
if (!$converted) {
    if ($mime === 'image/webp') {
        $converted = move_uploaded_file($f['tmp_name'], $dest);
    } else {
        // GD unavailable: store the original file as-is (still usable by <img>).
        $dest = ASSETS_DIR . '/' . $key . '.' . $allowed[$mime];
        $converted = move_uploaded_file($f['tmp_name'], $dest);
        $key = $key; // key stays; extension differs
    }
}
if (!$converted) {
    flash('error', 'Could not store the uploaded file (check folder permissions).');
    redirect(admin_url('media'));
}
@chmod($dest, 0644);

// Optional title/alt stored as an override in site.json (assets.json stays read-only).
$title = trim((string)($_POST['title'] ?? ''));
$alt = trim((string)($_POST['alt'] ?? ''));
if ($title !== '' || $alt !== '') {
    $site = site_load();
    $site['media_meta'][$key] = ['title' => $title, 'alt' => $alt, 'caption' => ''];
    try { site_save($site); } catch (Throwable $t) { /* non-fatal */ }
}

log_activity($u ? (int)$u['id'] : null, 'media_upload', $key . ' (' . human_filesize((int)@filesize($dest)) . ')');
flash('success', 'Uploaded as "' . $key . '"' . ($mime !== 'image/webp' && extension_loaded('gd') ? ' (converted to WebP).' : '.') .
    ' Note: it is not in assets.json metadata — the frontend should still load it via the asset key.');
redirect(admin_url('media'));
