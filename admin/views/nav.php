<?php /** Navigation editor. Vars: $site, $build_disabled */ ?>
<?php if (!$build_disabled): ?>
<div class="flash warn">Disabling nav items is not yet supported by <code>build.py</code> — it renders every item. Disabled items are stored and will take effect once the build honours them.</div>
<?php endif; ?>
<form method="post" action="<?= admin_action('nav_save') ?>">
<?= csrf_field() ?>
<div class="card">
  <h2>Navigation</h2>
  <p class="lede">Reorder with ↑ ↓. Links accept relative paths (<code>#work</code>, <code>project-index/</code>) or full <code>https://</code> URLs — <code>javascript:</code> and <code>data:</code> are blocked.</p>
  <table class="tbl"><thead><tr><th>Label</th><th>Link</th><th>Enabled</th><th>Order</th><th></th></tr></thead><tbody id="navRows">
    <?php foreach (($site['nav'] ?? []) as $i => $n): ?>
    <tr>
      <td><input type="text" name="nav_label[<?= $i ?>]" value="<?= e($n['label'] ?? '') ?>" maxlength="60" required></td>
      <td><input type="text" name="nav_href[<?= $i ?>]" value="<?= e($n['href'] ?? '') ?>" maxlength="300" required></td>
      <td><label><input type="checkbox" name="nav_enabled[<?= $i ?>]" value="1"<?= !isset($n['enabled']) || !empty($n['enabled']) ? ' checked' : '' ?>> show</label></td>
      <td style="white-space:nowrap"><button type="button" class="btn small ghost" onclick="mv(this,-1)" aria-label="Move up">↑</button> <button type="button" class="btn small ghost" onclick="mv(this,1)" aria-label="Move down">↓</button></td>
      <td><button type="button" class="btn small danger" onclick="this.closest('tr').remove()">Remove</button></td>
    </tr>
    <?php endforeach; ?>
  </tbody></table>
  <div class="actions">
    <button type="button" class="btn ghost small" onclick="addNav()">+ Add item</button>
  </div>
</div>
<div class="actions">
  <button class="btn" type="submit">Save & rebuild site</button>
  <a class="btn ghost" href="<?= admin_url('dashboard') ?>">Cancel</a>
</div>
</form>
<script>
var navIdx = <?= count($site['nav'] ?? []) ?>;
function mv(btn, dir) {
  var tr = btn.closest('tr'), sib = dir < 0 ? tr.previousElementSibling : tr.nextElementSibling;
  if (sib) { dir < 0 ? tr.parentNode.insertBefore(tr, sib) : tr.parentNode.insertBefore(sib, tr); }
}
function addNav() {
  var tr = document.createElement('tr');
  tr.innerHTML = '<td><input type="text" name="nav_label[' + navIdx + ']" maxlength="60" required></td>' +
    '<td><input type="text" name="nav_href[' + navIdx + ']" maxlength="300" required placeholder="#work or https://…"></td>' +
    '<td><label><input type="checkbox" name="nav_enabled[' + navIdx + ']" value="1" checked> show</label></td>' +
    '<td style="white-space:nowrap"><button type="button" class="btn small ghost" onclick="mv(this,-1)">↑</button> <button type="button" class="btn small ghost" onclick="mv(this,1)">↓</button></td>' +
    '<td><button type="button" class="btn small danger" onclick="this.closest(\'tr\').remove()">Remove</button></td>';
  navIdx++; document.getElementById('navRows').appendChild(tr);
}
</script>
