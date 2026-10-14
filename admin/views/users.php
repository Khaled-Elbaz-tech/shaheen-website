<?php /** Users management (super_admin). Vars: $rows, $user */ ?>
<div class="card">
  <h2><?= isset($_GET['edit']) ? 'Edit user' : 'Add user' ?></h2>
  <?php
    $eu = null;
    if (isset($_GET['edit'])) {
      foreach ($rows as $r) { if ((int)$r['id'] === (int)$_GET['edit']) { $eu = $r; break; } }
    }
  ?>
  <form method="post" action="<?= admin_action('user_save') ?>">
    <?= csrf_field() ?>
    <?php if ($eu): ?><input type="hidden" name="id" value="<?= (int)$eu['id'] ?>"><?php endif; ?>
    <div class="row">
      <div class="field"><label for="u-name">Full name</label><input type="text" id="u-name" name="name" value="<?= e($eu['name'] ?? '') ?>" required maxlength="120"></div>
      <div class="field"><label for="u-email">Email</label><input type="email" id="u-email" name="email" value="<?= e($eu['email'] ?? '') ?>" required maxlength="180"></div>
    </div>
    <div class="row">
      <div class="field"><label for="u-role">Role</label>
        <select id="u-role" name="role">
          <?php foreach (['super_admin' => 'Super admin — everything', 'editor' => 'Editor — content, media, journal, inquiries', 'author' => 'Author — create/edit projects, media, journal', 'viewer' => 'Viewer — read only'] as $v => $l): ?>
            <option value="<?= $v ?>"<?= ($eu['role'] ?? 'editor') === $v ? ' selected' : '' ?>><?= $l ?></option>
          <?php endforeach; ?>
        </select></div>
      <div class="field"><label for="u-pw">Password<?= $eu ? ' <span class="hint">(leave empty to keep current)</span>' : '' ?></label><input type="password" id="u-pw" name="password"<?= $eu ? '' : ' required' ?> minlength="10" autocomplete="new-password"><span class="hint">Minimum 10 characters. Never shown again after saving.</span></div>
    </div>
    <div class="field"><label><input type="checkbox" name="active" value="1"<?= ($eu['active'] ?? 1) ? ' checked' : '' ?>> Active (can sign in)</label></div>
    <div class="actions">
      <button class="btn" type="submit"><?= $eu ? 'Save changes' : 'Create user' ?></button>
      <?php if ($eu): ?><a class="btn ghost" href="<?= admin_url('users') ?>">Cancel</a><?php endif; ?>
    </div>
  </form>
</div>

<div class="card" style="padding:0;overflow:hidden">
<table class="tbl">
  <thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Status</th><th>Created</th><th></th></tr></thead>
  <tbody>
  <?php foreach ($rows as $r): ?>
    <tr>
      <td><strong><?= e($r['name']) ?></strong></td>
      <td><?= e($r['email']) ?></td>
      <td><?= e(role_label($r['role'])) ?></td>
      <td><?= (int)$r['active'] ? '<span class="pill active">active</span>' : '<span class="pill inactive">inactive</span>' ?></td>
      <td><?= e(fmt_dt($r['created_at'])) ?></td>
      <td style="white-space:nowrap">
        <a class="btn small ghost" href="<?= admin_url('users', ['edit' => $r['id']]) ?>">Edit</a>
        <?php if ((int)$r['id'] !== (int)$user['id']): ?>
        <form method="post" action="<?= admin_action('user_delete') ?>" class="inline-form">
          <?= csrf_field() ?><input type="hidden" name="id" value="<?= (int)$r['id'] ?>">
          <button class="btn small danger" type="submit" data-confirm="Delete user <?= e($r['email']) ?>?">Delete</button>
        </form>
        <?php endif; ?>
      </td>
    </tr>
  <?php endforeach; ?>
  </tbody>
</table>
</div>
