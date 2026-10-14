<?php
/** Shared image picker modal. Requires $media (media_list()). */
?>
<div class="modal" id="pickerModal" role="dialog" aria-modal="true" aria-label="Choose an image">
  <div class="modal-box">
    <div class="modal-head">
      <h3 style="margin:0">Choose an image</h3>
      <div style="display:flex;gap:10px;align-items:center">
        <input type="search" data-picker-search placeholder="Search filename…" style="width:220px">
        <button type="button" class="btn ghost small" data-picker-confirm>Done</button>
        <button type="button" class="btn ghost small" onclick="closePicker()">Close</button>
      </div>
    </div>
    <div class="modal-body">
      <div class="picker-grid">
        <?php foreach ($media as $m): ?>
          <button type="button" class="picker-item" data-key="<?= e($m['key']) ?>">
            <img src="../dist/assets/<?= e($m['key']) ?>.webp" alt="" loading="lazy">
            <span class="pk"><?= e($m['key']) ?></span>
          </button>
        <?php endforeach; ?>
      </div>
    </div>
  </div>
</div>
