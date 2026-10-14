<?php /** Inquiries inbox. Vars: $rows */ ?>
<?php if (!$rows): ?>
<div class="list-empty">
  <h2 style="margin-top:0">Inbox is empty</h2>
  <p>The public site currently uses a mailto link for contact, so there is no form feeding this inbox yet.<br>
  If a contact form is added later, its submissions will appear here.</p>
</div>
<?php else: ?>
<div class="toolbar">
  <div class="searchbar" style="margin:0"><input type="search" placeholder="Search name, email, message…" data-table-filter="inqTbl" aria-label="Search inquiries"></div>
  <span style="color:#6B6E68;font-size:.88rem"><?= count($rows) ?> messages</span>
</div>
<div class="card" style="padding:0;overflow:hidden">
<table class="tbl" id="inqTbl">
  <thead><tr><th>Received</th><th>From</th><th>Type</th><th>Message</th><th>Status</th><th></th></tr></thead>
  <tbody>
  <?php foreach ($rows as $r): ?>
    <tr style="<?= $r['read'] ? '' : 'font-weight:600' ?>">
      <td style="white-space:nowrap"><?= e(fmt_dt($r['created_at'])) ?></td>
      <td><?= e($r['name']) ?><br><a href="mailto:<?= e($r['email']) ?>" style="font-weight:400;font-size:.85rem"><?= e($r['email']) ?></a></td>
      <td><?= e($r['type'] ?: '—') ?></td>
      <td style="max-width:320px"><?= e(trunc($r['message'], 140)) ?></td>
      <td><?= $r['read'] ? '<span class="pill archived">read</span>' : '<span class="pill draft">unread</span>' ?></td>
      <td style="white-space:nowrap">
        <form method="post" action="<?= admin_action('inquiry') ?>" class="inline-form">
          <?= csrf_field() ?><input type="hidden" name="sub" value="read"><input type="hidden" name="id" value="<?= (int)$r['id'] ?>">
          <button class="btn small ghost" type="submit"><?= $r['read'] ? 'Mark unread' : 'Mark read' ?></button>
        </form>
        <form method="post" action="<?= admin_action('inquiry') ?>" class="inline-form">
          <?= csrf_field() ?><input type="hidden" name="sub" value="delete"><input type="hidden" name="id" value="<?= (int)$r['id'] ?>">
          <button class="btn small danger" type="submit" data-confirm="Delete this inquiry?">Delete</button>
        </form>
      </td>
    </tr>
  <?php endforeach; ?>
  </tbody>
</table>
</div>
<?php endif; ?>
