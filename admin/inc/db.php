<?php
/**
 * SQLite database layer (PDO). Creates admin/db/cms.sqlite on first run
 * with the schema required by the CMS and applies light migrations.
 */
declare(strict_types=1);

const CMS_DB_PATH = __DIR__ . '/../db/cms.sqlite';

function cms_pdo(): PDO {
    static $pdo = null;
    if ($pdo instanceof PDO) return $pdo;

    $dir = dirname(CMS_DB_PATH);
    if (!is_dir($dir)) {
        if (!mkdir($dir, 0755, true) && !is_dir($dir)) {
            throw new RuntimeException('Could not create database directory.');
        }
    }
    $isNew = !file_exists(CMS_DB_PATH);
    $pdo = new PDO('sqlite:' . CMS_DB_PATH);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
    $pdo->exec('PRAGMA journal_mode = WAL;');
    $pdo->exec('PRAGMA busy_timeout = 5000;');
    if ($isNew || !table_exists($pdo, 'users')) {
        cms_migrate($pdo);
    } else {
        cms_migrate($pdo); // idempotent — safe to run every boot
    }
    return $pdo;
}

function table_exists(PDO $pdo, string $table): bool {
    $st = $pdo->prepare("SELECT name FROM sqlite_master WHERE type='table' AND name=?");
    $st->execute([$table]);
    return (bool)$st->fetchColumn();
}

function column_exists(PDO $pdo, string $table, string $col): bool {
    foreach ($pdo->query("PRAGMA table_info(" . $table . ")") as $row) {
        if ($row['name'] === $col) return true;
    }
    return false;
}

/** Create tables if missing and add any columns added in later versions. */
function cms_migrate(PDO $pdo): void {
    $pdo->exec("CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'viewer',
        active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )");
    $pdo->exec("CREATE TABLE IF NOT EXISTS activity_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT NOT NULL,
        detail TEXT,
        ip TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )");
    $pdo->exec("CREATE TABLE IF NOT EXISTS inquiries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        type TEXT DEFAULT '',
        message TEXT NOT NULL,
        read INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )");
    $pdo->exec("CREATE TABLE IF NOT EXISTS revisions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        data TEXT NOT NULL,
        user_id INTEGER,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )");
    $pdo->exec("CREATE TABLE IF NOT EXISTS login_attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ip TEXT NOT NULL,
        attempted_at TEXT NOT NULL DEFAULT (datetime('now'))
    )");
    $pdo->exec("CREATE INDEX IF NOT EXISTS idx_login_attempts_ip ON login_attempts(ip, attempted_at)");
    $pdo->exec("CREATE INDEX IF NOT EXISTS idx_activity_created ON activity_log(created_at DESC)");
    $pdo->exec("CREATE INDEX IF NOT EXISTS idx_revisions_entity ON revisions(entity, entity_id, id DESC)");
}

/** Record a login attempt; returns number of attempts from this IP in last 10 min. */
function login_attempts_recent(string $ip): int {
    $pdo = cms_pdo();
    $st = $pdo->prepare("SELECT COUNT(*) FROM login_attempts WHERE ip=? AND attempted_at > datetime('now','-10 minutes')");
    $st->execute([$ip]);
    return (int)$st->fetchColumn();
}

function login_attempt_record(string $ip): void {
    $pdo = cms_pdo();
    $st = $pdo->prepare("INSERT INTO login_attempts (ip) VALUES (?)");
    $st->execute([$ip]);
    // Prune old attempts so the table stays small.
    $pdo->exec("DELETE FROM login_attempts WHERE attempted_at < datetime('now','-1 day')");
}

function user_count(): int {
    $st = cms_pdo()->query("SELECT COUNT(*) FROM users");
    return (int)$st->fetchColumn();
}

function get_user_by_email(string $email): ?array {
    $st = cms_pdo()->prepare("SELECT * FROM users WHERE email=? LIMIT 1");
    $st->execute([strtolower(trim($email))]);
    $row = $st->fetch();
    return $row ?: null;
}

function get_user_by_id(int $id): ?array {
    $st = cms_pdo()->prepare("SELECT * FROM users WHERE id=? LIMIT 1");
    $st->execute([$id]);
    $row = $st->fetch();
    return $row ?: null;
}
