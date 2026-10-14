<?php /** Dashboard. Vars: $counts, $journal_count, $unread, $recent, $media, $build_status */ ?>
<?php if (!$build_status): ?>
<div class="flash warn">Draft support: the current <code>build.py</code> does not filter <code>status: draft</code> — drafts/archived projects may still appear on the public site until the build is updated.</div>
<?php endif; ?>

<div class="grid g4" style="margin-bottom:20px">
  <div class="stat"><div class="num"><?= (int)$counts['total'] ?></div><div class="lbl">Projects</div><div class="sub"><?= (int)$counts['published'] ?> published · <?= (int)$counts['draft'] ?> draft · <?= (int)$counts['archived'] ?> archived</div></div>
  <div class="stat"><div class="num"><?= (int)$journal_count ?></div><div class="lbl">Journal entries</div><div class="sub"><a href="<?= admin_url('journal') ?>">Manage journal →</a></div></div>
  <div class="stat"><div class="num"><?= (int)$unread ?></div><div class="lbl">Unread inquiries</div><div class="sub"><a href="<?= admin_url('inquiries') ?>">Open inbox →</a></div></div>
  <div class="stat"><div class="num"><?= count($media) ?></div><div class="lbl">Media assets</div><div class="sub">newest shown below</div></div>
</div>

<div class="grid g2">
  <div class="card">
    <h2>Quick actions</h2>
    <div class="actions">
      <?php if (can('projects')): ?><a class="btn" href="<?= admin_url('project_edit') ?>">+ New project</a><?php endif; ?>
      <?php if (can('media')): ?><a class="btn ghost" href="<?= admin_url('media') ?>">Upload media</a><?php endif; ?>
      <?php if (can('journal')): ?><a class="btn ghost" href="<?= admin_url('journal') ?>">New journal entry</a><?php endif; ?>
      <a class="btn ghost" href="../dist/index.html" target="_blank" rel="noopener">View website ↗</a>
      <?php if (can('rebuild')): ?>
        <form method="post" action="<?= admin_action('rebuild') ?>" class="inline-form">
          <?= csrf_field() ?>
          <button class="btn ghost" type="submit">Rebuild site</button>
        </form>
      <?php endif; ?>
    </div>
  </div>
  <div class="card">
    <h2>Recent activity</h2>
    <?php if (!$recent): ?><p class="lede">Nothing logged yet.</p>
    <?php else: ?>
    <table class="tbl"><tbody>
      <?php foreach ($recent as $r): ?>
        <tr><td style="white-space:nowrap"><?= e(fmt_dt($r['created_at'])) ?></td>
            <td><strong><?= e($r['user_name'] ?? '—') ?></strong> · <?= e($r['action']) ?><br><span style="color:#6B6E68"><?= e(trunc($r['detail'] ?? '', 80)) ?></span></td></tr>
      <?php endforeach; ?>
    </tbody></table>
    <?php endif; ?>
    <p><a href="<?= admin_url('activity') ?>">Full activity log →</a></p>
  </div>
</div>

<div class="card">
  <h2>Recent media</h2>
  <?php if (!$media): ?><p class="lede">No images yet.</p>
  <?php else: ?>
  <div class="media-grid">
    <?php foreach ($media as $m): ?>
      <div class="media-card">
        <img src="../dist/assets/<?= e($m['key']) ?>.webp" alt="" loading="lazy">
        <div class="media-meta"><div class="key"><?= e($m['key']) ?></div><div class="dim"><?= $m['width'] ? e((string)$m['width']) . '×' . e((string)$m['height']) . ' · ' : '' ?><?= e(human_filesize((int)$m['bytes'])) ?></div></div>
      </div>
    <?php endforeach; ?>
  </div>
  <?php endif; ?>
  <p><a href="<?= admin_url('media') ?>">Open media library →</a></p>
</div>
