<?php
/** POST do=project_duplicate — copy a project under a new slug (super_admin/editor only). */
declare(strict_types=1);

require_perm('projects_delete');

$u = current_user();
$id = (string)($_POST['id'] ?? '');
$c = content_load();
$group = group_by_id($c, $id);
if (!$group) { flash('error', 'Project not found.'); redirect(admin_url('projects')); }

$base = $id . '-copy';
$newId = $base; $n = 2;
while (group_by_id($c, $newId)) { $newId = $base . '-' . $n++; }

$copy = $group;
$copy['id'] = $newId;
$copy['title'] = ($group['title'] ?? 'Untitled') . ' (copy)';
$copy['number'] = next_project_number($c);
$copy['status'] = 'draft';
$c['groups'][] = $copy;
sync_register($c, $copy);

try {
    content_save($c);
} catch (Throwable $t) {
    flash('error', 'Could not save content.json: ' . $t->getMessage());
    redirect(admin_url('projects'));
}

log_activity($u ? (int)$u['id'] : null, 'project_duplicate', $id . ' → ' . $newId);
flash('success', 'Duplicated as draft: ' . $newId . '.');
redirect(admin_url('project_edit', ['id' => $newId]));
