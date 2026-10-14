<?php
/** POST do=pages_save — save site.json page sections, then rebuild.
 *  Shapes match build.py DEFAULT_SITE exactly:
 *  sections_order = flat id list; disabled ids live in sections_disabled
 *  (admin-only until the build honours them).
 */
declare(strict_types=1);

require_perm('pages');
$u = current_user();

$site = site_load();

// Hero
$site['hero']['headline']   = trim((string)($_POST['hero_headline'] ?? ''));
$site['hero']['descriptor'] = trim((string)($_POST['hero_descriptor'] ?? ''));
$site['hero']['image']      = trim((string)($_POST['hero_image'] ?? ''));
$site['hero']['project_id'] = trim((string)($_POST['hero_project_id'] ?? ''));
$site['hero']['alt']        = trim((string)($_POST['hero_alt'] ?? ''));

// Intro
$site['intro']['eyebrow']   = trim((string)($_POST['intro_eyebrow'] ?? ''));
$site['intro']['statement'] = trim((string)($_POST['intro_statement'] ?? ''));
$site['intro']['copy']      = (string)($_POST['intro_copy'] ?? '');

// Studio
$site['studio']['headline']      = trim((string)($_POST['studio_headline'] ?? ''));
$site['studio']['intro']         = trim((string)($_POST['studio_intro'] ?? ''));
$site['studio']['bio']           = (string)($_POST['studio_bio'] ?? '');
$site['studio']['philosophy']    = (string)($_POST['studio_philosophy'] ?? '');
$site['studio']['image']         = trim((string)($_POST['studio_image'] ?? ''));
$site['studio']['image_alt']     = trim((string)($_POST['studio_image_alt'] ?? ''));
$site['studio']['image_caption'] = trim((string)($_POST['studio_image_caption'] ?? ''));

// Approach: 4 fixed stages, editable text.
$stages = [];
for ($i = 0; $i < 4; $i++) {
    $stages[] = [
        'n'     => str_pad((string)($i + 1), 2, '0', STR_PAD_LEFT),
        'title' => trim((string)($_POST['stage_title_' . $i] ?? '')),
        'text'  => trim((string)($_POST['stage_text_' . $i] ?? '')),
    ];
}
$site['approach']['headline'] = trim((string)($_POST['approach_headline'] ?? ''));
$site['approach']['intro']    = trim((string)($_POST['approach_intro'] ?? ''));
$site['approach']['stages']   = $stages;

// Landscape gallery: headline/intro + image list (key|caption|alt per row).
$site['landscape_gallery']['headline'] = trim((string)($_POST['lg_headline'] ?? ''));
$site['landscape_gallery']['intro']    = trim((string)($_POST['lg_intro'] ?? ''));
$imgs = [];
foreach ((array)($_POST['lg_images'] ?? []) as $row) {
    if (!is_array($row)) continue;
    $key = trim((string)($row['key'] ?? ''));
    if ($key === '') continue;
    $imgs[] = [
        'key'     => $key,
        'caption' => trim((string)($row['caption'] ?? '')),
        'alt'     => trim((string)($row['alt'] ?? '')),
    ];
}
$site['landscape_gallery']['images'] = $imgs;

// Contact
$site['contact']['headline'] = trim((string)($_POST['contact_headline'] ?? ''));
$site['contact']['copy']     = trim((string)($_POST['contact_copy'] ?? ''));
$email = trim((string)($_POST['contact_email'] ?? ''));
if ($email !== '' && !filter_var($email, FILTER_VALIDATE_EMAIL)) {
    flash('error', 'Contact email is not valid.');
    redirect(admin_url('pages'));
}
$site['contact']['email'] = $email;
$socials = [];
foreach ((array)($_POST['social_label'] ?? []) as $i => $label) {
    $label = trim((string)$label);
    $url = trim((string)($_POST['social_url'][$i] ?? ''));
    if ($label === '' || $url === '') continue;
    if (!is_safe_url($url)) { flash('error', 'Social URL for "' . $label . '" is not safe/valid.'); redirect(admin_url('pages')); }
    $socials[$label] = $url;
}
$site['contact']['socials'] = $socials;

// Sections order (flat id list, as build.py iterates it) + disabled ids.
// NOTE: build.py currently renders every id in sections_order, so disabling
// is stored but not honoured yet — the UI warns about this.
$order = [];
$disabled = [];
foreach ((array)($_POST['section_id'] ?? []) as $sid) {
    $sid = trim((string)$sid);
    if ($sid === '') continue;
    $order[] = $sid;
    if (empty($_POST['section_enabled'][$sid])) $disabled[] = $sid;
}
if ($order) {
    $site['sections_order'] = $order;
    $site['sections_disabled'] = $disabled;
}

try { site_save($site); }
catch (Throwable $t) { flash('error', 'Could not save site.json: ' . $t->getMessage()); redirect(admin_url('pages')); }

log_activity($u ? (int)$u['id'] : null, 'pages_update', 'Site sections updated');
flash('success', 'Pages & sections saved.');
if (!build_supports_disabled() && $disabled) {
    flash('warn', 'Disabled sections are stored, but the current build.py renders every section in the order list — they will still appear on the site.');
}
[$code, $out] = rebuild_site();
if ($code !== 0) flash('error', 'Rebuild failed (exit ' . $code . '): ' . trunc($out, 500));
redirect(admin_url('pages'));
