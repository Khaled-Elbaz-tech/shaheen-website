<?php
/** POST do=project_delete — remove a project (super_admin/editor only). */
declare(strict_types=1);

require_perm('projects_delete');

$u = current_user();
$id = (string)($_POST['id'] ?? '');
if ($id === '') { flash('error', 'Missing project id.'); redirect(admin_url('projects')); }

$c = content_load();
$group = group_by_id($c, $id);
if (!$group) { flash('error', 'Project not found.'); redirect(admin_url('projects')); }

revision_store('project', $id, $group, $u ? (int)$u['id'] : null);

$c['groups'] = array_values(array_filter($c['groups'], fn($g) => $g['id'] !== $id));
sync_register($c, null, $id);

try {
    content_save($c);
} catch (Throwable $t) {
    flash('error', 'Could not save content.json: ' . $t->getMessage());
    redirect(admin_url('projects'));
}

log_activity($u ? (int)$u['id'] : null, 'project_delete', $id . ' — ' . ($group['title'] ?? ''));
flash('success', 'Project deleted. A revision was kept so it can be restored.');
[$code, $out] = rebuild_site();
if ($code !== 0) {
    flash('error', 'Rebuild failed (exit ' . $code . '): ' . trunc($out, 500));
} else {
    flash('success', 'Site rebuilt.');
}
redirect(admin_url('projects'));
