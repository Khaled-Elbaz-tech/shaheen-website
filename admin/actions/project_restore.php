<?php
/** POST do=project_restore — restore a project from a stored revision. */
declare(strict_types=1);

require_perm('projects');

$u = current_user();
$revId = (int)($_POST['revision_id'] ?? 0);
$st = cms_pdo()->prepare("SELECT * FROM revisions WHERE id=? AND entity='project' LIMIT 1");
$st->execute([$revId]);
$rev = $st->fetch();
if (!$rev) { flash('error', 'Revision not found.'); redirect(admin_url('projects')); }

$data = json_decode($rev['data'], true);
if (!is_array($data) || empty($data['id'])) {
    flash('error', 'Revision data is corrupt.');
    redirect(admin_url('projects'));
}
$id = $data['id'];

$c = content_load();
$current = group_by_id($c, $id);
if ($current) {
    revision_store('project', $id, $current, $u ? (int)$u['id'] : null); // keep current before overwriting
    foreach ($c['groups'] as $i => $g) {
        if ($g['id'] === $id) { $c['groups'][$i] = $data; break; }
    }
} else {
    $c['groups'][] = $data;
}
sync_register($c, $data);

try {
    content_save($c);
} catch (Throwable $t) {
    flash('error', 'Could not save content.json: ' . $t->getMessage());
    redirect(admin_url('projects'));
}

log_activity($u ? (int)$u['id'] : null, 'project_restore', $id . ' restored to revision #' . $revId);
flash('success', 'Project restored from revision of ' . fmt_dt($rev['created_at']) . '. Site rebuilt below.');
[$code, $out] = rebuild_site();
if ($code !== 0) flash('error', 'Rebuild failed (exit ' . $code . '): ' . trunc($out, 500));
redirect(admin_url('project_edit', ['id' => $id]));
