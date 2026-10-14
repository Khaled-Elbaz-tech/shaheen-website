<?php
/** POST do=inquiry — sub=read toggles read/unread, sub=delete removes. */
declare(strict_types=1);

require_perm('inquiries');
$u = current_user();

$sub = (string)($_POST['sub'] ?? '');
$id = (int)($_POST['id'] ?? 0);
if ($id <= 0) { flash('error', 'Missing inquiry.'); redirect(admin_url('inquiries')); }

if ($sub === 'read') {
    $st = cms_pdo()->prepare("UPDATE inquiries SET read = 1 - read WHERE id=?");
    $st->execute([$id]);
    log_activity($u ? (int)$u['id'] : null, 'inquiry_toggle', '#' . $id);
    flash('success', 'Inquiry updated.');
} elseif ($sub === 'delete') {
    $st = cms_pdo()->prepare("DELETE FROM inquiries WHERE id=?");
    $st->execute([$id]);
    log_activity($u ? (int)$u['id'] : null, 'inquiry_delete', '#' . $id);
    flash('success', 'Inquiry deleted.');
} else {
    flash('error', 'Unknown inquiry action.');
}
redirect(admin_url('inquiries'));
